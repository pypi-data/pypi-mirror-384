"""
Code widget for displaying code with syntax highlighting.
"""

from typing import Optional
from fastpluggy.core.widgets.base import AbstractWidget


class CodeWidget(AbstractWidget):
    """Widget for displaying code with syntax highlighting."""

    widget_type = "code"
    template_name = "ui_tools/extra_widget/display/code.html.j2"
    macro_name = "render_code"
    render_method = "macro"

    category = "display"
    description = "Display code with syntax highlighting"
    icon = "code"

    def __init__(
        self,
        code: str,
        language: Optional[str] = None,
        title: Optional[str] = None,
        line_numbers: bool = True,
        theme: str = "default",
        **kwargs
    ):
        """
        Initialize a code widget.

        Args:
            code: The code to display
            language: The programming language for syntax highlighting
            title: Optional title for the code block
            line_numbers: Whether to show line numbers
            theme: The syntax highlighting theme
        """
        self.code = code
        self.language = language
        self.title = title
        self.line_numbers = line_numbers
        self.theme = theme
        super().__init__(**kwargs)

    def process(self, **kwargs) -> None:
        """Process the widget before rendering."""
        css_classes = ["code-widget"]
        
        if self.language:
            css_classes.append(f"language-{self.language}")
        
        if self.theme and self.theme != "default":
            css_classes.append(f"theme-{self.theme}")
            
        self.css_classes = " ".join(css_classes)