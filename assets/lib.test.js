const test = require('node:test');
const assert = require('node:assert');
const { searchCovers, sortCovers } = require('./lib.js');

const COVERS = [
  { id: '1', song: 'Two of Us', artist: 'The Beatles', date: '2023-05-01', views: 100 },
  { id: '2', song: 'The Swimming Song', artist: 'Loudon Wainwright III', date: '2024-08-28', views: 300 },
  { id: '3', song: "You've Got a Friend in Me", artist: 'Randy Newman', date: '2026-07-31', views: 200 },
];

test('searchCovers matches song title, case-insensitive', () => {
  const result = searchCovers(COVERS, 'swim');
  assert.deepStrictEqual(result.map(c => c.id), ['2']);
});

test('searchCovers matches artist name', () => {
  const result = searchCovers(COVERS, 'beatles');
  assert.deepStrictEqual(result.map(c => c.id), ['1']);
});

test('searchCovers with empty query returns everything', () => {
  assert.strictEqual(searchCovers(COVERS, '').length, 3);
});

test('sortCovers newest puts latest date first', () => {
  const result = sortCovers(COVERS, 'newest');
  assert.deepStrictEqual(result.map(c => c.id), ['3', '2', '1']);
});

test('sortCovers oldest puts earliest date first', () => {
  const result = sortCovers(COVERS, 'oldest');
  assert.deepStrictEqual(result.map(c => c.id), ['1', '2', '3']);
});

test('sortCovers popular sorts by views descending', () => {
  const result = sortCovers(COVERS, 'popular');
  assert.deepStrictEqual(result.map(c => c.id), ['2', '3', '1']);
});

test('sortCovers artist sorts alphabetically by artist', () => {
  // Loudon Wainwright III < Randy Newman < The Beatles
  const result = sortCovers(COVERS, 'artist');
  assert.deepStrictEqual(result.map(c => c.id), ['2', '3', '1']);
});

test('sortCovers title sorts alphabetically by song', () => {
  // The Swimming Song < Two of Us < You've Got a Friend in Me
  const result = sortCovers(COVERS, 'title');
  assert.deepStrictEqual(result.map(c => c.id), ['2', '1', '3']);
});
