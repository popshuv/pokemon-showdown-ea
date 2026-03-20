const pokemon = require('../../datasets/gen1-pokemon-dataset.json');
const moves = require('../../datasets/gen1-moves-dataset.json');
const typeEffectiveness = require('../../datasets/gen1-type-effectiveness.json');
const statuses = require('../../datasets/gen1-status-dataset.json');

const pokemonById = Object.fromEntries(pokemon.map(p => [p.id, p]));

module.exports = {
  pokemon,
  moves,
  typeEffectiveness,
  statuses,
  pokemonById,
};
