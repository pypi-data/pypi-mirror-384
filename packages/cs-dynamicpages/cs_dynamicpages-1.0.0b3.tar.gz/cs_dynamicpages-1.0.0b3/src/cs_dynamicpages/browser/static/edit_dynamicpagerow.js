/**
 * JavaScript for DynamicPageRow edit form
 * Loads configuration from control panel and applies it to the form
 */

(function () {
  "use strict";

  // Store row type configurations globally
  let rowTypeConfigs = {};
  let rowTypeSelect = null;

  function initialize(context = document) {
    // Check if we're in an edit form or an add form
    const isEditForm =
      context === document &&
      document.body.classList.contains("template-edit") &&
      document.body.classList.contains("portaltype-dynamicpagerow");

    // Check if we're in an add form or a dynamically added form
    const isAddForm = (context === document ? document : context).querySelector(
      "form.view-name-add-DynamicPageRow"
    );

    if (!isEditForm && !isAddForm) {
      return;
    }

    // Get configuration from control panel
    const baseUrl = document.body.dataset.portalUrl || "";
    fetch(
      `${baseUrl}/@registry/cs_dynamicpages.dynamic_pages_control_panel.row_type_fields`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        credentials: "same-origin",
      }
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        if (data && data.length > 0) {
          processRowTypeFields(data);
        }
      })
      .catch((error) => {
        console.error("Error loading row type fields:", error);
      });
  }

  function processRowTypeFields(rowTypeFields) {
    // Store all row type configurations
    rowTypeFields.forEach((rowTypeConfig) => {
      rowTypeConfigs[rowTypeConfig.row_type] = {
        fields: rowTypeConfig.each_row_type_fields || [],
      };
    });

    // Initial setup
    updateFieldVisibility();
  }

  function updateFieldVisibility() {
    rowTypeSelect = document.querySelector('select[name$=".row_type:list"]');
    if (!rowTypeSelect) return;

    // Remove previous event listener if it exists
    const newSelect = rowTypeSelect.cloneNode(true);
    rowTypeSelect.parentNode.replaceChild(newSelect, rowTypeSelect);
    rowTypeSelect = newSelect;

    // Add new event listener
    rowTypeSelect.addEventListener("change", toggleFields);

    // Initial setup - force update for the default value
    toggleFields();
  }

  function toggleFields() {
    const selectedRowType = rowTypeSelect.value;
    if (!selectedRowType) return;

    const config = rowTypeConfigs[selectedRowType];
    const allFields = document.querySelectorAll(".field");
    const rowTypeField = rowTypeSelect.closest(".field");

    // Show all fields first
    allFields.forEach((field) => {
      field.style.display = "";
    });

    // Always hide all fields except row type select by default
    allFields.forEach((field) => {
      if (field !== rowTypeField) {
        field.style.display = "none";
      }
    });

    // If we have a config for this row type, show its fields
    if (config && config.fields && config.fields.length > 0) {
      config.fields.forEach((fieldName) => {
        // Try different field name patterns to match the actual field in the form
        const fieldSelectors = [
          `[data-fieldname$="form.widgets.${fieldName}"]`,
          `[data-fieldname$="form.widgets.I${fieldName}"]`,
          `[data-fieldname*="${fieldName}"]`,
          `#formfield-form-widgets-${fieldName}`,
          `#formfield-form-widgets-I${fieldName}`,
        ];

        for (const selector of fieldSelectors) {
          const fieldElement = document.querySelector(selector);
          if (fieldElement) {
            const fieldContainer = fieldElement.closest(".field");
            if (fieldContainer) {
              fieldContainer.style.display = "";
              break; // Found and showed the field, no need to check other selectors
            }
          }
        }
      });
    } else if (selectedRowType === "horizontal-row-type") {
      // If no config but we're on the default type, show all fields
      allFields.forEach((field) => {
        field.style.display = "";
      });
    }
  }

  // Initialize when DOM is fully loaded
  function start() {
    initialize();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
