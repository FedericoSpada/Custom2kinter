// Collapsible right-hand TOC with configurable depth,
// leveraging the events Furo/Gumshoe already emits.
(function () {
   // How many heading levels remain ALWAYS visible.
   // Deeper levels open only while you are reading them.
   var SHOW_TOC_DEPTH = 1;

   function markCollapsible(tree) {
      tree.querySelectorAll("ul").forEach(function (ul) {
         var depth = 0;
         var parent = ul.parentElement;
         while (parent && parent !== tree) {
         if (parent.tagName === "UL") depth++;
         parent = parent.parentElement;
         }
         ul.classList.toggle("toc-collapsible", depth > SHOW_TOC_DEPTH);
      });
   }

   function updateBranch() {
      var tree = document.querySelector(".toc-tree");
      if (!tree) return;

      tree.querySelectorAll("li.toc-branch-current").forEach(function (li) {
         li.classList.remove("toc-branch-current");
      });

      var node = tree.querySelector(".scroll-current");
      while (node && node !== tree) {
         if (node.tagName === "LI") {
         node.classList.add("toc-branch-current");
         }
         node = node.parentElement;
      }
   }

   function init() {
      var tree = document.querySelector(".toc-tree");
      if (!tree) return;
      markCollapsible(tree);
      updateBranch();
   }

   document.addEventListener("gumshoeActivate", updateBranch);
   document.addEventListener("DOMContentLoaded", init);
})();
