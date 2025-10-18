/**
 * Handles deletion of dynamic page rows
 */

(function () {
  "use strict";

  // Initialize when DOM is loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRowDeletion);
  } else {
    initRowDeletion();
  }

  function initRowDeletion() {
    // Only run on dynamic-view with edit permissions
    if (
      !document.body.classList.contains("template-dynamic-view") ||
      !document.body.classList.contains("userrole-manager")
    ) {
      return;
    }

    const deleteModal = document.getElementById("deleteElementModal");
    if (!deleteModal) {
      // Delete element modal not found
      return;
    }

    let rowToDelete = null;

    deleteModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      // Get the closest parent element with data-delete-target="true"
      rowToDelete = button.closest('[data-delete-target="true"]');
      if (!rowToDelete) {
        // No deletable element found
        return;
      }
    });

    // Store the deletion context for modal confirmation
    let deletionContext = null;
    const modal = document.getElementById("deleteElementModal");

    // Handle delete button click
    document.addEventListener("click", function (event) {
      const deleteButton = event.target.closest(".btn-delete-element");
      if (deleteButton) {
        event.preventDefault();
        const elementToDelete = deleteButton.closest(
          '[data-delete-target="true"]'
        );
        if (elementToDelete) {
          // Store the deletion context for when modal is confirmed
          deletionContext = {
            elementId: elementToDelete.dataset.elementid,
            element: elementToDelete,
          };
          // The modal will be shown by Bootstrap's data-bs-toggle="modal"
        }
      }
    });

    // Handle modal confirm button click
    if (modal) {
      modal.addEventListener("show.bs.modal", function (event) {
        const button = event.relatedTarget;
        // Update the modal content if needed
        const modalTitle = modal.querySelector(".modal-title");
        if (modalTitle) {
          modalTitle.textContent = "Confirm Deletion";
        }
      });

      const confirmButton = document.getElementById("confirmDeleteElement");
      if (confirmButton) {
        confirmButton.addEventListener("click", function () {
          if (deletionContext) {
            deleteRow(deletionContext.elementId, deletionContext.element);
            // Close the modal
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
              modalInstance.hide();
            }
          }
        });
      } else {
        // Confirm button not found
      }
    }

    function deleteRow(elementId, elementToDelete) {
      const elementUrl = elementToDelete.dataset.elementurl;

      fetch(elementUrl, {
        method: "DELETE",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRF-TOKEN":
            document.querySelector('input[name="_authenticator"]')?.value || "",
        },
        credentials: "same-origin",
      })
        .then((response) => {
          if (!response.ok) {
            const error = new Error(`HTTP error! status: ${response.status}`);
            throw error;
          }
        })
        .finally(() => {
          const modal = bootstrap.Modal.getInstance(deleteModal);
          if (modal) {
            modal.hide();
          }
          sessionStorage.setItem('toast-message', 'Element deleted successfully.');
          // Refresh the page after successful update
          window.location.reload();
        });
    }
  }
})();
