/* ===== Sidebar accordion ===== */
document.querySelectorAll(".nav-toggle-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
        var module = btn.closest(".nav-module");
        if (module) module.classList.toggle("is-open");
    });
});

/* ===== Mermaid diagrams ===== */
(function () {
    if (typeof mermaid === "undefined") return;

    // Rouge wraps ```mermaid as .language-mermaid.highlighter-rouge > .highlight > pre > code
    var blocks = document.querySelectorAll(".language-mermaid code");
    if (blocks.length === 0) return;

    blocks.forEach(function (code) {
        var container = code.closest(".language-mermaid");
        if (!container) return;
        var div = document.createElement("div");
        div.className = "mermaid";
        // Use textContent to avoid any HTML escaping issues
        div.textContent = code.textContent;
        container.parentNode.replaceChild(div, container);
    });

    mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        themeVariables: {
            background: "#0a0a10",
            primaryColor: "#1a2535",
            primaryTextColor: "#d1d5db",
            primaryBorderColor: "#334155",
            lineColor: "#10b981",
            secondaryColor: "#161e2e",
            tertiaryColor: "#161e2e",
            edgeLabelBackground: "#0d0d12",
            clusterBkg: "#13131f",
            fontFamily: '"Noto Sans SC", "Inter", sans-serif',
            fontSize: "14px",
        },
        flowchart: { curve: "basis", htmlLabels: false, padding: 16 },
        sequence: { actorFontFamily: '"Noto Sans SC", sans-serif', messageFontFamily: '"Noto Sans SC", sans-serif' },
    });

    mermaid.run({ querySelector: ".mermaid" });
})();

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
