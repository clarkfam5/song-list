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

// btoa()/atob() only handle Latin1 text, but the data files contain
// curly quotes, emoji, and other non-Latin1 characters throughout (e.g.
// song titles with curly apostrophes), so encoding/decoding must go
// through UTF-8 bytes explicitly rather than passing strings straight in.
function utf8ToBase64(str) {
  const bytes = new TextEncoder().encode(str);
  let binary = '';
  bytes.forEach(b => { binary += String.fromCharCode(b); });
  return btoa(binary);
}

function base64ToUtf8(b64) {
  const binary = atob(b64);
  const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

module.exports = { applyReviewAction, utf8ToBase64, base64ToUtf8 };
