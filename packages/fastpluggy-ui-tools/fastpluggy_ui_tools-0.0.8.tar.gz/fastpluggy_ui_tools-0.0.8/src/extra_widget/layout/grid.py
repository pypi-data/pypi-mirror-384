"""
Grid layout widget for responsive layouts.
"""

from typing import List, Optional, Union, Dict, Any
from fastpluggy.core.widgets.base import AbstractWidget


class GridItem:
    """Grid item wrapper for responsive column sizing."""

    def __init__(
        self,
        widget: AbstractWidget,
        col_xs: Optional[int] = None,
        col_sm: Optional[int] = None,
        col_md: Optional[int] = None,
        col_lg: Optional[int] = None,
        col_xl: Optional[int] = None,
        col_xxl: Optional[int] = None,
        offset_xs: Optional[int] = None,
        offset_sm: Optional[int] = None,
        offset_md: Optional[int] = None,
        offset_lg: Optional[int] = None,
        offset_xl: Optional[int] = None,
        offset_xxl: Optional[int] = None,
        css_class: Optional[str] = None,
        order: Optional[int] = None,
        **kwargs
    ):
        self.widget = widget
        self.col_xs = col_xs
        self.col_sm = col_sm
        self.col_md = col_md
        self.col_lg = col_lg
        self.col_xl = col_xl
        self.col_xxl = col_xxl
        self.offset_xs = offset_xs
        self.offset_sm = offset_sm
        self.offset_md = offset_md
        self.offset_lg = offset_lg
        self.offset_xl = offset_xl
        self.offset_xxl = offset_xxl
        self.css_class = css_class
        self.order = order

    def get_column_classes(self) -> str:
        """Generate Bootstrap column classes."""
        classes = []

        # Column sizes
        for breakpoint, size in [
            ('', self.col_xs), ('sm', self.col_sm), ('md', self.col_md),
            ('lg', self.col_lg), ('xl', self.col_xl), ('xxl', self.col_xxl)
        ]:
            if size:
                prefix = f"col-{breakpoint}-" if breakpoint else "col-"
                classes.append(f"{prefix}{size}")

        # Offsets
        for breakpoint, offset in [
            ('', self.offset_xs), ('sm', self.offset_sm), ('md', self.offset_md),
            ('lg', self.offset_lg), ('xl', self.offset_xl), ('xxl', self.offset_xxl)
        ]:
            if offset:
                prefix = f"offset-{breakpoint}-" if breakpoint else "offset-"
                classes.append(f"{prefix}{offset}")

        if self.order:
            classes.append(f"order-{self.order}")
        if self.css_class:
            classes.append(self.css_class)

        # Default to col if no specific column class
        if not any(cls.startswith('col-') for cls in classes):
            classes.append('col')

        return " ".join(classes)


class GridWidget(AbstractWidget):
    """Responsive grid layout widget using Bootstrap grid system."""

    widget_type = "grid"
    template_name = "ui_tools/extra_widget/layout/grid.html.j2"

    category = "layout"
    description = "Responsive grid layout using Bootstrap grid system with customizable breakpoints"
    icon = "th"

    def __init__(
        self,
        items: Optional[List[Union[GridItem, AbstractWidget, Dict[str, Any]]]] = None,
        title: Optional[str] = None,
        gutter: Optional[str] = None,
        row_class: Optional[str] = None,
        container_class: Optional[str] = None,
        equal_height: bool = False,
        vertical_align: Optional[str] = None,
        horizontal_align: Optional[str] = None,
        responsive: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.items = items or []
        self.title = title
        self.gutter = gutter
        self.row_class = row_class
        self.container_class = container_class
        self.equal_height = equal_height
        self.vertical_align = vertical_align
        self.horizontal_align = horizontal_align
        self.responsive = responsive

    def process(self, **kwargs) -> None:
        """Process grid items and build CSS classes."""
        # Process items into GridItem objects
        processed_items = []

        for item in self.items:
            if isinstance(item, GridItem):
                if hasattr(item.widget, "process"):
                    item.widget.process(**kwargs)
                processed_items.append(item)
            elif isinstance(item, AbstractWidget):
                if hasattr(item, "process"):
                    item.process(**kwargs)
                processed_items.append(GridItem(widget=item))
            elif isinstance(item, dict):
                widget = item.pop('widget')
                if hasattr(widget, "process"):
                    widget.process(**kwargs)
                processed_items.append(GridItem(widget=widget, **item))

        self.processed_items = processed_items

        # Build row CSS classes
        row_classes = ["row"]
        if self.responsive:
            row_classes.append("row-cards")
        if self.gutter:
            row_classes.append(self.gutter)
        if self.equal_height:
            row_classes.append("row-deck")
        if self.vertical_align:
            row_classes.append(f"align-items-{self.vertical_align}")
        if self.horizontal_align:
            row_classes.append(f"justify-content-{self.horizontal_align}")
        if self.row_class:
            row_classes.append(self.row_class)

        self.row_css_classes = " ".join(row_classes)

        # Container classes
        container_classes = []
        if self.container_class:
            container_classes.append(self.container_class)
        self.container_css_classes = " ".join(container_classes) if container_classes else None

    @classmethod
    def create_responsive_grid(
        cls,
        widgets: List[AbstractWidget],
        cols_sm: int = 1,
        cols_md: int = 2, 
        cols_lg: int = 3,
        cols_xl: int = 4,
        **kwargs
    ):
        """Factory method to create responsive grid with automatic sizing."""
        col_size_sm = 12 // cols_sm
        col_size_md = 12 // cols_md
        col_size_lg = 12 // cols_lg
        col_size_xl = 12 // cols_xl

        items = []
        for widget in widgets:
            grid_item = GridItem(
                widget=widget,
                col_sm=col_size_sm,
                col_md=col_size_md,
                col_lg=col_size_lg,
                col_xl=col_size_xl
            )
            items.append(grid_item)

        return cls(items=items, **kwargs)
