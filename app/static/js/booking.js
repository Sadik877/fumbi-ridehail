/**
 * Booking widgets — ride & delivery pages.
 * Fare estimates call the /book/estimate mock endpoint; in production this
 * would be replaced with a real pricing/dispatch service call.
 */

function selectTier(el) {
  document.querySelectorAll(".tier-option").forEach((opt) => {
    opt.classList.remove("border-charcoal-900", "dark:border-emerald-500", "bg-charcoal-50", "dark:bg-charcoal-800");
    opt.classList.add("border-transparent");
  });
  el.classList.remove("border-transparent");
  el.classList.add("border-charcoal-900", "dark:border-emerald-500", "bg-charcoal-50", "dark:bg-charcoal-800");

  const tier = el.dataset.tier;
  const hiddenInput = document.getElementById("vehicleTypeInput");
  if (hiddenInput) hiddenInput.value = tier;

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  const pickup = document.getElementById("pickup")?.value;
  const dropoff = document.getElementById("dropoff")?.value;
  if (!dropoff) return; // nothing to estimate yet

  fetch("/book/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
    body: JSON.stringify({ tier, pickup_address: pickup, dropoff_address: dropoff }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.error) return;
      el.querySelector(".price-tag").textContent = `₦${data.fare_low.toLocaleString()}–₦${data.fare_high.toLocaleString()}`;
    })
    .catch(() => {});
}

function setWhen(el) {
  document.querySelectorAll("[data-when]").forEach((btn) => {
    btn.classList.remove("btn-secondary", "is-active");
    btn.classList.add("btn-ghost", "border", "border-charcoal-200", "dark:border-charcoal-700");
  });
  el.classList.remove("btn-ghost", "border", "border-charcoal-200", "dark:border-charcoal-700");
  el.classList.add("btn-secondary", "is-active");
}

// Ride form: show a brief "finding your driver" state, then let the
// browser continue with the real POST/redirect to booking.history.
document.getElementById("rideForm")?.addEventListener("submit", function (e) {
  const dropoff = document.getElementById("dropoff");
  if (dropoff && !dropoff.value.trim()) {
    e.preventDefault();
    dropoff.classList.add("ring-2", "ring-rose-400");
    dropoff.focus();
    if (window.showToast) showToast("Add a destination before requesting a ride", "error");
    return;
  }
  document.getElementById("idleState")?.classList.add("hidden");
  document.getElementById("searchState")?.classList.remove("hidden");
  const btn = document.getElementById("requestBtn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = "Finding your driver…";
  }
});

// Delivery page: parcel size selector
function selectParcelSize(el) {
  document.querySelectorAll(".parcel-option").forEach((opt) => {
    opt.classList.remove("border-charcoal-900", "dark:border-emerald-500", "bg-charcoal-50", "dark:bg-charcoal-800");
    opt.classList.add("border-transparent");
  });
  el.classList.remove("border-transparent");
  el.classList.add("border-charcoal-900", "dark:border-emerald-500", "bg-charcoal-50", "dark:bg-charcoal-800");
  const hiddenInput = document.getElementById("parcelSizeInput");
  if (hiddenInput) hiddenInput.value = el.dataset.size;
}

document.getElementById("deliveryForm")?.addEventListener("submit", function (e) {
  const dropoff = document.getElementById("delivery-dropoff");
  if (dropoff && !dropoff.value.trim()) {
    e.preventDefault();
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
});
