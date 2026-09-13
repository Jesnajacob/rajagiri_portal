// RCSS Connect - shared vanilla JS

document.addEventListener("DOMContentLoaded", function () {
  initPasswordToggles();
  initConfirmDialogs();
  initMarkAsRead();
  initLiveFilter();
  initFormValidation();
  animateCounters();
});

function getCsrfToken() {
  const el = document.querySelector('meta[name="csrf-token"]');
  return el ? el.getAttribute("content") : "";
}

// ---------- Password visibility toggle ----------
function initPasswordToggles() {
  document.querySelectorAll(".toggle-password").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (!input) return;
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      const icon = btn.querySelector("i");
      if (icon) {
        icon.classList.toggle("bi-eye");
        icon.classList.toggle("bi-eye-slash");
      }
    });
  });
}

// ---------- Confirmation dialogs for destructive actions ----------
function initConfirmDialogs() {
  document.querySelectorAll("[data-confirm]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      const msg = el.getAttribute("data-confirm") || "Are you sure?";
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
}

// ---------- Notification mark-as-read (AJAX) ----------
function initMarkAsRead() {
  document.querySelectorAll(".mark-read-btn").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const url = btn.getAttribute("data-url");
      fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
      }).then(function (resp) {
        if (resp.ok) {
          const item = btn.closest(".notif-item");
          if (item) item.classList.remove("unread");
          btn.remove();
          decrementBadge();
        }
      });
    });
  });

  const markAllBtn = document.getElementById("mark-all-read-btn");
  if (markAllBtn) {
    markAllBtn.addEventListener("click", function (e) {
      e.preventDefault();
      const url = markAllBtn.getAttribute("data-url");
      fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
      }).then(function (resp) {
        if (resp.ok) {
          document.querySelectorAll(".notif-item").forEach(function (el) {
            el.classList.remove("unread");
          });
          document.querySelectorAll(".notif-badge").forEach(function (el) {
            el.remove();
          });
        }
      });
    });
  }
}

function decrementBadge() {
  document.querySelectorAll(".notif-badge").forEach(function (badge) {
    let count = parseInt(badge.textContent, 10) || 0;
    count = Math.max(0, count - 1);
    if (count === 0) {
      badge.remove();
    } else {
      badge.textContent = count;
    }
  });
}

// ---------- Live search / filter for lists ----------
function initLiveFilter() {
  document.querySelectorAll("[data-live-filter]").forEach(function (input) {
    const targetSelector = input.getAttribute("data-live-filter");
    input.addEventListener("keyup", function () {
      const term = input.value.toLowerCase();
      document.querySelectorAll(targetSelector).forEach(function (card) {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(term) ? "" : "none";
      });
    });
  });
}

// ---------- Simple client-side required-field validation ----------
function initFormValidation() {
  document.querySelectorAll("form.needs-validation").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });
}

// ---------- Animated dashboard counters ----------
function animateCounters() {
  document.querySelectorAll(".counter").forEach(function (el) {
    const target = parseInt(el.getAttribute("data-count"), 10) || 0;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 40));
    const timer = setInterval(function () {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = current;
    }, 20);
  });
}
