import { applyReviewAction, utf8ToBase64, base64ToUtf8 } from './review-logic.js';

const REPO = 'clarkfam5/song-list';
const BRANCH = 'main';

async function getFile(path, token) {
  const res = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}?ref=${BRANCH}`, {
    headers: { Authorization: `Bearer ${token}`, 'User-Agent': 'covers-worker' },
  });
  const json = await res.json();
  return { content: JSON.parse(base64ToUtf8(json.content)), sha: json.sha };
}

async function putFile(path, content, sha, token, message) {
  await fetch(`https://api.github.com/repos/${REPO}/contents/${path}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, 'User-Agent': 'covers-worker' },
    body: JSON.stringify({
      message,
      content: utf8ToBase64(JSON.stringify(content, null, 2) + '\n'),
      sha,
      branch: BRANCH,
    }),
  });
}

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') return new Response('Not found', { status: 404 });
    if (request.headers.get('x-review-secret') !== env.REVIEW_SECRET) {
      return new Response('Unauthorized', { status: 401 });
    }
    const action = await request.json();

    const [coversFile, pendingFile] = await Promise.all([
      getFile('data/covers.json', env.GITHUB_TOKEN),
      getFile('data/pending.json', env.GITHUB_TOKEN),
    ]);

    const { covers, pending } = applyReviewAction(coversFile.content, pendingFile.content, action);

    await Promise.all([
      putFile('data/covers.json', covers, coversFile.sha, env.GITHUB_TOKEN, `Publish review: ${action.id}`),
      putFile('data/pending.json', pending, pendingFile.sha, env.GITHUB_TOKEN, `Remove from pending: ${action.id}`),
    ]);

    return new Response('OK');
  },
};
