/**
 * MoveX — global app behavior shared across every page.
 * Page-specific logic lives in landing.js / booking.js / dashboard.js.
 */

// ---------------------------------------------------------------------
// Dark mode
// ---------------------------------------------------------------------
const ThemeManager = {
  key: "movex-theme",
  init() {
    const saved = localStorage.getItem(this.key);
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (saved === "dark" || (!saved && prefersDark)) {
      document.documentElement.classList.add("dark");
    }
    this.syncToggles();
  },
  toggle() {
    document.documentElement.classList.toggle("dark");
    const isDark = document.documentElement.classList.contains("dark");
    localStorage.setItem(this.key, isDark ? "dark" : "light");
    this.syncToggles();
  },
  syncToggles() {
    const isDark = document.documentElement.classList.contains("dark");
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
      btn.setAttribute("aria-pressed", isDark ? "true" : "false");
    });
  },
};
ThemeManager.init();
document.addEventListener("click", (e) => {
  if (e.target.closest("[data-theme-toggle]")) ThemeManager.toggle();
});

// ---------------------------------------------------------------------
// PWA service worker registration
// ---------------------------------------------------------------------
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/service-worker.js").catch(() => {});
  });
}

// ---------------------------------------------------------------------
// Mobile navigation drawer
// ---------------------------------------------------------------------
document.addEventListener("click", (e) => {
  const opener = e.target.closest("[data-mobile-nav-open]");
  const closer = e.target.closest("[data-mobile-nav-close]");
  const drawer = document.querySelector("[data-mobile-nav]");
  if (!drawer) return;
  if (opener) {
    drawer.classList.remove("pointer-events-none", "opacity-0");
    drawer.querySelector("[data-mobile-nav-panel]").classList.remove("translate-x-full");
    document.body.classList.add("overflow-hidden");
  }
  if (closer || (drawer && e.target === drawer)) {
    drawer.classList.add("opacity-0");
    drawer.querySelector("[data-mobile-nav-panel]").classList.add("translate-x-full");
    document.body.classList.remove("overflow-hidden");
    setTimeout(() => drawer.classList.add("pointer-events-none"), 300);
  }
});

// ---------------------------------------------------------------------
// Responsive dashboard sidebar (off-canvas on mobile)
// ---------------------------------------------------------------------
document.addEventListener("click", (e) => {
  const opener = e.target.closest("[data-sidebar-open]");
  const closer = e.target.closest("[data-sidebar-close]");
  const sidebar = document.querySelector("[data-sidebar]");
  if (!sidebar) return;
  if (opener) {
    sidebar.classList.remove("-translate-x-full");
    sidebar.nextElementSibling?.classList.remove("hidden");
  }
  if (closer) {
    sidebar.classList.add("-translate-x-full");
    sidebar.nextElementSibling?.classList.add("hidden");
  }
});

// ---------------------------------------------------------------------
// Scroll reveal (IntersectionObserver-driven, respects prefers-reduced-motion)
// ---------------------------------------------------------------------
const revealEls = document.querySelectorAll("[data-reveal]");
if (revealEls.length) {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          const delay = entry.target.dataset.revealDelay || 0;
          setTimeout(() => entry.target.classList.add("is-visible"), Number(delay));
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  revealEls.forEach((el) => io.observe(el));
}

// ---------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------
window.showToast = function showToast(message, variant = "success") {
  let host = document.getElementById("toast-host");
  if (!host) {
    host = document.createElement("div");
    host.id = "toast-host";
    host.className = "fixed bottom-5 right-5 z-[100] flex flex-col gap-2 items-end";
    document.body.appendChild(host);
  }
  const colors = {
    success: "bg-charcoal-900 text-white dark:bg-emerald-500 dark:text-charcoal-950",
    error: "bg-rose-600 text-white",
  };
  const toast = document.createElement("div");
  toast.className = `toast ${colors[variant] || colors.success} rounded-xl shadow-lift px-4 py-3 text-sm font-medium max-w-xs`;
  toast.textContent = message;
  host.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
};

// ---------------------------------------------------------------------
// Generic tab component: [data-tabs] > [data-tab] triggers + [data-tab-panel]
// ---------------------------------------------------------------------
document.querySelectorAll("[data-tabs]").forEach((group) => {
  const triggers = group.querySelectorAll("[data-tab]");
  triggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const target = trigger.dataset.tab;
      triggers.forEach((t) => t.classList.remove("is-active"));
      trigger.classList.add("is-active");
      group.querySelectorAll("[data-tab-panel]").forEach((panel) => {
        panel.classList.toggle("hidden", panel.dataset.tabPanel !== target);
      });
    });
  });
});
