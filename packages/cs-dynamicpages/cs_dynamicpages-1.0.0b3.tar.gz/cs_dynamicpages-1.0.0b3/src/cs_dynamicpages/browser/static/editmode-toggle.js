/**
 * Handles the edit mode toggle functionality for dynamic pages.
 * Toggles between edit and preview modes and saves the preference in localStorage.
 */

document.addEventListener("DOMContentLoaded", function () {
  // Only run if both required classes are present on the body
  if (
    !document.body.classList.contains("template-dynamic-view") ||
    !document.body.classList.contains("userrole-manager")
  ) {
    return;
  }

  // Add preview-mode class by default on page load
  // document.body.classList.add("preview-mode");

  const toggle = document.getElementById("editModeToggle");
  if (toggle) {
    toggle.addEventListener("change", function () {
      if (this.checked) {
        document.body.classList.remove("preview-mode");
      } else {
        document.body.classList.add("preview-mode");
      }
    });
  }
});
