const { createRng } = require('../core/rng');
const { createBattleState, getActive } = require('./battle-state');
const { resolveTurn } = require('./turn-engine');
const { chooseMove } = require('../policy/move-policy');

function livingCount(side) {
  return side.team.reduce((n, mon) => n + (mon.fainted ? 0 : 1), 0);
}

function pickWinner(state) {
  const aAlive = livingCount(state.sideA);
  const bAlive = livingCount(state.sideB);
  if (aAlive > bAlive) return 'A';
  if (bAlive > aAlive) return 'B';
  const aHp = state.sideA.team.reduce((s, mon) => s + mon.hp, 0);
  const bHp = state.sideB.team.reduce((s, mon) => s + mon.hp, 0);
  if (aHp > bHp) return 'A';
  if (bHp > aHp) return 'B';
  return 'Tie';
}

function simulateBattle(teamA, teamB, options = {}) {
  const rand = options.rand || createRng(options.seed);
  const maxTurns = options.maxTurns || 200;
  const defaultPolicy = (state, actor, target) => chooseMove(state, actor, target);
  const policyA = options.policyA || defaultPolicy;
  const policyB = options.policyB || defaultPolicy;
  const state = createBattleState(teamA, teamB);

  while (state.turn < maxTurns) {
    const a = getActive(state.sideA);
    const b = getActive(state.sideB);
    if (a.fainted || b.fainted) break;
    const moveA = policyA(state, a, b);
    const moveB = policyB(state, b, a);
    resolveTurn(state, moveA, moveB, rand);
    const aAlive = livingCount(state.sideA);
    const bAlive = livingCount(state.sideB);
    if (!aAlive || !bAlive) break;
  }

  const winner = pickWinner(state);
  return {
    winner,
    turns: state.turn,
    state,
    score: {
      sideAAlive: livingCount(state.sideA),
      sideBAlive: livingCount(state.sideB),
    },
  };
}

module.exports = { simulateBattle };
