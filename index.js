const datasets = require('./src/data/datasets');
const { createRng } = require('./src/core/rng');
const { generateTeam } = require('./src/sim/team-generator');
const { simulateBattle } = require('./src/sim/battle-engine');

function evaluateFitness(candidateTeam, options = {}) {
  const opponents = options.opponents || Array.from(
    { length: options.numOpponents || 20 },
    (_, i) => generateTeam({ seed: (options.seed || 1) + i + 1000 })
  );
  let wins = 0;
  let turns = 0;
  for (const opponent of opponents) {
    const result = simulateBattle(candidateTeam, opponent, options);
    if (result.winner === 'A') wins++;
    turns += result.turns;
  }
  return {
    wins,
    total: opponents.length,
    winRate: opponents.length ? wins / opponents.length : 0,
    avgTurns: opponents.length ? turns / opponents.length : 0,
  };
}

module.exports = {
  datasets,
  generateTeam,
  simulateBattle,
  evaluateFitness,
  createRng,
};
