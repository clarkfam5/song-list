(function (exports) {
  function searchCovers(covers, query) {
    const q = query.trim().toLowerCase();
    if (!q) return covers;
    return covers.filter(c =>
      c.song.toLowerCase().includes(q) || c.artist.toLowerCase().includes(q)
    );
  }

  const SORTERS = {
    newest: (a, b) => b.date.localeCompare(a.date),
    oldest: (a, b) => a.date.localeCompare(b.date),
    popular: (a, b) => b.views - a.views,
    artist: (a, b) => a.artist.localeCompare(b.artist),
    title: (a, b) => a.song.localeCompare(b.song),
  };

  function sortCovers(covers, mode) {
    const sorter = SORTERS[mode] || SORTERS.newest;
    return [...covers].sort(sorter);
  }

  exports.searchCovers = searchCovers;
  exports.sortCovers = sortCovers;
})(typeof module !== 'undefined' ? module.exports : (window.CoversLib = {}));
