// Attach the CSRF token from <meta> or hidden input to all fetch requests.
(function () {
  const meta = document.querySelector('meta[name="csrf-token"]');
  const hidden = document.querySelector('input[name="csrf_token"]');
  const token = (meta && meta.content) || (hidden && hidden.value) || "";

  if (token && window.fetch) {
    const orig = window.fetch;
    window.fetch = function (input, init) {
      init = init || {};
      init.headers = init.headers || {};
      if (init.headers instanceof Headers) {
        init.headers.set("X-CSRF-Token", token);
      } else {
        init.headers["X-CSRF-Token"] = token;
      }
      return orig.call(window, input, init);
    };
  }
})();