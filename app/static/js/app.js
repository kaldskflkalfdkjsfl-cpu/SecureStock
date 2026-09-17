// SecureStock — small progressive-enhancement helpers.
// Kept in an external file so pages work under a strict Content-Security-Policy
// (no inline event handlers such as onclick="...").
document.addEventListener("submit", function (event) {
  var form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  var message = form.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});
