/* ===== TOC Generation ===== */
(function () {
    var tocList = document.getElementById("toc-list");
    var article = document.querySelector(".doc-article");
    if (!tocList || !article) return;

    var headings = article.querySelectorAll("h2, h3");
    if (headings.length === 0) {
        var toc = document.getElementById("doc-toc");
        if (toc) toc.style.display = "none";
        return;
    }

    var items = [];
    headings.forEach(function (h, i) {
        if (!h.id) {
            h.id = "toc-" + i + "-" + h.textContent.trim().replace(/\s+/g, "-").replace(/[^\w\-\u4e00-\u9fff]/g, "").slice(0, 40);
        }
        var a = document.createElement("a");
        a.href = "#" + h.id;
        a.textContent = h.textContent;
        a.className = "toc-item " + (h.tagName === "H3" ? "toc-h3" : "toc-h2");
        a.dataset.id = h.id;
        tocList.appendChild(a);
        items.push({ el: h, link: a });
    });

    /* Scroll-spy via IntersectionObserver */
    var activeLink = null;

    function setActive(link) {
        if (activeLink) activeLink.classList.remove("is-active");
        activeLink = link;
        if (activeLink) activeLink.classList.add("is-active");
    }

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                var match = items.find(function (it) { return it.el === entry.target; });
                if (match) setActive(match.link);
            }
        });
    }, { rootMargin: "-10% 0px -80% 0px", threshold: 0 });

    items.forEach(function (it) { observer.observe(it.el); });
})();

/* ===== Mobile nav toggle (legacy) ===== */
var navToggle = document.querySelector(".nav-toggle");
var navLinks = document.querySelector(".nav-links");
if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
        navLinks.classList.toggle("is-open");
    });
}
