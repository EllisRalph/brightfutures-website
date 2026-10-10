/* Bright Futures Recruitment — site behaviour */
(function () {
  "use strict";

  /* ---------- header shadow + compact logo on scroll ---------- */
  var header = document.querySelector(".site-header");
  function onScroll() {
    if (header) header.classList.toggle("scrolled", window.scrollY > 40);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* ---------- mobile drawer ---------- */
  var drawer = document.getElementById("drawer");
  var toggle = document.querySelector(".nav-toggle");
  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", open ? "false" : "true");
    document.body.classList.toggle("no-scroll", open);
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      var first = drawer.querySelector(".drawer-close");
      if (first) first.focus();
    } else if (toggle) {
      toggle.focus();
    }
  }
  if (toggle) toggle.addEventListener("click", function () { setDrawer(true); });
  if (drawer) {
    drawer.querySelector(".drawer-close").addEventListener("click", function () { setDrawer(false); });
    drawer.addEventListener("click", function (ev) {
      if (ev.target.closest("a")) setDrawer(false);
    });
  }
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && drawer && drawer.classList.contains("open")) setDrawer(false);
  });

  /* ---------- reveal on scroll ---------- */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add("in");
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- file inputs: show the chosen file name ---------- */
  document.querySelectorAll(".file-drop input[type=file]").forEach(function (input) {
    var drop = input.closest(".file-drop");
    var label = drop.querySelector("[data-file-label]");
    var original = label ? label.textContent : "";
    input.addEventListener("change", function () {
      var f = input.files && input.files[0];
      if (!label) return;
      if (f) {
        var tooBig = f.size > 8 * 1024 * 1024;
        label.textContent = tooBig ? "That file is over 8MB, please choose a smaller one" : f.name;
        input.setCustomValidity(tooBig ? "Please choose a file under 8MB" : "");
      } else {
        label.textContent = original;
      }
    });
    ["dragenter", "dragover"].forEach(function (t) { drop.addEventListener(t, function () { drop.classList.add("drag"); }); });
    ["dragleave", "drop"].forEach(function (t) { drop.addEventListener(t, function () { drop.classList.remove("drag"); }); });
  });

  /* ---------- opening hours: highlight today ---------- */
  var hours = document.querySelector("[data-hours]");
  if (hours) {
    var row = hours.querySelector('tr[data-day="' + new Date().getDay() + '"]');
    if (row) row.classList.add("today");
  }

  /* ---------- closing dates: hide or flag vacancies that closed since the last rebuild ---------- */
  var today = new Date();
  var todayIso = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, "0") + "-" + String(today.getDate()).padStart(2, "0");
  function hasClosed(el) { return el.dataset.closing && el.dataset.closing < todayIso; }
  document.querySelectorAll(".job-card[data-closing]").forEach(function (card) {
    if (hasClosed(card)) { card.hidden = true; card.dataset.closed = "1"; }
  });
  var closedNote = document.querySelector(".closed-note[data-closing]");
  if (closedNote && hasClosed(closedNote)) {
    closedNote.hidden = false;
    var apply = document.getElementById("apply");
    if (apply) apply.querySelector(".apply-card").hidden = true;
  }

  /* ---------- job pages: sticky Apply bar on small screens ---------- */
  var applyBar = document.querySelector(".apply-bar");
  var applyCard = document.querySelector("#apply .apply-card");
  var heroCta = document.querySelector(".job-hero-cta");
  if (applyBar && applyCard && "IntersectionObserver" in window) {
    var seen = { hero: true, form: false };
    var update = function () {
      var show = !seen.hero && !seen.form && !applyCard.hidden;
      applyBar.classList.toggle("show", show);
      applyBar.setAttribute("aria-hidden", show ? "false" : "true");
      applyBar.querySelectorAll("a").forEach(function (a) { a.tabIndex = show ? 0 : -1; });
    };
    new IntersectionObserver(function (es) { es.forEach(function (en) { seen.form = en.isIntersecting; }); update(); }).observe(document.getElementById("apply"));
    if (heroCta) new IntersectionObserver(function (es) { es.forEach(function (en) { seen.hero = en.isIntersecting; }); update(); }).observe(heroCta);
  }

  /* ---------- jobs board ---------- */
  var form = document.getElementById("job-filters");
  var board = document.getElementById("job-board");
  if (form && board) {
    var cards = Array.prototype.slice.call(board.querySelectorAll(".job-card")).filter(function (c) { return !c.dataset.closed; });
    var chips = Array.prototype.slice.call(form.querySelectorAll(".chip"));
    var q = form.elements.q;
    var area = form.elements.area;
    var type = form.elements.type;
    var countEl = document.querySelector("[data-count]");
    var countLabel = document.querySelector("[data-count-label]");
    var empty = document.getElementById("no-results");
    var state = { q: "", cat: "", area: "", type: "" };

    function readParams() {
      var p = new URLSearchParams(window.location.search);
      state.q = p.get("q") || "";
      state.cat = p.get("cat") || "";
      state.area = p.get("area") || "";
      state.type = p.get("type") || "";
      q.value = state.q;
      area.value = state.area;
      type.value = state.type;
      if (area.value !== state.area) state.area = "";
      if (type.value !== state.type) state.type = "";
    }

    function writeParams() {
      var p = new URLSearchParams();
      Object.keys(state).forEach(function (k) { if (state[k]) p.set(k, state[k]); });
      var qs = p.toString();
      history.replaceState(null, "", window.location.pathname + (qs ? "?" + qs : ""));
    }

    function apply() {
      var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      var shown = 0;
      cards.forEach(function (card) {
        var ok = (!state.cat || card.dataset.cat === state.cat) &&
                 (!state.area || card.dataset.area === state.area) &&
                 (!state.type || card.dataset.type === state.type) &&
                 terms.every(function (t) { return card.dataset.text.indexOf(t) !== -1; });
        card.hidden = !ok;
        if (ok) shown++;
      });
      chips.forEach(function (c) { c.setAttribute("aria-pressed", c.dataset.cat === state.cat ? "true" : "false"); });
      if (countEl) countEl.textContent = shown;
      if (countLabel) countLabel.textContent = shown === 1 ? "role" : "roles";
      if (empty) empty.classList.toggle("show", shown === 0);
    }

    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        state.cat = c.dataset.cat;
        apply();
        writeParams();
      });
    });
    var t;
    q.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () { state.q = q.value.trim(); apply(); writeParams(); }, 120);
    });
    area.addEventListener("change", function () { state.area = area.value; apply(); writeParams(); });
    type.addEventListener("change", function () { state.type = type.value; apply(); writeParams(); });
    document.querySelectorAll("[data-reset]").forEach(function (b) {
      b.addEventListener("click", function () {
        state = { q: "", cat: "", area: "", type: "" };
        q.value = ""; area.value = ""; type.value = "";
        apply();
        writeParams();
      });
    });

    readParams();
    apply();
    var active = form.querySelector('.chip[aria-pressed="true"]');
    if (active && active.scrollIntoView && state.cat) active.scrollIntoView({ block: "nearest", inline: "center" });
  }
})();
