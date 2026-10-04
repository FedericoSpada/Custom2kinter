// Normalizes the parameter descriptions of py: directives (:param:).
//
// Sphinx separates "name (type)" from the description with a dash (en-dash) and,
// with a single paragraph, keeps the description on the same line as the name
// (inline text node), whereas with 2+ paragraphs it moves it to a <p>.
// Here we remove the dash and, only in the single-paragraph case, move the
// description into its own <p>, so the layout is always identical.
(function () {
  "use strict";

  var EN_DASH = "\u2013"; // separator used by Sphinx between signature and description

  function normalizeParams() {
    var sigs = document.querySelectorAll(
      "dl.field-list > dd > ul.simple > li > p, dl.field-list > dd > p"
    );

    sigs.forEach(function (p) {
      // Must be a parameter line: it starts with <strong>name</strong>.
      var first = p.firstElementChild;
      if (!first || first.tagName !== "STRONG") return;

      // The separator is the text node (in the signature) containing the en-dash.
      var sep = null;
      for (var i = 0; i < p.childNodes.length; i++) {
        var n = p.childNodes[i];
        if (n.nodeType === Node.TEXT_NODE && n.nodeValue.indexOf(EN_DASH) !== -1) {
          sep = n;
          break;
        }
      }
      if (!sep) return; // parameter without description: nothing to do

      var idx = sep.nodeValue.indexOf(EN_DASH);
      var before = sep.nodeValue.slice(0, idx).replace(/\s+$/, ""); // signature without dash
      var after = sep.nodeValue.slice(idx + 1).replace(/^\s+/, ""); // inline description (single case)

      sep.nodeValue = before;

      // Single-paragraph case: the description is inline after the dash. It may
      // span several nodes (e.g. inline code), so move the leftover text plus
      // every following sibling into a separate <p> right after the signature,
      // matching the multi-paragraph structure (title in one <p>, body in another).
      var desc = document.createElement("p");
      if (after) desc.appendChild(document.createTextNode(after));
      var node = sep.nextSibling;
      while (node) {
        var next = node.nextSibling;
        desc.appendChild(node);
        node = next;
      }
      if (desc.childNodes.length) {
        p.parentNode.insertBefore(desc, p.nextSibling);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", normalizeParams);
  } else {
    normalizeParams();
  }
})();
