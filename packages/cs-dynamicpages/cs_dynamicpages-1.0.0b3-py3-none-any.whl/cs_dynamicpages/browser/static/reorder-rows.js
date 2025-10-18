/**
 * Handles reordering of dynamic page rows
 */

(function () {
  "use strict";

  // Initialize when DOM is loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRowReordering);
  } else {
    initRowReordering();
  }

  function initRowReordering() {
    // Only run on dynamic-view with edit permissions
    if (
      !document.body.classList.contains("template-dynamic-view") ||
      !document.body.classList.contains("userrole-manager")
    ) {
      return;
    }

    // Find all move up/down buttons
    const moveUpButtons = document.querySelectorAll('a[data-action="move-up"]');
    const moveDownButtons = document.querySelectorAll(
      'a[data-action="move-down"]'
    );

    // Add event listeners to move up buttons
    moveUpButtons.forEach((button) => {
      button.addEventListener(
        "click",
        function (e) {
          e.preventDefault();
          e.stopPropagation(); // Detener la propagación del evento

          // Deshabilitar el botón temporalmente
          if (this.disabled) return;
          this.disabled = true;

          const element = this.closest('[data-move-target="true"]');

          // Re-habilitar el botón después de un tiempo
          setTimeout(() => {
            this.disabled = false;
          }, 2000);

          moveElement(element, -1);
        },
        { once: true }
      ); // Usar { once: true } para que el listener se ejecute solo una vez
    });

    // Add event listeners to move down buttons
    moveDownButtons.forEach((button) => {
      button.addEventListener(
        "click",
        function (e) {
          e.preventDefault();
          e.stopPropagation(); // Detener la propagación del evento

          // Deshabilitar el botón temporalmente
          if (this.disabled) return;
          this.disabled = true;

          const element = this.closest('[data-move-target="true"]');

          // Re-habilitar el botón después de un tiempo
          setTimeout(() => {
            this.disabled = false;
          }, 2000);

          moveElement(element, 1);
        },
        { once: true }
      ); // Usar { once: true } para que el listener se ejecute solo una vez
    });
  }

  function moveElement(element, delta) {
    const elementId = element.dataset.elementid;
    if (!elementId) {
      const errorMsg = "No data-element-id attribute found on element";
      alert(errorMsg);
      return;
    }


    const baseUrl = element.dataset.parenturl || "";

    const requestBody = {
      ordering: {
        obj_id: elementId,
        delta: delta,
      },
    };


    fetch(baseUrl, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify(requestBody),
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          const error = new Error(`HTTP error! status: ${response.status}`);
          throw error;
        }
      })
      .finally(() => {
        sessionStorage.setItem('toast-message', 'Element reordered successfully.');
        // Refresh the page after successful update
        window.location.reload();
      });
  }
})();
