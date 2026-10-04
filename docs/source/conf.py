# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Custom2kinter"
copyright = "2026, Federico Spada"
author = "Federico Spada"
version = "5.3.0"
release = "5.3.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx.ext.extlinks"
]
templates_path = ["_templates"]
exclude_patterns = [
    "arguments",
    "methods",
    "definitions.rst"
]

toc_object_entries_show_parents = "hide"
rst_epilog = """
.. include:: /definitions.rst
"""

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = "Custom2kinter"
html_theme = "furo"
html_theme_options = {
    "sidebar_hide_name": True,
    "light_logo": "CustomTkinter_logo_light.png",
    "dark_logo": "CustomTkinter_logo_dark.png",
    "footer_icons": [
        {
            "name": "LinkedIn",
            "url": "https://www.linkedin.com/in/federicospada13",
            "html": """
                <svg fill="currentColor" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                    <path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z"/>
                </svg>
            """,
            "class": "",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/custom2kinter",
            "html": """
                <svg fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/>
                </svg>
            """,
            "class": "",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/FedericoSpada/Custom2kinter",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}
html_scaled_image_link = False
html_static_path = ["_static"]
html_css_files = [
    "custom.css",
    "toc-collapse.css"
]
html_js_files = [
    "toc-collapse.js",
    "param-linebreak.js"
]

# -- Options for extlinks ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

extlinks = {
    "tkdoc": ("https://tkdocs.com/shipman/%s.html", None),
    "tcldoc": ("https://www.tcl-lang.org/man/tcl8.6/TkCmd/%s.htm", None),
    "examples": ("https://github.com/FedericoSpada/Custom2kinter/blob/master/examples/%s_example.py", None),
}

# -- Setup -------------------------------------------------------------------

def setup(app) -> None:
    from sphinx import addnodes
    from sphinx.domains.python import PyClasslike
    from docutils.parsers.rst import directives
    from docutils import nodes

    #Add flag ":hidden:" to python classes
    class HiddenClassDirective(PyClasslike):
        option_spec = {**PyClasslike.option_spec, "hidden": directives.flag}

        def run(self) -> None:
            if "hidden" not in self.options:
                return super().run()

            self.options["no-contents-entry"] = None
            result = super().run()
            for node in result:
                if isinstance(node, addnodes.desc):
                    node["classes"].append("hidden-class")
            return result

    #Move sections out of hidden classes so they appear in the TOC
    def hoist_hidden_class_sections(_app, doctree) -> None:
        for description in list(doctree.findall(addnodes.desc)):
            if "hidden-class" not in description.get("classes", ()):
                continue

            parent = description.parent
            content = next((child
                            for child in description.children
                            if isinstance(child, addnodes.desc_content)), None)
            if parent is None or content is None:
                continue

            sections = [child
                        for child in content.children
                        if isinstance(child, nodes.section)]
            # Place them as siblings of the section that contains the class
            if isinstance(parent, nodes.section) and isinstance(parent.parent, nodes.section):
                anchor, parent = parent, parent.parent
            else:
                anchor = description
            index = parent.index(anchor) + 1
            for section in sections:
                content.remove(section)
                parent.insert(index, section)
                index += 1

    #Add the hidden class to "attr" and "meth" references without an explicit class
    def qualify_page_attribute_references(_app, doctree) -> None:
        hidden_classes = {
            (signature.get("module"), signature["fullname"])
            for description in doctree.findall(addnodes.desc)
            if (
                description.get("domain") == "py" and
                description.get("objtype") == "class" and
                "hidden-class" in description.get("classes", ())
            )
            for signature in description.children
            if isinstance(signature, addnodes.desc_signature) and "fullname" in signature
        }

        if len(hidden_classes) == 1:
            module_name, class_name = hidden_classes.pop()

            for reference in doctree.findall(addnodes.pending_xref):
                if (reference.get("refdomain") == "py" and
                    reference.get("reftype") in ["attr", "meth"] and
                    not reference.get("py:class") and
                    "." not in reference["reftarget"]):

                    reference["reftarget"] = ".".join(
                        part for part in (module_name, class_name, reference["reftarget"]) if part
                    )

    app.add_directive_to_domain("py", "class", HiddenClassDirective, override=True)
    app.connect("doctree-read", hoist_hidden_class_sections, priority=400)
    app.connect("doctree-read", qualify_page_attribute_references)
