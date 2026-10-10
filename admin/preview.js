/* Makes the editor's live preview look like the real vacancy page. */
(function () {
  if (!window.CMS) return;
  CMS.registerPreviewStyle("/assets/css/site.css");
  CMS.registerPreviewStyle("https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600&family=Atkinson+Hyperlegible+Next:wght@400;700&display=swap");
  CMS.registerPreviewStyle("body{padding:28px;background:#fef8e8} .job-content ul.preview-facts{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 28px} .job-content ul.preview-facts li{background:#fff;border:1px solid rgba(2,69,80,.13);border-radius:999px;padding:7px 13px;font-size:.9rem} .job-content ul.preview-facts li::before{display:none} .preview-hidden{background:#fde8e4;color:#7a2617;padding:10px 14px;border-radius:12px;margin-bottom:18px;display:inline-block}", { raw: true });

  var labels = {
    "primary": "Primary", "secondary": "Secondary", "send": "SEND", "semh": "SEMH",
    "cover-supervisors": "Cover supervisors", "teaching-assistants": "Teaching assistants",
    "lsa": "Learning support assistants", "residential": "Residential children's homes",
    "therapy": "Therapy", "other-school-roles": "Other school roles"
  };

  var JobPreview = createClass({
    render: function () {
      var d = this.props.entry.get("data");
      var get = function (k) { return d.get(k) || ""; };
      var facts = [get("location"), get("type"), get("hours"), get("start") && "Start: " + get("start"), get("pay")]
        .filter(Boolean).map(function (f, i) { return h("li", { key: i }, f); });
      return h("div", { className: "job-content" },
        d.get("live") === false ? h("p", { className: "preview-hidden" }, "Hidden: this vacancy won't show on the website") : null,
        h("span", { className: "tag-cat" }, labels[get("category")] || ""),
        h("h1", { style: { fontSize: "2.2rem", margin: "14px 0 10px" } }, get("title") || "Job title"),
        h("p", { className: "lead" }, get("summary")),
        h("ul", { className: "preview-facts" }, facts),
        h("section", {}, this.props.widgetFor("body"))
      );
    }
  });
  CMS.registerPreviewTemplate("jobs", JobPreview);

  var TestimonialPreview = createClass({
    render: function () {
      var d = this.props.entry.get("data");
      return h("figure", { className: "review", style: { maxWidth: "560px" } },
        h("blockquote", {}, "“" + (d.get("quote") || "") + "”"),
        h("figcaption", {}, h("b", {}, d.get("name") || "Name"), d.get("who") ? ", " + d.get("who") : ""));
    }
  });
  CMS.registerPreviewTemplate("testimonials", TestimonialPreview);
})();
