const { pokemon } = require('../data/datasets');
const { createRng } = require('../core/rng');

function sampleNoReplace(items, count, rand) {
  const pool = items.slice();
  const out = [];
  while (pool.length && out.length < count) {
    const idx = Math.floor(rand() * pool.length);
    out.push(pool.splice(idx, 1)[0]);
  }
  return out;
}

function generateTeam(options = {}) {
  const rand = options.rand || createRng(options.seed);
  const teamSize = options.teamSize || 6;
  return sampleNoReplace(pokemon, teamSize, rand);
}

module.exports = { generateTeam };
