from typing import Any, Literal

from pbi_core.attrs import converter, define
from pbi_core.static_files.layout._base_node import LayoutNode
from pbi_core.static_files.layout.condition import ConditionType
from pbi_core.static_files.layout.sources import LiteralSource, MeasureSource, Source
from pbi_core.static_files.layout.sources.aggregation import AggregationSource, SelectRef
from pbi_core.static_files.layout.sources.column import ColumnSource


@define()
class LiteralExpression(LayoutNode):
    expr: LiteralSource


@define()
class MeasureExpression(LayoutNode):
    expr: MeasureSource


@define()
class AggregationExpression(LayoutNode):
    expr: AggregationSource


@define()
class ThemeDataColor(LayoutNode):
    ColorId: int
    Percent: float


@define()
class ThemeExpression(LayoutNode):
    ThemeDataColor: ThemeDataColor


@define()
class FillRule(LayoutNode):
    FillRule: "Expression"
    Input: Source


@define()
class FillRuleExpression(LayoutNode):
    FillRule: FillRule


@define()
class ConditionalCase(LayoutNode):
    Condition: ConditionType
    Value: LiteralSource


@define()
class ConditionalSource(LayoutNode):
    @define()
    class _ConditionalSourceHelper(LayoutNode):
        Cases: list[ConditionalCase]

    Conditional: _ConditionalSourceHelper


@define()
class ConditionalExpression(LayoutNode):
    expr: ConditionalSource


ColorSubExpression = (
    ThemeExpression | LiteralSource | MeasureSource | FillRuleExpression | AggregationSource | ConditionalSource
)


@converter.register_structure_hook
def get_color_sub_expression_type(v: dict[str, Any], _: type | None = None) -> ColorSubExpression:
    keys = list(v.keys())
    assert len(keys) == 1, f"Expected single key, got {keys}"
    mapper = {
        "ThemeDataColor": ThemeExpression,
        "Aggregation": AggregationSource,
        "Literal": LiteralSource,
        "Measure": MeasureSource,
        "FillRule": FillRuleExpression,
        "Conditional": ConditionalSource,
    }
    if keys[0] in mapper:
        return mapper[keys[0]].model_validate(v)
    msg = f"Unknown type: {v.keys()}"
    raise TypeError(msg)


@converter.register_unstructure_hook
def unparse_color_sub_expression_type(v: ColorSubExpression) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class ColorExpression(LayoutNode):
    expr: ColorSubExpression


Color = ColorExpression | LiteralSource


@converter.register_structure_hook
def get_color_type(v: dict[str, Any], _: type | None = None) -> Color:
    if "expr" in v:
        return ColorExpression.model_validate(v)
    if "Literal" in v:
        return LiteralSource.model_validate(v)
    msg = f"Unknown Color Type: {v.keys()}"
    raise TypeError(msg)


@converter.register_unstructure_hook
def unparse_color_type(v: Color) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class SolidExpression(LayoutNode):
    color: Color
    value: LiteralSource | LiteralExpression | None = None  # TODO: explore the cases here more


@define()
class SolidColorExpression(LayoutNode):
    solid: SolidExpression

    @staticmethod
    def from_hex(color: str) -> "SolidColorExpression":
        return SolidColorExpression(
            solid=SolidExpression(
                color=ColorExpression(
                    expr=LiteralSource.new(color),
                ),
            ),
        )


@define()
class StrategyExpression(LayoutNode):
    strategy: LiteralExpression | LiteralSource  # TODO: explore the cases here more


@define()
class ExtremeColor(LayoutNode):
    color: LiteralSource
    value: LiteralSource


LinearGradient2HelperExtreme = SolidExpression | ExtremeColor


@converter.register_structure_hook
def get_linear_gradient_type(v: dict[str, Any], _: type | None = None) -> LinearGradient2HelperExtreme:
    if "solid" in v:
        return SolidExpression.model_validate(v)
    if "color" in v:
        return ExtremeColor.model_validate(v)
    msg = f"Unknown class: {v.keys()}"
    breakpoint()
    raise TypeError(msg)


@converter.register_unstructure_hook
def unparse_linear_gradient_type(v: LinearGradient2HelperExtreme) -> dict[str, Any]:
    return converter.unstructure(v)


@define()
class LinearGradient2Helper(LayoutNode):
    max: SolidExpression
    min: SolidExpression
    nullColoringStrategy: StrategyExpression


@define()
class LinearGradient2Expression(LayoutNode):
    linearGradient2: LinearGradient2Helper


@define()
class LinearGradient3Helper(LayoutNode):
    max: SolidExpression
    mid: SolidExpression
    min: SolidExpression
    nullColoringStrategy: StrategyExpression


@define()
class LinearGradient3Expression(LayoutNode):
    linearGradient3: LinearGradient3Helper


@define()
class ResourcePackageItem(LayoutNode):
    PackageName: str
    PackageType: int  # TODO: enum
    ItemName: str


@define()
class ResourcePackageAccessExpression(LayoutNode):
    ResourcePackageItem: ResourcePackageItem


@define()
class ResourcePackageAccess(LayoutNode):
    expr: ResourcePackageAccessExpression


@define()
class ImageKindExpression(LayoutNode):
    kind: Literal["Icon"]
    layout: LiteralExpression
    verticalAlignment: LiteralExpression
    value: ConditionalExpression


# TODO: centralize the expr: Source classes
@define()
class SelectRefExpression(LayoutNode):
    expr: SelectRef


@define()
class ImageExpression(LayoutNode):
    class _ImageExpressionHelper(LayoutNode):
        name: "Expression"
        scaling: "Expression"
        url: "Expression"

    image: _ImageExpressionHelper


@define()
class GeoJsonExpression(LayoutNode):
    class _GeoJsonExpressionHelper(LayoutNode):
        name: "Expression"
        content: "Expression"
        type: "Expression"

    geoJson: _GeoJsonExpressionHelper


@define()
class AlgorithmParameter(LiteralSource):
    Name: str


@define()
class AlgorithmExpression(LayoutNode):
    algorithm: str
    parameters: list[AlgorithmParameter]


@define()
class ExpressionList(LayoutNode):
    exprs: list["Expression"]
    kind: Literal["ExprList"]


@define()
class ColumnExpression(LayoutNode):
    expr: ColumnSource


Expression = (
    LiteralExpression
    | AlgorithmExpression
    | ColumnExpression
    | MeasureExpression
    | AggregationExpression
    | SolidColorExpression
    | LinearGradient2Expression
    | LinearGradient3Expression
    | ResourcePackageAccess
    | ImageKindExpression
    | ImageExpression
    | ExpressionList
    | GeoJsonExpression
    | SelectRefExpression
)


@converter.register_structure_hook
def get_expression_type(v: dict[str, Any], _: type | None = None) -> Expression:
    mapper: dict[str, type[Expression]] = {
        "solid": SolidColorExpression,
        "linearGradient2": LinearGradient2Expression,
        "linearGradient3": LinearGradient3Expression,
        "image": ImageExpression,
        "geoJson": GeoJsonExpression,
        "algorithm": AlgorithmExpression,
    }
    kind_mapper: dict[str, type[Expression]] = {
        "Icon": ImageKindExpression,
        "ExprList": ExpressionList,
    }
    expr_mapper: dict[str, type[Expression]] = {
        "Column": ColumnExpression,
        "Measure": MeasureExpression,
        "Literal": LiteralExpression,
        "Aggregation": AggregationExpression,
        "ResourcePackageItem": ResourcePackageAccess,
        "SelectRef": SelectRefExpression,
    }
    if "kind" in v:
        if v["kind"] in kind_mapper:
            return kind_mapper[v["kind"]].model_validate(v)
        msg = f"Unknown kind: {v['kind']}"
        raise ValueError(msg)

    if "expr" in v:
        # Column has multiple keys, so we need to check them
        for k in v["expr"]:
            if k in expr_mapper:
                return expr_mapper[k].model_validate(v)
    for key in v:
        if key in mapper:
            return mapper[key].model_validate(v)

    msg = f"Unknown expression type: {v['expr']}"
    raise ValueError(msg)


@converter.register_unstructure_hook
def unparse_expression_type(v: Expression) -> dict[str, Any]:
    return converter.unstructure(v)
