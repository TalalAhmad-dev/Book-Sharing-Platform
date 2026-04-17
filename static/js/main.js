document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss flash messages
  const flashes = document.querySelectorAll(".alert-dismissible");
  flashes.forEach((flash) => {
    setTimeout(() => {
      flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 600);
    }, 4000);
  });

  // Bootstrap Toasts Initialization
  var toastElList = [].slice.call(document.querySelectorAll(".toast"));
  var toastList = toastElList.map(function (toastEl) {
    return new bootstrap.Toast(toastEl);
  });
  toastList.forEach(function (toast) {
    toast.show();
  });

  // Bootstrap Popovers Initialization
  const popoverTriggerList = document.querySelectorAll(
    '[data-bs-toggle="popover"]',
  );
  const popoverList = [...popoverTriggerList].map(
    (popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl),
  );
});
