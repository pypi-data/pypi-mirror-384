"""
Progress bar widget for displaying progress.
"""

from typing import Optional
from fastpluggy.core.widgets.base import AbstractWidget


class ProgressBarWidget(AbstractWidget):
    """Bootstrap-style progress bar widget for displaying progress."""

    widget_type = "progress"
    template_name = "ui_tools/extra_widget/display/progress.html.j2"
    macro_name = "render_progress"
    render_method = "macro"

    category = "display"
    description = "Bootstrap progress bar component for displaying progress with customizable styling"
    icon = "chart-bar"

    def __init__(
        self,
        value: float = 0,
        max_value: float = 100,
        min_value: float = 0,
        title: Optional[str] = None,
        label: Optional[str] = None,
        show_percentage: bool = True,
        show_value: bool = False,
        bar_type: str = "default",
        striped: bool = False,
        animated: bool = False,
        height: Optional[str] = None,
        **kwargs
    ):
        self.value = value
        self.max_value = max_value
        self.min_value = min_value
        self.title = title
        self.label = label
        self.show_percentage = show_percentage
        self.show_value = show_value
        self.bar_type = bar_type
        self.striped = striped
        self.animated = animated
        self.height = height
        super().__init__(**kwargs)

    def process(self, **kwargs) -> None:
        """Calculate progress percentage and build CSS classes."""
        # Calculate percentage
        if self.max_value > self.min_value:
            self.percentage = ((self.value - self.min_value) / (self.max_value - self.min_value)) * 100
        else:
            self.percentage = 0
        
        # Ensure percentage is within bounds
        self.percentage = max(0, min(100, self.percentage))
        
        # Build CSS classes for progress bar
        css_classes = ["progress-bar"]
        
        if self.bar_type and self.bar_type != "default":
            bar_type_mapping = {
                "primary": "bg-primary",
                "secondary": "bg-secondary", 
                "success": "bg-success",
                "danger": "bg-danger",
                "warning": "bg-warning",
                "info": "bg-info",
                "light": "bg-light",
                "dark": "bg-dark"
            }
            if self.bar_type in bar_type_mapping:
                css_classes.append(bar_type_mapping[self.bar_type])
        
        if self.striped:
            css_classes.append("progress-bar-striped")
        
        if self.animated:
            css_classes.append("progress-bar-animated")
        
        self.css_classes = " ".join(css_classes)
        
        # Format display text
        if self.show_percentage:
            self.display_text = f"{self.percentage:.1f}%"
        elif self.show_value:
            self.display_text = f"{self.value}/{self.max_value}"
        else:
            self.display_text = ""