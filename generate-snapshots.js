const fs = require('fs');
const path = require('path');

const root = 'C:/Users/Ethan/Projects/pokemom-showdown-workspace';
const eaRoot = path.join(root, 'pokemon-showdown-ea');
const eaDataRoot = path.join(eaRoot, 'datasets');
const psRoot = path.join(root, 'pokemon-showdown');

const pokemonDatasetPath = path.join(eaDataRoot, 'gen1-pokemon-dataset.json');
const baseMovesPath = path.join(psRoot, 'data/moves.ts');
const gen1MovesPath = path.join(psRoot, 'data/mods/gen1/moves.ts');
const baseTypechartPath = path.join(psRoot, 'data/typechart.ts');
const gen1TypechartPath = path.join(psRoot, 'data/mods/gen1/typechart.ts');

function readText(filePath) {
  return fs.readFileSync(filePath, 'utf8');
}

function extractObjectBlock(text, key) {
  const re = new RegExp(`\\n\\t${key}:\\s*\\{`);
  const match = text.match(re);
  if (!match) return null;
  let i = match.index + match[0].length - 1;
  let depth = 1;
  let j = i + 1;
  while (j < text.length && depth > 0) {
    const ch = text[j];
    if (ch === '{') depth++;
    if (ch === '}') depth--;
    j++;
  }
  return text.slice(match.index, j);
}

function parseScalar(block, key) {
  const str = (block.match(new RegExp(`${key}:\\s*"([^"]+)"`)) || [])[1];
  if (str) return str;
  const num = (block.match(new RegExp(`${key}:\\s*([0-9]+)`)) || [])[1];
  if (num) return Number(num);
  const boolTrue = new RegExp(`${key}:\\s*true`).test(block);
  if (boolTrue) return true;
  const boolFalse = new RegExp(`${key}:\\s*false`).test(block);
  if (boolFalse) return false;
  return undefined;
}

function parseMoveData(baseBlock, overrideBlock) {
  const merged = {
    type: parseScalar(overrideBlock || '', 'type') || parseScalar(baseBlock || '', 'type') || 'Normal',
    category: parseScalar(overrideBlock || '', 'category') || parseScalar(baseBlock || '', 'category') || 'Status',
    basePower: parseScalar(overrideBlock || '', 'basePower'),
    accuracy: parseScalar(overrideBlock || '', 'accuracy'),
    target: parseScalar(overrideBlock || '', 'target') || parseScalar(baseBlock || '', 'target') || 'normal',
  };
  if (merged.basePower === undefined) merged.basePower = parseScalar(baseBlock || '', 'basePower') ?? 0;
  if (merged.accuracy === undefined) merged.accuracy = parseScalar(baseBlock || '', 'accuracy') ?? true;

  const block = `${baseBlock || ''}\n${overrideBlock || ''}`;
  const secondaryChance = parseScalar(block, 'chance');
  const causesStatus = (block.match(/status:\s*'([a-z]+)'/) || [])[1] || null;
  const volatileStatus = (block.match(/volatileStatus:\s*'([a-z]+)'/) || [])[1] || null;
  const drain = /\bdrain:\s*\[/.test(block);
  const heal = /\bheal:\s*\[/.test(block);
  const recoil = /\brecoil:\s*\[/.test(block) || /\bselfdestruct:\s*(true|'always'|'ifHit')/.test(block);
  const hasDamage = merged.category !== 'Status' || merged.basePower > 0 || /\bdamage:\s*/.test(block);

  const gen1PhysicalTypes = new Set(['normal', 'fighting', 'flying', 'ground', 'rock', 'bug', 'ghost', 'poison']);
  const moveTypeId = String(merged.type).toLowerCase();
  const gen1AttackClass = merged.category === 'Status'
    ? 'status'
    : (gen1PhysicalTypes.has(moveTypeId) ? 'physical' : 'special');

  const tags = [];
  if (hasDamage) tags.push('damage');
  if (merged.category === 'Status') tags.push('status');
  if (heal) tags.push('healing');
  if (drain) tags.push('drain');
  if (recoil) tags.push('recoil');
  if (causesStatus || volatileStatus) tags.push('ailment');
  if (/\bboosts:\s*\{/.test(block)) tags.push('statchange');

  return {
    type: moveTypeId,
    category: String(merged.category).toLowerCase(),
    gen1AttackClass,
    basePower: Number(merged.basePower) || 0,
    accuracy: merged.accuracy === true ? null : Number(merged.accuracy),
    target: merged.target,
    effects: {
      majorStatus: causesStatus,
      volatileStatus,
      secondaryChance: typeof secondaryChance === 'number' ? secondaryChance : null,
      drain,
      heal,
      recoil,
    },
    tags,
  };
}

function generateMovesSnapshot() {
  const baseMovesText = readText(baseMovesPath);
  const gen1MovesText = readText(gen1MovesPath);
  const pokemonData = JSON.parse(readText(pokemonDatasetPath));
  const moveIds = new Set();
  for (const p of pokemonData) {
    for (const m of p.moves) moveIds.add(String(m).toLowerCase());
  }

  const moves = {};
  for (const moveId of [...moveIds].sort()) {
    const baseBlock = extractObjectBlock(baseMovesText, moveId);
    const gen1Block = extractObjectBlock(gen1MovesText, moveId);
    if (!baseBlock && !gen1Block) continue;
    moves[moveId] = parseMoveData(baseBlock, gen1Block);
  }
  return moves;
}

function generateTypeEffectivenessSnapshot() {
  const baseChartText = readText(baseTypechartPath);
  const gen1ChartText = readText(gen1TypechartPath);

  const parseDefenderMap = (chartText) => {
    const map = {};
    const typeIds = [...chartText.matchAll(/\n\t([a-z]+):\s*\{/g)].map(m => m[1]);
    for (const defenderType of typeIds) {
      const block = extractObjectBlock(chartText, defenderType);
      if (!block || !/damageTaken:\s*\{/.test(block)) continue;
      const takenBlock = (block.match(/damageTaken:\s*\{([\s\S]*?)\n\t\t\}/) || [])[1];
      if (!takenBlock) continue;
      const damageTaken = {};
      for (const m of takenBlock.matchAll(/\n\s*([A-Za-z]+):\s*([0-9]),?/g)) {
        damageTaken[m[1].toLowerCase()] = Number(m[2]);
      }
      if (!Object.keys(damageTaken).length) continue;
      map[defenderType] = damageTaken;
    }
    return map;
  };

  const defenderMap = parseDefenderMap(baseChartText);
  const gen1Overrides = parseDefenderMap(gen1ChartText);
  for (const [defType, overrideMap] of Object.entries(gen1Overrides)) {
    defenderMap[defType] = { ...(defenderMap[defType] || {}), ...overrideMap };
  }

  const attackers = Object.keys(defenderMap)
    .filter(t => !['dark', 'steel', 'fairy', 'stellar'].includes(t))
    .sort();
  const effectiveness = {};
  for (const atk of attackers) {
    effectiveness[atk] = {};
    for (const def of attackers) {
      const code = defenderMap[def][atk];
      let mult = 1;
      if (code === 1) mult = 2;
      if (code === 2) mult = 0.5;
      if (code === 3) mult = 0;
      effectiveness[atk][def] = mult;
    }
  }

  return {
    notes: 'Derived from Pokemon Showdown gen1 typechart damageTaken values.',
    encoding: { 0: 'neutral', 1: 'super-effective', 2: 'resisted', 3: 'immune' },
    effectiveness,
  };
}

function generateStatusSnapshot() {
  return {
    brn: {
      kind: 'major',
      declarative: { residualDamageFraction: 1 / 16 },
      logicNotes: ['Deals residual damage each turn.', 'In Gen1, interacts with Toxic counter carryover edge cases.'],
    },
    par: {
      kind: 'major',
      declarative: { fullParalysisChance: 63 / 256, speedMultiplierApprox: 0.25 },
      logicNotes: ['Can prevent acting each turn.', 'Gen1 speed behavior differs from modern gens.'],
    },
    slp: {
      kind: 'major',
      declarative: { sleepTurnsMin: 1, sleepTurnsMax: 7 },
      logicNotes: ['Target cannot act while asleep.', 'Gen1 sleep turn accounting differs from later gens.'],
    },
    frz: {
      kind: 'major',
      declarative: { thawByFireMove: true },
      logicNotes: ['Frozen target generally cannot move.', 'In Gen1, thawing is far more restricted than later gens.'],
    },
    psn: {
      kind: 'major',
      declarative: { residualDamageFraction: 1 / 16 },
      logicNotes: ['Deals residual damage each turn.', 'Gen1 can share Toxic counter behavior in some interactions.'],
    },
    tox: {
      kind: 'major',
      declarative: { escalatingResidual: true },
      logicNotes: ['Damage increases over turns.', 'Gen1 has Toxic counter carryover quirks.'],
    },
    confusion: {
      kind: 'volatile',
      declarative: { selfHitChanceApprox: 128 / 256, turnsMin: 2, turnsMax: 5 },
      logicNotes: ['May cause self-hit instead of acting.', 'Implemented as volatile status in Showdown.'],
    },
    flinch: {
      kind: 'volatile',
      declarative: { durationTurns: 1 },
      logicNotes: ['Prevents move on that turn when applied before action.'],
    },
  };
}

function writeJSON(name, data) {
  if (!fs.existsSync(eaDataRoot)) fs.mkdirSync(eaDataRoot, { recursive: true });
  const outputPath = path.join(eaDataRoot, name);
  fs.writeFileSync(outputPath, `${JSON.stringify(data, null, 2)}\n`);
  return outputPath;
}

const moves = generateMovesSnapshot();
const types = generateTypeEffectivenessSnapshot();
const statuses = generateStatusSnapshot();

console.log(`Wrote ${Object.keys(moves).length} moves -> ${writeJSON('gen1-moves-dataset.json', moves)}`);
console.log(`Wrote type matrix -> ${writeJSON('gen1-type-effectiveness.json', types)}`);
console.log(`Wrote statuses -> ${writeJSON('gen1-status-dataset.json', statuses)}`);
