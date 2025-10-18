(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const toastMessage = sessionStorage.getItem("toast-message");

    if (toastMessage) {
      const toastLiveExample = document.getElementById("liveToast");
      if (toastLiveExample) {
        const toastBody = toastLiveExample.querySelector(".toast-body");
        if (toastBody) {
          toastBody.textContent = toastMessage;
        }

        const toast = new bootstrap.Toast(toastLiveExample);
        toast.show();
      }

      // Clear the message from session storage
      sessionStorage.removeItem("toast-message");
    }
  });
})();
