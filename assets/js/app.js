/* ===== Sidebar accordion ===== */
document.querySelectorAll(".nav-toggle-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
        var module = btn.closest(".nav-module");
        if (!module) return;
        var willOpen = !module.classList.contains("is-open");
        if (willOpen) {
            document.querySelectorAll(".nav-module.is-open").forEach(function (m) {
                if (m !== module) m.classList.remove("is-open");
            });
        }
        module.classList.toggle("is-open");
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


/* ===== Theme toggle ===== */
(function () {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;

    function currentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    }

    btn.addEventListener('click', function () {
        var next = currentTheme() === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('z2a-theme', next);
        swapHljsTheme(next);
        rerenderMermaid(next);
    });

    function swapHljsTheme(theme) {
        var link = document.getElementById('hljs-theme');
        if (!link) return;
        link.href = theme === 'light'
            ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css'
            : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css';
    }

    var darkVars = {
        background: '#0a0a10', primaryColor: '#1a2535',
        primaryTextColor: '#d1d5db', primaryBorderColor: '#334155',
        lineColor: '#10b981', secondaryColor: '#161e2e',
        tertiaryColor: '#161e2e', edgeLabelBackground: '#0d0d12',
        clusterBkg: '#13131f'
    };
    var lightVars = {
        background: '#ffffff', primaryColor: '#dbeafe',
        primaryTextColor: '#1a1a2e', primaryBorderColor: '#93c5fd',
        lineColor: '#059669', secondaryColor: '#f0fdf4',
        tertiaryColor: '#ecfdf5', edgeLabelBackground: '#ffffff',
        clusterBkg: '#f8fafc'
    };

    function rerenderMermaid(theme) {
        if (typeof mermaid === 'undefined') return;
        var els = document.querySelectorAll('.mermaid');
        if (!els.length) return;

        mermaid.initialize({
            startOnLoad: false,
            securityLevel: 'loose',
            theme: theme === 'light' ? 'default' : 'dark',
            themeVariables: theme === 'light' ? lightVars : darkVars,
            flowchart: { curve: 'basis', htmlLabels: false, padding: 16 }
        });

        els.forEach(function (el) {
            var src = el.dataset.mermaidSrc;
            if (!src) return;
            el.removeAttribute('data-processed');
            el.innerHTML = src;
            mermaid.init(undefined, el);
        });
    }

    /* On initial load, swap hljs if light */
    if (currentTheme() === 'light') {
        swapHljsTheme('light');
    }

    /* Listen for OS theme change when no stored preference */
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function (e) {
        if (!localStorage.getItem('z2a-theme')) {
            var theme = e.matches ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', theme);
            swapHljsTheme(theme);
            rerenderMermaid(theme);
        }
    });
})();
