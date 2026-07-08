/**
 * Booking widgets — ride & delivery pages.
 * Fare estimates call the /book/estimate mock endpoint; in production this
 * would be replaced with a real pricing/dispatch service call.
 */

function selectTier(el) {
  document.querySelectorAll(".tier-option").forEach((opt) => {
    opt.classList.remove("border-ink-900", "dark:border-canopy-500", "bg-ink-50", "dark:bg-ink-800");
    opt.classList.add("border-transparent");
  });
  el.classList.remove("border-transparent");
  el.classList.add("border-ink-900", "dark:border-canopy-500", "bg-ink-50", "dark:bg-ink-800");

  const tier = el.dataset.tier;
  fetch("/book/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tier }),
  })
    .then((r) => r.json())
    .then((data) => {
      el.querySelector(".price-tag").textContent = `$${data.fare_low.toFixed(2)}–$${data.fare_high.toFixed(2)}`;
    })
    .catch(() => {});
}

function setWhen(el) {
  document.querySelectorAll("[data-when]").forEach((btn) => {
    btn.classList.remove("btn-secondary", "is-active");
    btn.classList.add("btn-ghost", "border", "border-ink-200", "dark:border-ink-700");
  });
  el.classList.remove("btn-ghost", "border", "border-ink-200", "dark:border-ink-700");
  el.classList.add("btn-secondary", "is-active");
}

function requestRide() {
  const dropoff = document.getElementById("dropoff");
  if (dropoff && !dropoff.value.trim()) {
    dropoff.classList.add("ring-2", "ring-rose-400");
    dropoff.focus();
    if (window.showToast) showToast("Add a destination before requesting a ride", "error");
    return;
  }

  const idle = document.getElementById("idleState");
  const searching = document.getElementById("searchState");
  const matched = document.getElementById("matchedState");
  const btn = document.getElementById("requestBtn");

  idle?.classList.add("hidden");
  matched?.classList.add("hidden");
  searching?.classList.remove("hidden");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = "Finding your driver…";
  }

  setTimeout(() => {
    searching?.classList.add("hidden");
    matched?.classList.remove("hidden");
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = 'Trip in progress <i data-lucide="check" class="w-4 h-4"></i>';
    }
    if (window.lucide) lucide.createIcons();
    if (window.showToast) showToast("Driver matched — Tendai is on the way!");
  }, 2600);
}

// Delivery page: parcel size selector
function selectParcelSize(el) {
  document.querySelectorAll(".parcel-option").forEach((opt) => {
    opt.classList.remove("border-ink-900", "dark:border-canopy-500", "bg-ink-50", "dark:bg-ink-800");
    opt.classList.add("border-transparent");
  });
  el.classList.remove("border-transparent");
  el.classList.add("border-ink-900", "dark:border-canopy-500", "bg-ink-50", "dark:bg-ink-800");
}

function requestDelivery() {
  const dropoff = document.getElementById("delivery-dropoff");
  if (dropoff && !dropoff.value.trim()) {
    dropoff.classList.add("ring-2", "ring-rose-400");
    dropoff.focus();
    if (window.showToast) showToast("Add a drop-off address first", "error");
    return;
  }
  const btn = document.getElementById("requestDeliveryBtn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = "Matching a courier…";
  }
  setTimeout(() => {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = 'Courier assigned <i data-lucide="check" class="w-4 h-4"></i>';
    }
    if (window.lucide) lucide.createIcons();
    if (window.showToast) showToast("Courier assigned — pickup in 4 minutes");
  }, 2200);
}
