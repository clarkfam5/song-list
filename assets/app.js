let covers = [];

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function render() {
  const query = document.getElementById('search').value;
  const mode = document.getElementById('sort').value;
  const filtered = CoversLib.sortCovers(CoversLib.searchCovers(covers, query), mode);
  document.getElementById('list').innerHTML = filtered.map(c => `
    <div class="cover">
      <img src="${escapeHtml(c.thumbnail)}" alt="${escapeHtml(c.song)}" width="120">
      <div>
        <strong>${escapeHtml(c.song)}</strong> by ${escapeHtml(c.artist)}<br>
        <span>${escapeHtml(c.date)}</span> &middot;
        <span>${c.views.toLocaleString()} views</span> &middot;
        <a href="${escapeHtml(c.url)}" target="_blank" rel="noopener">Watch</a>
      </div>
    </div>
  `).join('');
}

fetch('data/covers.json?t=' + Date.now())
  .then(r => r.json())
  .then(data => { covers = data; render(); });

document.getElementById('search').addEventListener('input', render);
document.getElementById('sort').addEventListener('change', render);
