"""
Card widget for content display.
"""

from typing import Optional, List
from fastpluggy.core.widgets.base import AbstractWidget


class CardWidget(AbstractWidget):
    """Bootstrap-style card widget for content display."""

    widget_type = "card"
    template_name = "ui_tools/extra_widget/display/card.html.j2"
    macro_name = "render_card"
    render_method = "macro"

    category = "display"
    description = "Bootstrap card component for displaying content with optional header, body, and footer"
    icon = "rectangle-list"

    def __init__(
        self,
        title: Optional[str] = None,
        content: Optional[str | List[str]] = None,
        footer: Optional[str] = None,
        header: Optional[str] = None,
        card_type: str = "default",
        text_color: Optional[str] = None,
        bg_color: Optional[str] = None,
        border_color: Optional[str] = None,
        image_url: Optional[str] = None,
        image_position: str = "top",
        links: Optional[List] = None,
        **kwargs
    ):
        self.title = title
        self.content = content
        self.footer = footer
        self.header = header
        self.card_type = card_type
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.image_url = image_url
        self.image_position = image_position
        self.links = links or []
        super().__init__(**kwargs)

    def process(self, **kwargs) -> None:
        """Build CSS classes for the card."""
        css_classes = ["card"]

        if self.card_type and self.card_type != "default":
            card_type_mapping = {
                "primary": "border-primary",
                "secondary": "border-secondary", 
                "success": "border-success",
                "danger": "border-danger",
                "warning": "border-warning",
                "info": "border-info",
                "light": "border-light",
                "dark": "border-dark"
            }
            if self.card_type in card_type_mapping:
                css_classes.append(card_type_mapping[self.card_type])

        if self.bg_color:
            css_classes.append(self.bg_color)
        if self.text_color:
            css_classes.append(self.text_color)
        if self.border_color:
            css_classes.append(self.border_color)

        # Convert list content to string if needed
        if isinstance(self.content, list):
            self.content = ''.join(self.content)

        self.css_classes = " ".join(css_classes)
        self.has_actions = bool(self.footer or self.links)
