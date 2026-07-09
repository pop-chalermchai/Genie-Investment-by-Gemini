/*
 * GenieAuth — Supabase Auth (email/password) for the Genie Investment app.
 *
 * Design notes:
 *  - Uses the Supabase Auth (GoTrue) REST API directly — no bundled library, to
 *    keep the app's "vanilla JS, no build step" architecture.
 *  - SUPABASE_URL and SUPABASE_ANON_KEY are PUBLIC values (the anon key is a
 *    JWT designed to ship in the browser; it is safe here and protected by RLS).
 *  - window.fetch is patched once so every /api/* request carries the user's
 *    access token automatically — the 42 existing fetch() call sites are untouched.
 *  - Signup is invite-only: users are created in the Supabase Dashboard. This
 *    screen only signs existing users IN.
 */
(function () {
  "use strict";

  var SUPABASE_URL = "https://jkndlurskolcmifmsctm.supabase.co";
  var SUPABASE_ANON_KEY =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImprbmRsdXJza29sY21pZm1zY3RtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEyNzEyNjUsImV4cCI6MjA5Njg0NzI2NX0.lfgMZNRAIFpy4Bn0LEOOO8O1BWUGu1hwEtJL2FDg8Ik";

  var STORAGE_KEY = "genie-session";
  var AUTH_BASE = SUPABASE_URL + "/auth/v1";
  var AUTH_CONFIG_URL = "/api/auth-config";

  // Whether the backend enforces auth. Determined at startup from the backend
  // (source of truth) rather than guessed from the hostname — running locally
  // against the production DB still requires login. Safe default: true.
  var authRequired = true;
  var _configPromise = null;

  function loadAuthConfig() {
    if (_configPromise) return _configPromise;
    _configPromise = _origFetch(AUTH_CONFIG_URL)
      .then(function (r) { return r.json(); })
      .then(function (cfg) { authRequired = !!cfg.authRequired; return authRequired; })
      .catch(function () { authRequired = true; return true; }); // fail closed
    return _configPromise;
  }

  // ── Session storage ─────────────────────────────────────────────────────────
  function loadSession() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    } catch (e) {
      return null;
    }
  }
  function saveSession(s) {
    // GoTrue returns expires_in (seconds); track an absolute expiry.
    if (s && s.expires_in && !s.expires_at) {
      s.expires_at = Math.floor(Date.now() / 1000) + s.expires_in;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  }
  function clearSession() {
    localStorage.removeItem(STORAGE_KEY);
  }

  function isExpired(s, skewSeconds) {
    if (!s || !s.expires_at) return true;
    return Math.floor(Date.now() / 1000) >= s.expires_at - (skewSeconds || 60);
  }

  function hasSession() {
    var s = loadSession();
    return !!(s && s.access_token);
  }

  // Called by app.js before it loads data. Resolves true if the app may proceed;
  // otherwise shows the login screen and resolves false.
  function ensureAllowed() {
    return loadAuthConfig().then(function (required) {
      if (!required) return true;
      if (hasSession()) return true;
      showLogin();
      return false;
    });
  }

  // ── Token lifecycle ─────────────────────────────────────────────────────────
  function refresh() {
    var s = loadSession();
    if (!s || !s.refresh_token) return Promise.reject(new Error("no refresh token"));
    return fetch(AUTH_BASE + "/token?grant_type=refresh_token", {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: SUPABASE_ANON_KEY },
      body: JSON.stringify({ refresh_token: s.refresh_token }),
    }).then(function (r) {
      if (!r.ok) throw new Error("refresh failed");
      return r.json();
    }).then(function (data) {
      saveSession(data);
      return data.access_token;
    });
  }

  // Returns a valid access token, refreshing if near expiry. Rejects if none.
  function freshToken() {
    var s = loadSession();
    if (!s || !s.access_token) return Promise.reject(new Error("no session"));
    if (isExpired(s, 60)) return refresh();
    return Promise.resolve(s.access_token);
  }

  function login(email, password) {
    return fetch(AUTH_BASE + "/token?grant_type=password", {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: SUPABASE_ANON_KEY },
      body: JSON.stringify({ email: email, password: password }),
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) {
          throw new Error(data.error_description || data.msg || data.error || "Login failed");
        }
        return data;
      });
    }).then(function (data) {
      saveSession(data);
      return data;
    });
  }

  // Self-service signup. With email confirmation ON, GoTrue returns the bare
  // user (no session) and sends a confirmation link; with confirmation OFF it
  // returns a full session like login. Both shapes are handled by the caller.
  function signup(email, password, displayName) {
    return fetch(AUTH_BASE + "/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: SUPABASE_ANON_KEY },
      body: JSON.stringify({
        email: email,
        password: password,
        data: { display_name: displayName || "" },
      }),
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) {
          throw new Error(data.error_description || data.msg || data.error || "Signup failed");
        }
        return data;
      });
    });
  }

  // Display name typed at signup is applied to the profile after the first
  // successful login (the profile row is created server-side on first access).
  var PENDING_NAME_KEY = "genie-pending-display-name";

  function applyPendingDisplayName() {
    var name = localStorage.getItem(PENDING_NAME_KEY);
    if (!name) return Promise.resolve();
    return fetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ display_name: name }),
    }).then(function (r) {
      if (r.ok) localStorage.removeItem(PENDING_NAME_KEY);
    }).catch(function () {});
  }

  function logout() {
    var s = loadSession();
    clearSession();
    // Best-effort server-side revoke; ignore result.
    if (s && s.access_token) {
      fetch(AUTH_BASE + "/logout", {
        method: "POST",
        headers: {
          apikey: SUPABASE_ANON_KEY,
          Authorization: "Bearer " + s.access_token,
        },
      }).catch(function () {});
    }
    window.location.reload();
  }

  // ── fetch() interception ────────────────────────────────────────────────────
  var _origFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    var url = typeof input === "string" ? input : (input && input.url) || "";
    var isApi = url.indexOf("/api/") !== -1 && url.indexOf(SUPABASE_URL) === -1;
    var isAuthConfig = url.indexOf(AUTH_CONFIG_URL) !== -1;
    // Don't intercept non-API calls, the public auth-config probe, or when the
    // backend isn't enforcing auth (pure local dev).
    if (!isApi || isAuthConfig || !authRequired) return _origFetch(input, init);

    return freshToken().then(
      function (token) {
        init = init || {};
        var headers = new Headers(init.headers || (typeof input !== "string" ? input.headers : undefined) || {});
        headers.set("Authorization", "Bearer " + token);
        init.headers = headers;
        return _origFetch(input, init).then(function (resp) {
          if (resp.status === 401) {
            clearSession();
            showLogin();
          }
          return resp;
        });
      },
      function () {
        // No valid session — surface a 401-like response and prompt login.
        showLogin();
        return new Response(JSON.stringify({ error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        });
      }
    );
  };

  // ── Login / Signup overlay UI ───────────────────────────────────────────────
  function showLogin() {
    if (document.getElementById("genie-auth-overlay")) return;
    var overlay = document.createElement("div");
    overlay.id = "genie-auth-overlay";
    overlay.innerHTML =
      '<div class="genie-auth-card">' +
      '  <img src="./assets/Genie.png?v=2" alt="Genie" class="genie-auth-logo" onerror="this.style.display=\'none\'"/>' +
      '  <h2>Genie Investment</h2>' +
      '  <p class="genie-auth-sub" id="genie-auth-sub">Sign in to continue</p>' +
      '  <form id="genie-auth-form">' +
      '    <input id="genie-auth-name" type="text" placeholder="Display name" autocomplete="name" maxlength="60" style="display:none;" />' +
      '    <input id="genie-auth-email" type="email" placeholder="Email" autocomplete="username" required />' +
      '    <input id="genie-auth-pass" type="password" placeholder="Password" autocomplete="current-password" required minlength="6" />' +
      '    <input id="genie-auth-pass2" type="password" placeholder="Confirm password" autocomplete="new-password" minlength="6" style="display:none;" />' +
      '    <button type="submit" id="genie-auth-btn">Sign in</button>' +
      '    <div id="genie-auth-err" class="genie-auth-err"></div>' +
      "  </form>" +
      '  <div id="genie-auth-success" style="display:none;">' +
      '    <p class="genie-auth-success-msg">🎉 Account created!<br>Check your email for a confirmation link, then come back and sign in.</p>' +
      '    <button type="button" id="genie-auth-back-btn">← Back to sign in</button>' +
      "  </div>" +
      '  <p class="genie-auth-note"><a href="#" id="genie-auth-toggle">New here? Create an account →</a></p>' +
      "</div>";
    document.body.appendChild(overlay);

    var style = document.createElement("style");
    style.textContent =
      "#genie-auth-overlay{position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;" +
      "background:rgba(10,12,20,.92);backdrop-filter:blur(6px);font-family:inherit;}" +
      ".genie-auth-card{background:#151823;border:1px solid #262b3d;border-radius:16px;padding:32px 28px;width:min(360px,90vw);" +
      "box-shadow:0 20px 60px rgba(0,0,0,.5);text-align:center;color:#e8eaf0;}" +
      ".genie-auth-logo{width:56px;height:56px;border-radius:12px;object-fit:cover;margin-bottom:10px;}" +
      ".genie-auth-card h2{margin:0 0 2px;font-size:1.25rem;}" +
      ".genie-auth-sub{margin:0 0 20px;color:#8b90a3;font-size:.9rem;}" +
      ".genie-auth-card input{width:100%;box-sizing:border-box;margin-bottom:12px;padding:12px 14px;border-radius:10px;" +
      "border:1px solid #2d3346;background:#0e1119;color:#e8eaf0;font-size:.95rem;}" +
      ".genie-auth-card input:focus{outline:none;border-color:#5b8cff;}" +
      "#genie-auth-btn{width:100%;padding:12px;border:0;border-radius:10px;background:#5b8cff;color:#fff;font-weight:600;" +
      "font-size:.95rem;cursor:pointer;margin-top:4px;}" +
      "#genie-auth-btn:disabled{opacity:.6;cursor:default;}" +
      ".genie-auth-err{color:#ff6b6b;font-size:.82rem;min-height:18px;margin-top:10px;}" +
      ".genie-auth-note{color:#6b7186;font-size:.75rem;margin:18px 0 0;}" +
      ".genie-auth-note a{color:#5b8cff;text-decoration:none;}" +
      ".genie-auth-success-msg{color:#7ee2a8;font-size:.9rem;line-height:1.6;margin:8px 0 16px;}" +
      "#genie-auth-back-btn{width:100%;padding:12px;border:1px solid #2d3346;border-radius:10px;background:#0e1119;" +
      "color:#e8eaf0;font-size:.9rem;cursor:pointer;}";
    document.head.appendChild(style);

    var mode = "signin"; // 'signin' | 'signup'
    var form = document.getElementById("genie-auth-form");
    var btn = document.getElementById("genie-auth-btn");
    var err = document.getElementById("genie-auth-err");
    var sub = document.getElementById("genie-auth-sub");
    var nameEl = document.getElementById("genie-auth-name");
    var passEl = document.getElementById("genie-auth-pass");
    var pass2El = document.getElementById("genie-auth-pass2");
    var toggle = document.getElementById("genie-auth-toggle");
    var successEl = document.getElementById("genie-auth-success");

    function setMode(m) {
      mode = m;
      err.textContent = "";
      form.style.display = "";
      successEl.style.display = "none";
      var isUp = m === "signup";
      nameEl.style.display = isUp ? "" : "none";
      pass2El.style.display = isUp ? "" : "none";
      pass2El.required = isUp;
      passEl.setAttribute("autocomplete", isUp ? "new-password" : "current-password");
      sub.textContent = isUp ? "Create your account" : "Sign in to continue";
      btn.textContent = isUp ? "Create account" : "Sign in";
      toggle.textContent = isUp ? "← Already have an account? Sign in" : "New here? Create an account →";
    }

    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      setMode(mode === "signin" ? "signup" : "signin");
    });

    document.getElementById("genie-auth-back-btn").addEventListener("click", function () {
      setMode("signin");
    });

    function doSignin(email, pass) {
      btn.textContent = "Signing in…";
      return login(email, pass).then(function () {
        // Apply the display name captured at signup (if any), then enter the app.
        return applyPendingDisplayName().finally(function () {
          window.location.reload();
        });
      });
    }

    function doSignup(email, pass) {
      if (pass !== pass2El.value) {
        return Promise.reject(new Error("Passwords do not match"));
      }
      var displayName = nameEl.value.trim();
      if (displayName) localStorage.setItem(PENDING_NAME_KEY, displayName);
      btn.textContent = "Creating account…";
      return signup(email, pass, displayName).then(function (data) {
        var user = data.user || (data.id ? data : null);
        // GoTrue masks duplicate emails as a "success" with no identities.
        if (user && user.identities && user.identities.length === 0) {
          throw new Error("This email is already registered — try signing in.");
        }
        if (data.access_token) {
          // Email confirmation is disabled — we already have a session.
          saveSession(data);
          return applyPendingDisplayName().finally(function () {
            window.location.reload();
          });
        }
        // Confirmation email sent — show the success panel.
        form.style.display = "none";
        successEl.style.display = "";
      });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      err.textContent = "";
      btn.disabled = true;
      var email = document.getElementById("genie-auth-email").value.trim();
      var pass = passEl.value;
      var run = mode === "signup" ? doSignup(email, pass) : doSignin(email, pass);
      run.catch(function (ex) {
        err.textContent = ex.message || (mode === "signup" ? "Signup failed" : "Login failed");
        btn.disabled = false;
        btn.textContent = mode === "signup" ? "Create account" : "Sign in";
      });
    });
  }

  // Public API used by index.html / app.js.
  window.GenieAuth = {
    hasSession: hasSession,
    ensureAllowed: ensureAllowed,
    showLogin: showLogin,
    logout: logout,
    freshToken: freshToken,
  };
})();
