(function () {
    var counters = document.querySelectorAll('[data-github-stars]');
    if (!counters.length) return;

    function formatStars(value) {
        if (value < 1000) return String(value);
        return (Math.round(value / 100) / 10).toFixed(value < 10000 ? 1 : 0).replace(/\.0$/, '') + 'k';
    }

    fetch('https://api.github.com/repos/ranxi2001/zero2Agent', {
        headers: { 'Accept': 'application/vnd.github+json' }
    })
        .then(function (response) {
            if (!response.ok) throw new Error('GitHub API ' + response.status);
            return response.json();
        })
        .then(function (repo) {
            var value = Number(repo.stargazers_count);
            if (!Number.isFinite(value)) return;
            counters.forEach(function (counter) {
                counter.textContent = formatStars(value);
                counter.setAttribute('title', value + ' GitHub Stars');
            });
        })
        .catch(function () {
            counters.forEach(function (counter) { counter.textContent = '★'; });
        });
})();