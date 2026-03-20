const { typeEffectiveness } = require('../data/datasets');

function getTypeMultiplier(attackType, defenderTypes) {
  const chart = typeEffectiveness.effectiveness[attackType] || {};
  let mult = 1;
  for (const dType of defenderTypes) {
    mult *= chart[dType] ?? 1;
  }
  return mult;
}

module.exports = { getTypeMultiplier };
