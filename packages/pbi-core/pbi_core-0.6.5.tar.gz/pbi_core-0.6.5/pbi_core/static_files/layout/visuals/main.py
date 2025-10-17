from typing import Any

from pbi_core.attrs import converter

from .action_button import ActionButton
from .bar_chart import BarChart
from .basic_shape import BasicShape
from .card import Card
from .clustered_column_chart import ClusteredColumnChart
from .column_chart import ColumnChart
from .donut_chart import DonutChart
from .funnel import Funnel
from .generic import GenericVisual
from .image import Image
from .line_chart import LineChart
from .line_stacked_column_combo_chart import LineStackedColumnComboChart
from .pie_chart import PieChart
from .scatter_chart import ScatterChart
from .slicer import Slicer
from .table import TableChart
from .text_box import TextBox

Visual = (
    ActionButton
    | BarChart
    | GenericVisual
    | BasicShape
    | Card
    | ColumnChart
    | ClusteredColumnChart
    | DonutChart
    | Funnel
    | Image
    | LineChart
    | LineStackedColumnComboChart
    | PieChart
    | ScatterChart
    | Slicer
    | TableChart
    | TextBox
)


@converter.register_structure_hook
def get_visual_type(v: dict[str, Any], _: type | None = None) -> Visual:
    assert "visualType" in v
    assert isinstance(v["visualType"], str)

    mapping = {
        "actionButton": ActionButton,
        "barChart": BarChart,
        "basicShape": BasicShape,
        "card": Card,
        "clusteredColumnChart": ClusteredColumnChart,
        "columnChart": ColumnChart,
        "donutChart": DonutChart,
        "funnel": Funnel,
        "image": Image,
        "lineChart": LineChart,
        "lineStackedColumnComboChart": LineStackedColumnComboChart,
        "pieChart": PieChart,
        "scatterChart": ScatterChart,
        "slicer": Slicer,
        "tableEx": TableChart,
        "textbox": TextBox,
    }
    return mapping.get(v["visualType"], GenericVisual).model_validate(v)


@converter.register_unstructure_hook
def unparse_visual_type(v: Visual) -> dict[str, Any]:
    return converter.unstructure(v)


__all__ = ["GenericVisual", "Visual"]
