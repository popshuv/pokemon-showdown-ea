const { moves } = require('../data/datasets');
const { expectedDamage } = require('../core/damage');

function scoreMove(actor, target, move) {
  const damageScore = expectedDamage(actor, target, move);
  const statusBonus = move.effects?.majorStatus && !target.status ? 18 : 0;
  const healBonus = move.tags?.includes('healing') ? 12 : 0;
  return damageScore + statusBonus + healBonus;
}

function chooseMove(state, actor, target) {
  let bestMoveId = actor.moves[0];
  let bestScore = -Infinity;
  for (const moveId of actor.moves) {
    const move = moves[moveId];
    if (!move) continue;
    const s = scoreMove(actor, target, move);
    if (s > bestScore) {
      bestScore = s;
      bestMoveId = moveId;
    }
  }
  return bestMoveId;
}

module.exports = { chooseMove };
