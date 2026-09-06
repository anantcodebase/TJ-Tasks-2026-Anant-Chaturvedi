const menuBtn = document.getElementById("menuBtn");
const navLinks = document.getElementById("navLinks");

menuBtn.addEventListener("click", () => {
    navLinks.classList.toggle("active");
});

document.querySelectorAll(".nav-links a").forEach(link => {
    link.addEventListener("click", () => {
        navLinks.classList.remove("active");
    });
});

const typingText = document.getElementById("typingText");

const roles = [
    "DSA enthusiast",
    "C++ developer",
    "problem solver",
    "developer in progress",
    "future app builder"
];

let roleIndex = 0;
let charIndex = 0;
let deleting = false;

function typeEffect() {
    const currentRole = roles[roleIndex];

    if (!deleting) {
        typingText.textContent = currentRole.substring(0, charIndex + 1);
        charIndex++;

        if (charIndex === currentRole.length) {
            deleting = true;
            setTimeout(typeEffect, 1500);
            return;
        }
    } else {
        typingText.textContent = currentRole.substring(0, charIndex - 1);
        charIndex--;

        if (charIndex === 0) {
            deleting = false;
            roleIndex = (roleIndex + 1) % roles.length;
        }
    }

    setTimeout(typeEffect, deleting ? 45 : 80);
}

typeEffect();

const cursorGlow = document.querySelector(".cursor-glow");

document.addEventListener("mousemove", event => {
    cursorGlow.style.left = `${event.clientX}px`;
    cursorGlow.style.top = `${event.clientY}px`;
});

const skillTabs = document.querySelectorAll(".skill-tab");
const skillCards = document.querySelectorAll(".skill-card");

skillTabs.forEach(tab => {
    tab.addEventListener("click", () => {
        skillTabs.forEach(item => item.classList.remove("active"));
        tab.classList.add("active");

        const filter = tab.dataset.filter;

        skillCards.forEach(card => {
            if (filter === "all" || card.dataset.category === filter) {
                card.classList.remove("hidden");
            } else {
                card.classList.add("hidden");
            }
        });
    });
});

const observer = new IntersectionObserver(
    entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    },
    {
        threshold: 0.12
    }
);

document.querySelectorAll(".section-heading, .skill-card, .project-card, .stat-card, .learning-box, .youtube-grid, .contact-grid").forEach(element => {
    element.style.opacity = "0";
    element.style.transform = "translateY(25px)";
    element.style.transition = "opacity 0.7s ease, transform 0.7s ease";
    observer.observe(element);
});

const contactForm = document.getElementById("contactForm");
const formStatus = document.getElementById("formStatus");

contactForm.addEventListener("submit", event => {
    event.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const message = document.getElementById("message").value.trim();

    if (!name || !email || !message) {
        formStatus.textContent = "Please fill in everything first.";
        return;
    }

    formStatus.textContent = `Message received, ${name}. Now go touch some grass.`;

    contactForm.reset();
});

const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {
    if (window.scrollY > 40) {
        navbar.style.background = "rgba(5, 5, 7, 0.94)";
    } else {
        navbar.style.background = "rgba(5, 5, 7, 0.78)";
    }
});
