const { statuses } = require('../data/datasets');

function maybeApplyStatus(target, move, rand) {
  if (!move?.effects?.majorStatus || target.status) return;
  const chance = move.effects.secondaryChance == null ? 1 : move.effects.secondaryChance / 100;
  if (rand() <= chance) {
    target.status = move.effects.majorStatus;
    if (target.status === 'slp') {
      const slp = statuses.slp?.declarative || { sleepTurnsMin: 1, sleepTurnsMax: 3 };
      const span = slp.sleepTurnsMax - slp.sleepTurnsMin + 1;
      target.statusCounter = slp.sleepTurnsMin + Math.floor(rand() * span);
    }
  }
}

function onBeforeAction(mon, rand) {
  if (!mon.status) return true;
  if (mon.status === 'par') {
    const c = statuses.par?.declarative?.fullParalysisChance ?? 0.25;
    if (rand() <= c) return false;
    return true;
  }
  if (mon.status === 'slp') {
    mon.statusCounter = Math.max(0, (mon.statusCounter || 0) - 1);
    if (mon.statusCounter <= 0) {
      mon.status = null;
      return true;
    }
    return false;
  }
  if (mon.status === 'frz') return false;
  return true;
}

function endTurn(mon) {
  if (mon.fainted || !mon.status) return 0;
  const maxHp = mon.baseStats.hp;
  if (mon.status === 'brn' || mon.status === 'psn') return Math.max(1, Math.floor(maxHp / 16));
  if (mon.status === 'tox') {
    mon.toxicCounter = (mon.toxicCounter || 0) + 1;
    return Math.max(1, Math.floor(maxHp / 16) * mon.toxicCounter);
  }
  return 0;
}

module.exports = { maybeApplyStatus, onBeforeAction, endTurn };
