"""Microsoft Fluent UI System Icons via the Iconify CDN.

Icons are rendered with the <iconify-icon> web component (loaded once from
Iconify's CDN in base.html), which fetches each icon's SVG live from
https://api.iconify.design and renders it with full CSS color/sizing control
(fill: currentColor), so hover states, dark mode, and the app's chart colors
all keep working exactly as with inline SVG.
"""
from markupsafe import Markup


def fluent_icon(name: str, css_class: str = "") -> Markup:
    """Render a Microsoft Fluent icon (Iconify "fluent" set) by its kebab-case name,
    e.g. fluent_icon('brain-circuit-24-regular')."""
    classes = f"icon {css_class}".strip()
    return Markup(
        f'<iconify-icon icon="fluent:{name}" class="{classes}" aria-hidden="true"></iconify-icon>'
    )
