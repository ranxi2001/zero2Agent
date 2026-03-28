/* ===== Sidebar accordion ===== */
document.querySelectorAll(".nav-toggle-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
        var module = btn.closest(".nav-module");
        if (module) module.classList.toggle("is-open");
    });
});


/* ===== TOC generation ===== */
(function () {
    var tocList = document.getElementById("toc-list");
    var tocNav  = document.getElementById("doc-toc");
    var article = document.querySelector(".doc-article");
    if (!tocList || !article) return;

    var headings = Array.prototype.slice.call(article.querySelectorAll("h2, h3"));

    if (headings.length === 0) {
        if (tocNav) tocNav.style.display = "none";
        return;
    }

    headings.forEach(function (h, i) {
        if (!h.id) {
            var slug = h.textContent.trim()
                .replace(/\s+/g, "-")
                .replace(/[^\w\u4e00-\u9fff\-]/g, "")
                .slice(0, 50);
            h.id = "h-" + i + "-" + slug;
        }
        var a = document.createElement("a");
        a.href    = "#" + h.id;
        a.textContent = h.textContent;
        a.className = "toc-item " + (h.tagName === "H3" ? "toc-h3" : "toc-h2");
        a.dataset.target = h.id;
        tocList.appendChild(a);
    });

    /* Scroll-spy */
    var links = Array.prototype.slice.call(tocList.querySelectorAll(".toc-item"));
    var active = null;

    function activate(link) {
        if (active) active.classList.remove("is-active");
        active = link;
        if (active) active.classList.add("is-active");
    }

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                var id = entry.target.id;
                var match = links.find(function (l) { return l.dataset.target === id; });
                if (match) activate(match);
            }
        });
    }, { rootMargin: "-8% 0px -82% 0px", threshold: 0 });

    headings.forEach(function (h) { observer.observe(h); });
})();


/* ===== Prev / Next pager ===== */
(function () {
    var nav = window.Z2A_NAV;
    if (!nav || !nav.length) return;

    var base = (window.Z2A_BASE || '').replace(/\/$/, '');
    var url  = window.location.pathname;

    /* find current article index */
    var cur = -1;
    for (var i = 0; i < nav.length; i++) {
        if (url.indexOf('/' + nav[i].path + '/') !== -1 ||
            url.indexOf('/' + nav[i].path + 'index') !== -1) {
            cur = i; break;
        }
    }
    if (cur === -1) return;

    function setBtn(id, titleId, item) {
        var btn = document.getElementById(id);
        if (!btn) return;
        btn.href = base + '/' + item.path + '/index.html';
        document.getElementById(titleId).textContent = item.title;
        btn.classList.add('is-ready');
        /* prefetch so the page loads instantly on click */
        var lnk = document.createElement('link');
        lnk.rel  = 'prefetch';
        lnk.href = btn.href;
        document.head.appendChild(lnk);
    }

    if (cur > 0)              setBtn('pager-prev', 'pager-prev-title', nav[cur - 1]);
    if (cur < nav.length - 1) setBtn('pager-next', 'pager-next-title', nav[cur + 1]);
})();


/* ===== Back to top ===== */
(function () {
    var btn = document.getElementById('back-to-top');
    if (!btn) return;
    var shown = false;
    window.addEventListener('scroll', function () {
        var should = window.scrollY > 320;
        if (should !== shown) {
            shown = should;
            btn.classList.toggle('is-visible', shown);
        }
    }, { passive: true });
    btn.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
})();
