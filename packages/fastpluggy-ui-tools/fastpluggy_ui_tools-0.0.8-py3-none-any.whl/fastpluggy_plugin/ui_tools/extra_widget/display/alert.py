"""
Alert widget for displaying messages.
"""

from typing import Optional
from fastpluggy.core.widgets.base import AbstractWidget


class AlertWidget(AbstractWidget):
    """Bootstrap alert widget for displaying messages."""

    widget_type = "alert"
    template_name = "ui_tools/extra_widget/display/alert.html.j2"
    category = "display"
    description = "Bootstrap alert component for displaying contextual feedback messages"
    icon = "exclamation-triangle"

    def __init__(
        self,
        message: str = "",
        alert_type: str = "info",
        dismissible: bool = True,
        auto_dismiss: Optional[int] = None,
        icon: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.message = message
        self.alert_type = alert_type
        self.dismissible = dismissible
        self.auto_dismiss = auto_dismiss
        self.icon = icon

    def process(self, **kwargs) -> None:
        """Build alert classes and configuration."""
        css_classes = [f"alert alert-{self.alert_type}"]

        if self.dismissible:
            css_classes.append("alert-dismissible fade show")

        self.css_classes = " ".join(css_classes)

        # Default icons for alert types
        if not self.icon:
            icon_mapping = {
                "success": "check-circle",
                "danger": "exclamation-circle", 
                "warning": "exclamation-triangle",
                "info": "info-circle"
            }
            self.icon = icon_mapping.get(self.alert_type, "info-circle")
