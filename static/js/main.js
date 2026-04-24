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

  // Select2 Initialization
  if (window.jQuery && typeof window.jQuery.fn.select2 === "function") {
    const $ = window.jQuery;

    $(".js-select2").not(".js-select2-multiple").each(function () {
      const $select = $(this);
      $select.select2({
        width: "100%",
        minimumResultsForSearch: 6,
        placeholder: $select.data("placeholder") || "",
      });
    });

    $(".js-select2-multiple").each(function () {
      const $select = $(this);
      $select.select2({
        width: "100%",
        closeOnSelect: false,
        allowClear: true,
        minimumResultsForSearch: 0,
        placeholder: $select.data("placeholder") || "",
      });
    });
  }
});
