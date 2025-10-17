from typing import Annotated

from fastpluggy.core.module_base import FastPluggyBaseModule
from fastpluggy.core.tools.inspect_tools import InjectDependency
from fastpluggy.core.tools.install import is_installed
from fastpluggy.fastpluggy import FastPluggy


class UiToolsModule(FastPluggyBaseModule):
    module_name: str = "ui_tools"

    module_menu_name: str = "UI Tools"
    module_menu_icon: str = "fa fa-tools"
    module_menu_type: str = "no"

    extra_js_files: list = ['/app_static/ui_tools/script.js']
    extra_css_files: list = ['/app_static/ui_tools/style.css']

    def after_setup_templates(self, fast_pluggy: Annotated[FastPluggy, InjectDependency]):
        from .template_tools import b64encode_filter, pydantic_model_dump, nl2br

        fast_pluggy.templates.env.filters['b64encode'] = b64encode_filter
        fast_pluggy.templates.env.filters['pydantic_model_dump'] = pydantic_model_dump
        fast_pluggy.templates.env.filters["nl2br"] = nl2br

        if is_installed('babel'):
            from .localization import localizedcurrency, localizeddate

            fast_pluggy.templates.env.filters["localizedcurrency"] = localizedcurrency
            fast_pluggy.templates.env.filters["localizeddate"] = localizeddate

        from .html_render import from_json_filter
        fast_pluggy.templates.env.filters["from_json"] = from_json_filter

        # todo check if its needed
        from fastpluggy.core.widgets import FastPluggyWidgets
        from .extra_widget.display.stats import StatsWidget
        from .extra_widget.display.card import CardWidget
        from .extra_widget.display.alert import AlertWidget
        from .extra_widget.display.code import CodeWidget
        from .extra_widget.display.progress import ProgressBarWidget
        FastPluggyWidgets.register_plugin_widgets('ui_tools', [AlertWidget, CardWidget, StatsWidget, CodeWidget, ProgressBarWidget])
