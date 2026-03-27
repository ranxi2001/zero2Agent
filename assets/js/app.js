const navToggle = document.querySelector(".nav-toggle");
const navLinks = document.querySelector(".nav-links");

if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
        navLinks.classList.toggle("is-open");
    });
}

if (window.location.protocol === "file:") {
    document.querySelectorAll("[data-file-href]").forEach((link) => {
        link.setAttribute("href", link.getAttribute("data-file-href"));
    });
}
