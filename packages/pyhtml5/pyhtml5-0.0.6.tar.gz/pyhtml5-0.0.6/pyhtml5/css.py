"""
css.py — Generic CSS builder for rules and common at-rules.
"""

from __future__ import annotations

from collections.abc import Sequence as _Sequence
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .utils import HAS_JS, _BuildStacks, _document, _hyphenate

# --- helpers ---------------------------------------------------------------------


def _css_prop_name(name: str) -> str:
    # Preserve custom properties verbatim (must start with --)
    if name.startswith("--"):
        return name
    return _hyphenate(name)


# A conservative set of unitless CSS properties.
# Numbers for these are emitted without units. Zero is always emitted as "0".
UNITLESS_PROPS = {
    "animation-iteration-count",
    "border-image-slice",
    "column-count",
    "flex-grow",
    "flex-shrink",
    "font-weight",
    "line-height",
    "opacity",
    "order",
    "orphans",
    "tab-size",
    "widows",
    "z-index",
    # Grid helpers
    "grid-row",
    "grid-row-start",
    "grid-row-end",
    "grid-column",
    "grid-column-start",
    "grid-column-end",
}


def _format_css_value(prop: str, value: Any) -> Optional[str]:
    """
    Convert a Python value to a CSS value string for a given property.
    - Skip None / False / "" (caller should treat as 'omit').
    - For custom properties ("--foo"), return str(value) verbatim (no unit gymnastics).
    - For numeric values:
        * if value == 0 -> "0" (no unit)
        * if prop in UNITLESS_PROPS -> raw number
        * else -> append "px"
    - For strings: use as-is.
    """
    if value is None or value is False or value == "":
        return None

    # Custom property: pass through verbatim
    if prop.startswith("--"):
        return str(value)

    # Hyphenated property name for unitless lookup
    prop_name = _css_prop_name(prop)

    if isinstance(value, (int, float)):
        if value == 0:
            return "0"
        if prop_name in UNITLESS_PROPS:
            return str(value)
        return f"{value}px"

    # Otherwise, treat as raw CSS token string
    return str(value)


# --- core data structures ---------------------------------------------------------


@dataclass
class CSSDeclaration:
    prop: str
    value: str
    important: bool = False

    def to_css(self) -> str:
        imp = " !important" if self.important else ""
        return f"{self.prop}:{self.value}{imp};"


class CSSContainer:
    def __init__(self):
        self.children: List[
            Union[
                "CSSStyleRule",
                "AtRule",
                "_AtRuleHeader",
                "KeyframesRule",
                "PageRule",
                "FontFaceRule",
                "CounterStyleRule",
                "PropertyRule",
            ]
        ] = []

    def __enter__(self):
        _BuildStacks.push_css(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _BuildStacks.pop_css()
        return False

    def add(self, child):
        # Guard header-only at-rules from appearing anywhere but top-level Stylesheet
        if isinstance(child, _AtRuleHeader):
            if not isinstance(self, Stylesheet):
                raise ValueError(
                    "@import/@namespace allowed only at the stylesheet header"
                )
            # Enforce top-of-stylesheet ordering: all header rules must precede any other rules.
            if any(not isinstance(c, _AtRuleHeader) for c in self.children):
                raise ValueError(
                    "@import/@namespace must appear before all other rules in the stylesheet"
                )
        self.children.append(child)
        return child

    # ----- rule builders on any container (attach to nearest container) ------------

    def rule(self, selector: Union[str, _Sequence], **props) -> "CSSStyleRule":
        rule = CSSStyleRule(selector, props or None)
        container = _BuildStacks.current_css_container() or self
        container.add(rule)
        return rule

    def media(self, query: str) -> "AtRule":
        ar = AtRule("media", query)
        (_BuildStacks.current_css_container() or self).add(ar)
        return ar

    def supports(self, condition: str) -> "AtRule":
        ar = AtRule("supports", condition)
        (_BuildStacks.current_css_container() or self).add(ar)
        return ar

    def layer(self, name: Optional[str] = None) -> "AtRule":
        if name is None or not str(name).strip():
            raise ValueError("layer name required")
        ar = AtRule("layer", name)
        (_BuildStacks.current_css_container() or self).add(ar)
        return ar

    def container(self, query: str) -> "AtRule":
        ar = AtRule("container", query)
        (_BuildStacks.current_css_container() or self).add(ar)
        return ar

    def page(self, selector: Optional[str] = None) -> "PageRule":
        pr = PageRule(selector)
        (_BuildStacks.current_css_container() or self).add(pr)
        return pr

    def keyframes(self, name: str) -> "KeyframesRule":
        kf = KeyframesRule(name)
        (_BuildStacks.current_css_container() or self).add(kf)
        return kf

    def font_face(self, **props) -> "FontFaceRule":
        ff = FontFaceRule(props or None)
        (_BuildStacks.current_css_container() or self).add(ff)
        return ff

    def counter_style(self, name: str) -> "CounterStyleRule":
        cs = CounterStyleRule(name)
        (_BuildStacks.current_css_container() or self).add(cs)
        return cs

    def property(self, name: str) -> "PropertyRule":
        pr = PropertyRule(name)
        (_BuildStacks.current_css_container() or self).add(pr)
        return pr

    # ----- top-level header at-rules (only on Stylesheet) --------------------------

    def to_css(self, indent: int = 0) -> str:
        return "".join(ch.to_css(indent) for ch in self.children)

    # Mount QoL: id/replace support and stateful references
    def mount(
        self,
        target: Optional[Union[str, Any]] = None,
        *,
        id: Optional[str] = None,
        replace: bool = True,
    ):
        css_text = self.to_css()
        if not HAS_JS:
            raise RuntimeError(
                "CSS mounting requires PyScript / a browser (js.document)."
            )
        style_el = None

        if id:
            existing = _document.querySelector(f"style#{id}")
            if existing is not None and replace:
                existing.textContent = css_text
                style_el = existing
            elif existing is not None and not replace:
                style_el = _document.createElement("style")
                style_el.setAttribute("type", "text/css")
                # do NOT duplicate id on a new element
                style_el.textContent = css_text
                # append below
            else:
                style_el = _document.createElement("style")
                style_el.setAttribute("type", "text/css")
                style_el.setAttribute("id", id)
                style_el.textContent = css_text
        else:
            style_el = _document.createElement("style")
            style_el.setAttribute("type", "text/css")
            style_el.textContent = css_text

        # Append if we created a new node or replace=False case
        if style_el.parentNode is None:
            if target is None:
                _document.head.appendChild(style_el)
            elif isinstance(target, str):
                parent = _document.querySelector(target)
                if parent is None:
                    raise ValueError(f"mount target not found: {target}")
                parent.appendChild(style_el)
            else:
                target.appendChild(style_el)

        # cache references for DX
        self.element = style_el
        self.last_css = css_text
        return style_el


class Stylesheet(CSSContainer):
    """Top-level CSS container (semantic alias)."""

    # Header-only at-rules: only valid at top level
    def import_(self, url: str, media: Optional[str] = None) -> "_AtRuleHeader":
        # Ensure we are adding at top-level stylesheet
        cur = _BuildStacks.current_css_container()
        if cur is not None and cur is not self:
            raise ValueError("@import is only allowed at the stylesheet header")
        prelude = (
            f'url("{url}")' if not url.strip().startswith(("url(", '"', "'")) else url
        )
        if media:
            prelude = f"{prelude} {media}"
        node = _AtRuleHeader("import", prelude)
        self.add(node)
        return node

    def namespace(self, prefix: Optional[str], uri: str) -> "_AtRuleHeader":
        cur = _BuildStacks.current_css_container()
        if cur is not None and cur is not self:
            raise ValueError("@namespace is only allowed at the stylesheet header")
        uri_part = (
            f'url("{uri}")' if not uri.strip().startswith(("url(", '"', "'")) else uri
        )
        prelude = f"{prefix} {uri_part}" if prefix else f"{uri_part}"
        node = _AtRuleHeader("namespace", prelude)
        self.add(node)
        return node


# --- rules ------------------------------------------------------------------------


class CSSStyleRule:
    def __init__(
        self, selector: Union[str, _Sequence], props: Optional[Dict[str, Any]] = None
    ):
        # Selector ergonomics: accept any non-string Sequence and join with ", "
        if isinstance(selector, _Sequence) and not isinstance(selector, (str, bytes)):
            self.selector = ", ".join(str(s) for s in selector)
        else:
            self.selector = str(selector)
        self.decls: List[CSSDeclaration] = []
        if props:
            for k, v in props.items():
                val = _format_css_value(k, v)
                if val is None:
                    continue
                self.decls.append(
                    CSSDeclaration(_css_prop_name(k), val, important=False)
                )

    # Not a container: keep with-support for ergonomics, but do not push on stack
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def decl(self, prop: str, value: Any, *, important: bool = False) -> "CSSStyleRule":
        val = _format_css_value(prop, value)
        if val is None:
            return self
        self.decls.append(
            CSSDeclaration(_css_prop_name(prop), val, important=important)
        )
        return self

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join("  " * (indent + 1) + d.to_css() + "\n" for d in self.decls)
        return f"{pad}{self.selector} {{\n{inner}{pad}}}\n"


class AtRule(CSSContainer):
    def __init__(self, name: str, prelude: str):
        super().__init__()
        self.name = name
        self.prelude = prelude

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join(ch.to_css(indent + 1) for ch in self.children)
        return f"{pad}@{self.name} {self.prelude} {{\n{inner}{pad}}}\n"


class _AtRuleHeader:
    """
    Header-only (blockless) at-rules like @import and @namespace.
    These must appear at the stylesheet top-level.
    """

    def __init__(self, name: str, prelude: str):
        self.name = name
        self.prelude = prelude

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        return f"{pad}@{self.name} {self.prelude};\n"


class KeyframesRule(CSSContainer):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def frame(self, selector: Union[str, int, float], **props) -> "CSSStyleRule":
        if isinstance(selector, (int, float)):
            sel = f"{selector}%"
        else:
            sel = str(selector)
        rule = CSSStyleRule(sel, props or None)
        # Always attach frames to this keyframes block, not any outer container on the stack.
        self.add(rule)
        return rule

    # Ergonomics
    def from_(self, **props) -> "CSSStyleRule":
        return self.frame("from", **props)

    def to(self, **props) -> "CSSStyleRule":
        return self.frame("to", **props)

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join(ch.to_css(indent + 1) for ch in self.children)
        return f"{pad}@keyframes {self.name} {{\n{inner}{pad}}}\n"


class PageRule(CSSContainer):
    def __init__(self, selector: Optional[str] = None):
        super().__init__()
        self.selector = selector

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        head = "@page" + (f" {self.selector}" if self.selector else "")
        inner = "".join(ch.to_css(indent + 1) for ch in self.children)
        return f"{pad}{head} {{\n{inner}{pad}}}\n"


class FontFaceRule:
    def __init__(self, props: Optional[Dict[str, Any]] = None):
        self.decls: List[CSSDeclaration] = []
        if props:
            for k, v in props.items():
                val = _format_css_value(k, v)
                if val is None:
                    continue
                self.decls.append(
                    CSSDeclaration(_css_prop_name(k), val, important=False)
                )

    # Non-container: allow `with` ergonomics without altering the build stack
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def decl(self, prop: str, value: Any, *, important: bool = False) -> "FontFaceRule":
        val = _format_css_value(prop, value)
        if val is None:
            return self
        self.decls.append(
            CSSDeclaration(_css_prop_name(prop), val, important=important)
        )
        return self

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join("  " * (indent + 1) + d.to_css() + "\n" for d in self.decls)
        return f"{pad}@font-face {{\n{inner}{pad}}}\n"


class CounterStyleRule:
    def __init__(self, name: str):
        self.name = name
        self.decls: List[CSSDeclaration] = []

    # Non-container: allow `with` ergonomics without altering the build stack
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def decl(
        self, prop: str, value: Any, *, important: bool = False
    ) -> "CounterStyleRule":
        val = _format_css_value(prop, value)
        if val is None:
            return self
        self.decls.append(
            CSSDeclaration(_css_prop_name(prop), val, important=important)
        )
        return self

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join("  " * (indent + 1) + d.to_css() + "\n" for d in self.decls)
        return f"{pad}@counter-style {self.name} {{\n{inner}{pad}}}\n"


class PropertyRule:
    def __init__(self, name: str):
        self.name = name
        self.decls: List[CSSDeclaration] = []

    # Non-container: allow `with` ergonomics without altering the build stack
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def decl(self, prop: str, value: Any, *, important: bool = False) -> "PropertyRule":
        val = _format_css_value(prop, value)
        if val is None:
            return self
        self.decls.append(
            CSSDeclaration(_css_prop_name(prop), val, important=important)
        )
        return self

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join("  " * (indent + 1) + d.to_css() + "\n" for d in self.decls)
        return f"{pad}@property {self.name} {{\n{inner}{pad}}}\n"


# --- utilities -------------------------------------------------------------------


def css_string(sheet: Stylesheet) -> str:
    return sheet.to_css()


__all__ = [
    "CSSDeclaration",
    "CSSContainer",
    "CSSStyleRule",
    "AtRule",
    "KeyframesRule",
    "PageRule",
    "FontFaceRule",
    "CounterStyleRule",
    "PropertyRule",
    "Stylesheet",
    "css_string",
    "UNITLESS_PROPS",
]
