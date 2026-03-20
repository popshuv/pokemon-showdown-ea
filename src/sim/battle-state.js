function cloneCombatant(mon) {
  return {
    ...mon,
    maxHp: mon.baseStats.hp,
    hp: mon.baseStats.hp,
    status: null,
    statusCounter: 0,
    toxicCounter: 0,
    fainted: false,
  };
}

function createBattleState(teamA, teamB) {
  return {
    turn: 0,
    sideA: { team: teamA.map(cloneCombatant), activeIndex: 0 },
    sideB: { team: teamB.map(cloneCombatant), activeIndex: 0 },
    ended: false,
    winner: null,
    history: [],
  };
}

function getActive(side) {
  return side.team[side.activeIndex];
}

function autoPromote(side) {
  if (!getActive(side).fainted) return;
  const next = side.team.findIndex(mon => !mon.fainted);
  if (next >= 0) side.activeIndex = next;
}

function markFainted(mon) {
  if (mon.hp <= 0) {
    mon.hp = 0;
    mon.fainted = true;
  }
}

module.exports = { createBattleState, getActive, autoPromote, markFainted };
