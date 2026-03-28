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
