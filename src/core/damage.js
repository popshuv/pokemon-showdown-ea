const { getTypeMultiplier } = require('./types');

function expectedDamage(attacker, defender, move) {
  const power = move.basePower || 0;
  if (power <= 0) return 0;
  const hitChance = move.accuracy == null ? 1 : Math.max(0, Math.min(1, move.accuracy / 100));
  const stab = attacker.types.includes(move.type) ? 1.5 : 1;
  const typeMult = getTypeMultiplier(move.type, defender.types);
  const attackStat = move.gen1AttackClass === 'physical' ? attacker.baseStats.atk : attacker.baseStats.spa;
  const defenseStat = move.gen1AttackClass === 'physical' ? defender.baseStats.def : defender.baseStats.spd;
  const statRatio = Math.max(0.4, attackStat / Math.max(1, defenseStat));
  const raw = power * statRatio * stab * typeMult;
  return raw * hitChance;
}

function sampleHit(move, rand) {
  if (move.accuracy == null) return true;
  return rand() <= move.accuracy / 100;
}

module.exports = { expectedDamage, sampleHit };
