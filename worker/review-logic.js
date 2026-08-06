function applyReviewAction(covers, pending, action) {
  const idx = pending.findIndex(p => p.id === action.id);
  if (idx === -1) throw new Error('pending item not found: ' + action.id);
  const item = pending[idx];
  const newPending = pending.slice(0, idx).concat(pending.slice(idx + 1));

  if (action.type === 'discard') {
    return { covers, pending: newPending };
  }

  const published = {
    id: item.id, date: item.date, views: item.views,
    thumbnail: item.thumbnail, url: item.url,
    song: action.song, artist: action.artist,
  };
  return { covers: covers.concat([published]), pending: newPending };
}

module.exports = { applyReviewAction };
