"""
html.py — HTML nodes, Element base class, and dynamic HTML5 element classes.
"""

from __future__ import annotations

import html as _html
from typing import Any, Dict, List, Optional, Union

from .utils import (
    HAS_JS,
    _BuildStacks,
    _document,
    _hyphenate,
    _normalize_attrs,
    _normalize_style,
    _stringify,
)

# ---- Nodes -----------------------------------------------------------------------


class Node:
    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        raise NotImplementedError

    def to_dom(self, parent_js=None):
        raise NotImplementedError

    def mount(self, target: Optional[Union[str, Any]] = None):
        if not HAS_JS:
            raise RuntimeError("mount() requires PyScript / a browser (js.document).")
        if target is None:
            parent = _document.body
        elif isinstance(target, str):
            parent = _document.querySelector(target)
            if parent is None:
                raise ValueError(f"mount target not found: {target}")
        else:
            parent = target
        return self.to_dom(parent)


class Text(Node):
    def __init__(self, text: str):
        self.text = str(text)

    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        return self.text if _in_raw_text else _html.escape(self.text)

    def to_dom(self, parent_js=None):
        if not HAS_JS:
            return None
        tn = _document.createTextNode(self.text)
        if parent_js is not None:
            parent_js.appendChild(tn)
        return tn


class Comment(Node):
    def __init__(self, text: str):
        self.text = str(text)

    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        return f"<!-- { _html.escape(self.text) } -->"

    def to_dom(self, parent_js=None):
        if not HAS_JS:
            return None
        cn = _document.createComment(self.text)
        if parent_js is not None:
            parent_js.appendChild(cn)
        return cn


class Fragment(Node):
    def __init__(self, *children: Union[Node, str]):
        self.children: List[Node] = []
        for c in children:
            self.add(c)

    def __enter__(self):
        _BuildStacks.push_element(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _BuildStacks.pop_element()
        return False

    def add(self, child: Union["Node", str, None]) -> Optional["Node"]:
        if child is None:
            return None
        if isinstance(child, str):
            child = Text(child)
        self.children.append(child)
        return child

    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        return "".join(
            ch.to_html(indent, _in_raw_text=_in_raw_text) for ch in self.children
        )

    def to_dom(self, parent_js=None):
        if not HAS_JS:
            return None
        frag = _document.createDocumentFragment()
        for ch in self.children:
            ch.to_dom(frag)
        if parent_js is not None:
            parent_js.appendChild(frag)
        return frag


# ---- Element ---------------------------------------------------------------------

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
RAW_TEXT_TAGS = {"script", "style"}


class Element(Node):
    _tag: str = "div"

    def __init__(self, *children: Union[Node, str], **attrs):
        self.tag = getattr(self, "_tag", "div")
        self.void = self.tag in VOID_TAGS
        self.attrs: Dict[str, str] = {}
        self.children: List[Node] = []

        # Preserve attribute insertion order and apply boolean & class/style semantics.
        for k, v in attrs.items():
            if k in ("class_", "class"):
                if v == "":
                    # explicit clear
                    self.attrs["class"] = ""
                elif v is False or v is None:
                    # explicit remove
                    self.attrs.pop("class", None)
                elif v:
                    self.add_class(v)
                # else (falsy but not ""/False/None) -> skip
            elif k == "style":
                if v is not None:
                    self.set_style(v)
            else:
                self._apply_single_attr(k, v)

        parent = _BuildStacks.current_element_parent()
        if parent is not None:
            parent.add(self)

        for c in children:
            self.add(c)

    def __enter__(self):
        _BuildStacks.push_element(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _BuildStacks.pop_element()
        return False

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        return f"<{cls} tag={self.tag!r} void={self.void} attrs={self.attrs!r} children={len(self.children)}>"

    def add(self, child: Union["Node", str, None]) -> Optional["Node"]:
        if child is None:
            return None
        if self.void:
            raise TypeError(f"<{self.tag}> is a void element and cannot have children.")

        # For raw-text elements, only allow strings or Text nodes (no elements or comments).
        if self.tag in RAW_TEXT_TAGS:
            if isinstance(child, str):
                child = Text(child)
            if not isinstance(child, Text):
                raise TypeError(
                    f"<{self.tag}> only supports string/text content (no elements or comments)."
                )

        if isinstance(child, str):
            child = Text(child)
        self.children.append(child)
        return child

    def __call__(self, *children: Union["Node", str], **attrs) -> "Element":
        for c in children:
            self.add(c)

        # Handle attributes in user-defined order, with boolean/class/style semantics.
        for k, v in attrs.items():
            if k in ("class_", "class"):
                if v == "":
                    self.attrs["class"] = ""
                elif v is False or v is None:
                    self.attrs.pop("class", None)
                elif v:
                    self.add_class(v)
            elif k == "style":
                if v is not None:
                    self.set_style(v)
            else:
                self._apply_single_attr(k, v)
        return self

    # --- attribute helpers ---

    def _apply_single_attr(self, key: str, value: Any) -> None:
        """
        Normalize a single attribute (preserving order) and apply semantics:

          * aria-* : True -> "true"; False/None -> remove; else -> str(value)
          * data-* : True -> "true"; False/None -> remove; else -> _stringify(value)
          * other  : True -> valueless(""); False/None -> remove; else -> normalized value

        _normalize_attrs is used to resolve aliases and hyphenation before applying.
        """
        normalized = _normalize_attrs({key: value})
        # We must consider the *original* Python value for boolean decisions,
        # but apply them to the normalized key(s).
        if any(k.startswith("aria-") for k in normalized.keys()):
            for k in normalized.keys():
                if not k.startswith("aria-"):
                    continue
                if value is True:
                    self.attrs[k] = "true"
                elif value is False or value is None:
                    self.attrs.pop(k, None)
                else:
                    self.attrs[k] = str(value)
            # If normalization produced non-aria keys too, fall through for them below.

        if any(k.startswith("data-") for k in normalized.keys()):
            for k in list(normalized.keys()):
                if not k.startswith("data-"):
                    continue
                if value is True:
                    self.attrs[k] = "true"
                elif value is False or value is None:
                    self.attrs.pop(k, None)
                else:
                    # Use original value for stringify so objects/numbers format nicely
                    self.attrs[k] = _stringify(value)

        # Handle all remaining normalized keys that aren't aria-/data-
        for k, v in normalized.items():
            if k.startswith("aria-") or k.startswith("data-"):
                continue
            if value is True:
                self.attrs[k] = ""
            elif value is False or value is None:
                self.attrs.pop(k, None)
            else:
                self.attrs[k] = v

    def set_attr(self, **attrs) -> "Element":
        # Respect insertion order and semantics for class_/style plus aria-/data-.
        for k, v in attrs.items():
            if k in ("class_", "class"):
                if v == "":
                    self.attrs["class"] = ""
                elif v is False or v is None:
                    self.attrs.pop("class", None)
                elif v:
                    self.add_class(v)
            elif k == "style":
                if v is not None:
                    self.set_style(v)
            else:
                self._apply_single_attr(k, v)
        return self

    def add_class(self, *classes) -> "Element":
        tokens: List[str] = []
        for cls in classes:
            if cls is None or cls is False:
                continue
            if isinstance(cls, (list, tuple, set)):
                for t in cls:
                    if t:
                        tokens.extend(str(t).split())
            else:
                tokens.extend(str(cls).split())
        if not tokens:
            return self
        existing = self.attrs.get("class", "")
        merged = (
            (existing + " " + " ".join(tokens)).strip()
            if existing
            else " ".join(tokens)
        )
        self.attrs["class"] = merged
        return self

    def classes(self, *classes) -> "Element":
        return self.add_class(*classes)

    def set_style(self, style: Union[str, Dict[str, Any]]) -> "Element":
        style_str = _normalize_style(style) if isinstance(style, dict) else style
        existing = self.attrs.get("style", "")
        if existing and style_str:
            self.attrs["style"] = existing.rstrip(";") + ";" + style_str
        elif style_str:
            self.attrs["style"] = style_str
        elif style_str == "":  # allow clearing style
            self.attrs["style"] = ""
        return self

    def style(self, **props) -> "Element":
        return self.set_style(props)

    def data(self, **ds) -> "Element":
        # Route through _apply_single_attr so boolean and stringify semantics apply.
        for k, v in ds.items():
            self._apply_single_attr(f"data-{_hyphenate(k)}", v)
        return self

    def aria(self, **props) -> "Element":
        # Route through _apply_single_attr so ARIA boolean semantics apply.
        for k, v in props.items():
            self._apply_single_attr(f"aria-{_hyphenate(k)}", v)
        return self

    # --- serialization / DOM ---

    def _attrs_to_html(self) -> str:
        if not self.attrs:
            return ""
        parts = []
        # Preserve insertion order of self.attrs
        for k, v in self.attrs.items():
            if (
                v == ""
                and k not in {"value"}
                and k not in {"style", "class"}
                and not k.startswith(("aria-", "data-"))
            ):
                parts.append(f" {k}")  # boolean or valueless attribute
            else:
                v_escaped = _html.escape(v, quote=True)
                parts.append(f' {k}="{v_escaped}"')
        return "".join(parts)

    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        pad = "  " * indent if indent else ""
        open_tag = f"<{self.tag}{self._attrs_to_html()}>"
        if self.void:
            return pad + open_tag
        if not self.children:
            return pad + open_tag + f"</{self.tag}>"

        in_raw = self.tag in RAW_TEXT_TAGS
        if in_raw:
            # Do not add any whitespace/indent/newlines inside raw-text elements
            inner = "".join(ch.to_html(0, _in_raw_text=True) for ch in self.children)
            return pad + open_tag + inner + f"</{self.tag}>"

        has_block = any(isinstance(ch, Element) and not ch.void for ch in self.children)
        if has_block:
            inner = []
            for ch in self.children:
                if isinstance(ch, Element):
                    inner.append("\n" + ch.to_html(indent + 1, _in_raw_text=False))
                else:
                    inner.append(
                        "\n"
                        + ("  " * (indent + 1))
                        + ch.to_html(indent + 1, _in_raw_text=False)
                    )
            inner_str = "".join(inner) + "\n" + pad
            return pad + open_tag + inner_str + f"</{self.tag}>"
        else:
            inner = "".join(
                ch.to_html(indent, _in_raw_text=False) for ch in self.children
            )
            return pad + open_tag + inner + f"</{self.tag}>"

    def to_dom(self, parent_js=None):
        if not HAS_JS:
            return None
        el = _document.createElement(self.tag)
        for k, v in self.attrs.items():
            if (
                v == ""
                and k not in {"value"}
                and k not in {"style", "class"}
                and not k.startswith(("aria-", "data-"))
            ):
                el.setAttribute(k, "")
            else:
                el.setAttribute(k, v)
        if not self.void:
            for ch in self.children:
                ch.to_dom(el)
        if parent_js is not None:
            parent_js.appendChild(el)
        return el


# ---- HTML5 Tag -> Class mapping ---------------------------------------------------

TAG_TO_CLASSNAME: Dict[str, str] = {
    # Document metadata
    "html": "Html",
    "head": "Head",
    "title": "Title",
    "base": "Base",
    "link": "Link",
    "meta": "Meta",
    "style": "Style",
    # Sections
    "body": "Body",
    "address": "Address",
    "article": "Article",
    "aside": "Aside",
    "footer": "Footer",
    "header": "Header",
    "h1": "Heading1",
    "h2": "Heading2",
    "h3": "Heading3",
    "h4": "Heading4",
    "h5": "Heading5",
    "h6": "Heading6",
    "hgroup": "HeadingGroup",
    "main": "Main",
    "nav": "Navigation",
    "section": "Section",
    # Grouping
    "blockquote": "BlockQuote",
    "dd": "DescriptionDetails",
    "div": "Division",
    "dl": "DescriptionList",
    "dt": "DescriptionTerm",
    "figcaption": "FigureCaption",
    "figure": "Figure",
    "hr": "HorizontalRule",
    "li": "ListItem",
    "menu": "Menu",
    "ol": "OrderedList",
    "p": "Paragraph",
    "pre": "PreformattedText",
    "ul": "UnorderedList",
    # Text-level
    "a": "Anchor",
    "abbr": "Abbreviation",
    "b": "Bold",
    "bdi": "BidirectionalIsolation",
    "bdo": "BidirectionalOverride",
    "br": "LineBreak",
    "cite": "Citation",
    "code": "Code",
    "data": "Data",
    "dfn": "Definition",
    "em": "Emphasis",
    "i": "Italic",
    "kbd": "KeyboardInput",
    "mark": "Mark",
    "q": "Quotation",
    "rp": "RubyParenthesis",
    "rt": "RubyText",
    "ruby": "RubyAnnotation",
    "s": "Strikethrough",
    "samp": "SampleOutput",
    "small": "Small",
    "span": "Span",
    "strong": "Strong",
    "sub": "Subscript",
    "sup": "Superscript",
    "time": "Time",
    "u": "Underline",
    "var": "Variable",
    "wbr": "WordBreakOpportunity",
    # Edits
    "del": "Deletion",
    "ins": "Insertion",
    # Embedded
    "area": "MapArea",
    "audio": "Audio",
    "img": "Image",
    "map": "ImageMap",
    "track": "Track",
    "video": "Video",
    "embed": "Embed",
    "iframe": "InlineFrame",
    "object": "Object",
    "param": "Parameter",
    "picture": "Picture",
    "source": "Source",
    # Scripting
    "canvas": "Canvas",
    "noscript": "NoScript",
    "script": "Script",
    "slot": "Slot",
    "template": "Template",
    # Table
    "caption": "TableCaption",
    "col": "TableColumn",
    "colgroup": "TableColumnGroup",
    "table": "Table",
    "tbody": "TableBody",
    "td": "TableDataCell",
    "tfoot": "TableFooter",
    "th": "TableHeaderCell",
    "thead": "TableHead",
    "tr": "TableRow",
    # Forms
    "button": "Button",
    "datalist": "DataList",
    "fieldset": "FieldSet",
    "form": "Form",
    "input": "Input",
    "label": "Label",
    "legend": "Legend",
    "meter": "Meter",
    "optgroup": "OptionGroup",
    "option": "Option",
    "output": "Output",
    "progress": "Progress",
    "select": "Select",
    "textarea": "TextArea",
    # Interactive
    "details": "Details",
    "dialog": "Dialog",
    "summary": "Summary",
    # Non-standard (optional convenience)
    "portal": "Portal",
}

CLASSNAME_TO_TAG: Dict[str, str] = {v: k for k, v in TAG_TO_CLASSNAME.items()}
TAG_TO_CLASS: Dict[str, type] = {}
CLASSNAME_TO_CLASS: Dict[str, type] = {}


def rebuild_html_classes(overrides: Optional[Dict[str, str]] = None) -> None:
    """
    Rebuild the HTML element classes from TAG_TO_CLASSNAME, optionally using
    non-mutating overrides for this rebuild call.
    """
    global CLASSNAME_TO_TAG, TAG_TO_CLASS, CLASSNAME_TO_CLASS

    # Build an effective mapping without mutating the canonical base mapping.
    effective: Dict[str, str] = dict(TAG_TO_CLASSNAME)
    if overrides:
        effective.update(overrides)

    # remove previous generated classes from this module's globals
    for name in list(CLASSNAME_TO_CLASS.keys()):
        if name in globals():
            try:
                del globals()[name]
            except Exception:
                pass

    TAG_TO_CLASS.clear()
    CLASSNAME_TO_CLASS.clear()

    for tag, class_name in effective.items():
        cls = type(class_name, (Element,), {"_tag": tag})
        globals()[class_name] = cls
        TAG_TO_CLASS[tag] = cls
        CLASSNAME_TO_CLASS[class_name] = cls

    # Update reverse mapping to reflect effective mapping.
    CLASSNAME_TO_TAG = {v: k for k, v in effective.items()}


def element_class_for_tag(tag: str) -> type:
    return TAG_TO_CLASS[tag]


def tag_for_element_class_name(class_name: str) -> str:
    return CLASSNAME_TO_TAG[class_name]


def create(tag: str, *children, **attrs) -> Element:
    """Instantiate by tag string using the current mapping."""
    return element_class_for_tag(tag)(*children, **attrs)


def custom(tag_name: str, *children, **attrs) -> Element:
    """Create a custom element with an arbitrary tag name (e.g., web components)."""
    cls = type(
        "Custom_" + "".join(p.capitalize() for p in tag_name.split("-")),
        (Element,),
        {"_tag": tag_name},
    )
    return cls(*children, **attrs)


def html_string(node: Node) -> str:
    return node.to_html()


# Generate classes on import
rebuild_html_classes()


__all__ = [
    "Node",
    "Text",
    "Comment",
    "Fragment",
    "Element",
    "create",
    "custom",
    "html_string",
    "rebuild_html_classes",
    "element_class_for_tag",
    "tag_for_element_class_name",
    "TAG_TO_CLASSNAME",
    "CLASSNAME_TO_TAG",
    "TAG_TO_CLASS",
    "CLASSNAME_TO_CLASS",
]
