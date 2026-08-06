const WORKER_URL = 'https://covers-review.clarkfamilyband.workers.dev';
const SECRET_STORAGE_KEY = 'covers_review_secret';

function getSecret() {
  let secret = localStorage.getItem(SECRET_STORAGE_KEY);
  if (!secret) {
    secret = prompt('Enter the review secret:');
    localStorage.setItem(SECRET_STORAGE_KEY, secret);
  }
  return secret;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

async function submitAction(action) {
  await fetch(WORKER_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-review-secret': getSecret() },
    body: JSON.stringify(action),
  });
  location.reload();
}

function render(items) {
  document.getElementById('list').innerHTML = items.map(item => `
    <div class="cover" data-id="${escapeHtml(item.id)}">
      <img src="${escapeHtml(item.thumbnail)}" width="120">
      <div>
        <div>${escapeHtml(item.title || '(no title)')} &middot; ${escapeHtml(item.date)}</div>
        <label>Song <input class="song" value="${escapeHtml(item.song || '')}"></label>
        <label>Artist <input class="artist" value="${escapeHtml(item.artist || '')}"></label>
        <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">Watch</a>
        <button class="publish">Publish</button>
        <button class="discard">Discard</button>
      </div>
    </div>
  `).join('');

  document.querySelectorAll('.publish').forEach(btn => btn.addEventListener('click', e => {
    const card = e.target.closest('.cover');
    submitAction({
      type: 'publish',
      id: card.dataset.id,
      song: card.querySelector('.song').value,
      artist: card.querySelector('.artist').value,
    });
  }));
  document.querySelectorAll('.discard').forEach(btn => btn.addEventListener('click', e => {
    submitAction({ type: 'discard', id: e.target.closest('.cover').dataset.id });
  }));
}

fetch('data/pending.json').then(r => r.json()).then(render);
