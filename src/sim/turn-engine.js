const { moves } = require('../data/datasets');
const { expectedDamage, sampleHit } = require('../core/damage');
const { maybeApplyStatus, onBeforeAction, endTurn } = require('../core/status-engine');
const { getActive, markFainted, autoPromote } = require('./battle-state');

function speedWithStatus(mon) {
  const slow = mon.status === 'par' ? 0.25 : 1;
  return mon.baseStats.spe * slow;
}

function resolveAttack(attacker, defender, moveId, rand) {
  const move = moves[moveId];
  if (!move || attacker.fainted) return { acted: false, moveId, damage: 0, hit: false };
  if (!onBeforeAction(attacker, rand)) return { acted: false, moveId, damage: 0, hit: false };
  if (!sampleHit(move, rand)) return { acted: true, moveId, damage: 0, hit: false };

  const damage = Math.max(1, Math.floor(expectedDamage(attacker, defender, move)));
  defender.hp -= damage;
  markFainted(defender);
  maybeApplyStatus(defender, move, rand);
  return { acted: true, moveId, damage, hit: true };
}

function applyEndTurn(sideA, sideB) {
  const a = getActive(sideA);
  const b = getActive(sideB);
  if (!a.fainted) {
    a.hp -= endTurn(a);
    markFainted(a);
  }
  if (!b.fainted) {
    b.hp -= endTurn(b);
    markFainted(b);
  }
  autoPromote(sideA);
  autoPromote(sideB);
}

function resolveTurn(state, moveA, moveB, rand) {
  const a = getActive(state.sideA);
  const b = getActive(state.sideB);
  const aFirst = speedWithStatus(a) >= speedWithStatus(b);
  const first = aFirst ? ['A', a, b, moveA] : ['B', b, a, moveB];
  const second = aFirst ? ['B', b, a, moveB] : ['A', a, b, moveA];

  const log = { turn: state.turn + 1, actions: [] };
  const r1 = resolveAttack(first[1], first[2], first[3], rand);
  log.actions.push({ side: first[0], ...r1 });
  if (!first[2].fainted) {
    const r2 = resolveAttack(second[1], second[2], second[3], rand);
    log.actions.push({ side: second[0], ...r2 });
  }

  applyEndTurn(state.sideA, state.sideB);
  state.turn += 1;
  state.history.push(log);
}

module.exports = { resolveTurn };
