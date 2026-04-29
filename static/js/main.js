document.addEventListener("DOMContentLoaded", function () {
  const parseTargetIndexes = (value) => {
    if (!value) {
      return [];
    }

    return value
      .split(",")
      .map((part) => Number.parseInt(part.trim(), 10))
      .filter((part) => !Number.isNaN(part));
  };

  const parseDefaultOrder = (value) => {
    if (!value) {
      return [[0, "desc"]];
    }

    const parsed = value
      .split(";")
      .map((segment) => segment.trim())
      .filter(Boolean)
      .map((segment) => {
        const [column, direction] = segment.split(",");
        const columnIndex = Number.parseInt((column || "").trim(), 10);
        const orderDirection = (direction || "asc").trim().toLowerCase();

        if (Number.isNaN(columnIndex)) {
          return null;
        }

        return [columnIndex, orderDirection === "desc" ? "desc" : "asc"];
      })
      .filter(Boolean);

    return parsed.length ? parsed : [[0, "desc"]];
  };

  const buildColumnDefs = (table) => {
    const nonOrderableTargets = parseTargetIndexes(
      table.dataset.nonOrderableTargets,
    );
    const nonSearchableTargets = parseTargetIndexes(
      table.dataset.nonSearchableTargets,
    );
    const noExportTargets = parseTargetIndexes(table.dataset.noExportTargets);
    const columnDefs = [];

    if (nonOrderableTargets.length) {
      columnDefs.push({
        targets: nonOrderableTargets,
        orderable: false,
      });
    }

    if (nonSearchableTargets.length) {
      columnDefs.push({
        targets: nonSearchableTargets,
        searchable: false,
      });
    }

    if (noExportTargets.length) {
      columnDefs.push({
        targets: noExportTargets,
        className: "dt-no-export",
      });
    }

    return columnDefs;
  };

  const buildButtons = (table) => {
    if (table.dataset.enableButtons === "false") {
      return [];
    }

    const exportTitle = table.dataset.exportTitle || document.title;
    const exportOptions = {
      columns: ":visible:not(.dt-no-export)",
    };

    return [
      {
        extend: "collection",
        text: "Export Data",
        split: [
          {
            extend: "pdf",
            title: exportTitle,
            exportOptions,
            className: "dropdown-item",
          },
          {
            extend: "excel",
            title: exportTitle,
            exportOptions,
            className: "dropdown-item",
          },
          {
            extend: "csv",
            title: exportTitle,
            exportOptions,
            className: "dropdown-item",
          },
          {
            extend: "print",
            title: exportTitle,
            exportOptions,
            className: "dropdown-item",
          },
        ],
      },
      "spacer",
      "copy",
    ];
  };

  const initializeDataTables = () => {
    if (typeof DataTable !== "function") {
      return;
    }

    document.querySelectorAll("table.dataTable").forEach((table) => {
      if (table.dataset.dtInitialized === "true") {
        return;
      }

      const columnDefs = buildColumnDefs(table);
      const buttons = buildButtons(table);

      const baseConfig = {
        colReorder: true,
        columnControl: [
          "order",
          [
            "searchDropdown",
            "colVisDropdown",
            "spacer",
            "orderClear",
            "searchClear",
          ],
        ],
        ordering: {
          indicators: false,
          handler: false,
        },
        responsive: true,
        keys: true,
        order: parseDefaultOrder(table.dataset.defaultOrder),
        pageLength: Number.parseInt(table.dataset.pageLength || "10", 10),
        columnDefs,
      };

      if (buttons.length) {
        baseConfig.layout = {
          topEnd: ["search", "buttons"],
          bottomStart: ["pageLength"],
          topStart: ["info"],
          bottomEnd: {
            paging: {
              buttons: 3,
            },
          },
        };
        baseConfig.lengthMenu = [5, 10, 25, 50, { label: "All", value: -1 }];
        baseConfig.buttons = buttons;
      } else {
        baseConfig.layout = {
          topEnd: ["search"],
          bottomStart: ["pageLength"],
          topStart: ["info"],
          bottomEnd: {
            paging: {
              buttons: 3,
            },
          },
        };
        baseConfig.lengthMenu = [5, 10, 25, 50, { label: "All", value: -1 }];
      }

      new DataTable(table, baseConfig);
      table.dataset.dtInitialized = "true";
    });
  };

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

    $(".js-select2")
      .not(".js-select2-multiple")
      .each(function () {
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

  // DataTables Initialization
  initializeDataTables();
});
