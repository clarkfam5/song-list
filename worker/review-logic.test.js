const test = require('node:test');
const assert = require('node:assert');
const { applyReviewAction, utf8ToBase64, base64ToUtf8 } = require('./review-logic.js');

const COVERS = [{ id: '1', song: 'Old', artist: 'X', date: '2020-01-01', views: 1, thumbnail: 't', url: 'u' }];
const PENDING = [{ id: '2', title: 'New Vlog', date: '2026-08-01', views: 5, thumbnail: 't2', url: 'u2' }];

test('publish moves item from pending to covers with the edited fields', () => {
  const result = applyReviewAction(COVERS, PENDING, { type: 'publish', id: '2', song: 'Fixed Song', artist: 'Fixed Artist' });
  assert.strictEqual(result.pending.length, 0);
  assert.strictEqual(result.covers.length, 2);
  assert.deepStrictEqual(result.covers[1], {
    id: '2', date: '2026-08-01', views: 5, thumbnail: 't2', url: 'u2',
    song: 'Fixed Song', artist: 'Fixed Artist',
  });
});

test('discard removes the item from pending without touching covers', () => {
  const result = applyReviewAction(COVERS, PENDING, { type: 'discard', id: '2' });
  assert.strictEqual(result.pending.length, 0);
  assert.deepStrictEqual(result.covers, COVERS);
});

test('unknown id throws', () => {
  assert.throws(() => applyReviewAction(COVERS, PENDING, { type: 'discard', id: 'missing' }));
});

test('utf8ToBase64/base64ToUtf8 round-trip non-Latin1 characters', () => {
  // Real content from the data files: curly apostrophes, curly quotes,
  // and emoji all fall outside what plain btoa()/atob() can handle,
  // which caused a real production failure (500 error) before this fix.
  const original = 'Messin’ with the Kid “Live” 😊';
  const encoded = utf8ToBase64(original);
  assert.strictEqual(base64ToUtf8(encoded), original);
});
