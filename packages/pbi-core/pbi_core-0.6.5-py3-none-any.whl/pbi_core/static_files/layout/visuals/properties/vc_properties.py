from attrs import field

from pbi_core.attrs import define
from pbi_core.static_files.layout._base_node import LayoutNode

from .base import Expression


@define()
class BackgroundProperties(LayoutNode):
    @define()
    class _BackgroundPropertiesHelper(LayoutNode):
        color: Expression | None = None
        show: Expression | None = None
        transparency: Expression | None = None

    properties: _BackgroundPropertiesHelper = field(factory=_BackgroundPropertiesHelper)


@define()
class BorderProperties(LayoutNode):
    @define()
    class _BorderPropertiesHelper(LayoutNode):
        background: Expression | None = None
        color: Expression | None = None
        radius: Expression | None = None
        show: Expression | None = None
        width: Expression | None = None

    properties: _BorderPropertiesHelper = field(factory=_BorderPropertiesHelper)


@define()
class DividerProperties(LayoutNode):
    @define()
    class _DividerPropertiesHelper(LayoutNode):
        color: Expression | None = None
        show: Expression | None = None
        style: Expression | None = None
        width: Expression | None = None

    properties: _DividerPropertiesHelper = field(factory=_DividerPropertiesHelper)


@define()
class DropShadowProperties(LayoutNode):
    @define()
    class _DropShadowPropertiesHelper(LayoutNode):
        angle: Expression | None = None
        color: Expression | None = None
        position: Expression | None = None
        preset: Expression | None = None
        shadowBlur: Expression | None = None
        shadowDistance: Expression | None = None
        shadowSpread: Expression | None = None
        show: Expression | None = None
        transparency: Expression | None = None

    properties: _DropShadowPropertiesHelper = field(factory=_DropShadowPropertiesHelper)


@define()
class GeneralProperties(LayoutNode):
    @define()
    class _GeneralPropertiesHelper(LayoutNode):
        altText: Expression | None = None
        keepLayerOrder: Expression | None = None

    properties: _GeneralPropertiesHelper = field(factory=_GeneralPropertiesHelper)


@define()
class LockAspectProperties(LayoutNode):
    @define()
    class _LockAspectPropertiesHelper(LayoutNode):
        show: Expression | None = None

    properties: _LockAspectPropertiesHelper = field(factory=_LockAspectPropertiesHelper)


@define()
class SpacingProperties(LayoutNode):
    @define()
    class _SpacingPropertiesHelper(LayoutNode):
        customizeSpacing: Expression | None = None
        spaceBelowSubTitle: Expression | None = None
        spaceBelowTitle: Expression | None = None
        spaceBelowTitleArea: Expression | None = None

    properties: _SpacingPropertiesHelper = field(factory=_SpacingPropertiesHelper)


@define()
class StylePresetProperties(LayoutNode):
    @define()
    class _StylePresetPropertiesHelper(LayoutNode):
        name: Expression | None = None

    properties: _StylePresetPropertiesHelper = field(factory=_StylePresetPropertiesHelper)


@define()
class SubTitleProperties(LayoutNode):
    @define()
    class _SubTitlePropertiesHelper(LayoutNode):
        alignment: Expression | None = None
        bold: Expression | None = None
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        heading: Expression | None = None
        show: Expression | None = None
        text: Expression | None = None
        titleWrap: Expression | None = None

    properties: _SubTitlePropertiesHelper = field(factory=_SubTitlePropertiesHelper)


@define()
class TitleProperties(LayoutNode):
    @define()
    class _TitlePropertiesHelper(LayoutNode):
        alignment: Expression | None = None
        background: Expression | None = None
        fontColor: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        heading: Expression | None = None
        show: Expression | None = None
        text: Expression | None = None
        titleWrap: Expression | None = None
        underline: Expression | None = None

    properties: _TitlePropertiesHelper = field(factory=_TitlePropertiesHelper)


@define()
class VisualHeaderProperties(LayoutNode):
    @define()
    class _VisualHeaderPropertiesHelper(LayoutNode):
        background: Expression | None = None
        border: Expression | None = None
        foreground: Expression | None = None
        show: Expression | None = None
        showDrillDownExpandButton: Expression | None = None
        showDrillDownLevelButton: Expression | None = None
        showDrillRoleSelector: Expression | None = None
        showDrillToggleButton: Expression | None = None
        showDrillUpButton: Expression | None = None
        showFilterRestatementButton: Expression | None = None
        showFocusModeButton: Expression | None = None
        showOptionsMenu: Expression | None = None
        showPinButton: Expression | None = None
        showSeeDataLayoutToggleButton: Expression | None = None
        showSmartNarrativeButton: Expression | None = None
        showTooltipButton: Expression | None = None
        showVisualErrorButton: Expression | None = None
        showVisualInformationButton: Expression | None = None
        showVisualWarningButton: Expression | None = None
        transparency: Expression | None = None

    properties: _VisualHeaderPropertiesHelper = field(factory=_VisualHeaderPropertiesHelper)


@define()
class VisualHeaderTooltipProperties(LayoutNode):
    @define()
    class _VisualHeaderTooltipPropertiesHelper(LayoutNode):
        background: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        section: Expression | None = None
        text: Expression | None = None
        themedBackground: Expression | None = None
        themedTitleFontColor: Expression | None = None
        titleFontColor: Expression | None = None
        transparency: Expression | None = None
        type: Expression | None = None
        underline: Expression | None = None

    properties: _VisualHeaderTooltipPropertiesHelper = field(factory=_VisualHeaderTooltipPropertiesHelper)


@define()
class VisualLinkProperties(LayoutNode):
    @define()
    class _VisualLinkPropertiesHelper(LayoutNode):
        bookmark: Expression | None = None
        disabledTooltip: Expression | None = None
        drillthroughSection: Expression | None = None
        enabledTooltip: Expression | None = None
        navigationSection: Expression | None = None
        show: Expression | None = None
        tooltip: Expression | None = None
        type: Expression | None = None
        webUrl: Expression | None = None

    properties: _VisualLinkPropertiesHelper = field(factory=_VisualLinkPropertiesHelper)


@define()
class VisualTooltipProperties(LayoutNode):
    @define()
    class _VisualTooltipPropertiesHelper(LayoutNode):
        background: Expression | None = None
        fontFamily: Expression | None = None
        fontSize: Expression | None = None
        section: Expression | None = None
        show: Expression | None = None
        titleFontColor: Expression | None = None
        type: Expression | None = None
        valueFontColor: Expression | None = None

    properties: _VisualTooltipPropertiesHelper = field(factory=_VisualTooltipPropertiesHelper)


@define()
class VCProperties(LayoutNode):
    background: list[BackgroundProperties] | None = field(factory=lambda: [BackgroundProperties()])
    border: list[BorderProperties] | None = field(factory=lambda: [BorderProperties()])
    divider: list[DividerProperties] | None = field(factory=lambda: [DividerProperties()])
    dropShadow: list[DropShadowProperties] | None = field(factory=lambda: [DropShadowProperties()])
    general: list[GeneralProperties] | None = field(factory=lambda: [GeneralProperties()])
    lockAspect: list[LockAspectProperties] | None = field(factory=lambda: [LockAspectProperties()])
    spacing: list[SpacingProperties] | None = field(factory=lambda: [SpacingProperties()])
    stylePreset: list[StylePresetProperties] | None = field(factory=lambda: [StylePresetProperties()])
    subTitle: list[SubTitleProperties] | None = field(factory=lambda: [SubTitleProperties()])
    title: list[TitleProperties] | None = field(factory=lambda: [TitleProperties()])
    visualHeader: list[VisualHeaderProperties] | None = field(factory=lambda: [VisualHeaderProperties()])
    visualHeaderTooltip: list[VisualHeaderTooltipProperties] | None = field(
        factory=lambda: [VisualHeaderTooltipProperties()],
    )
    visualLink: list[VisualLinkProperties] | None = field(factory=lambda: [VisualLinkProperties()])
    visualTooltip: list[VisualTooltipProperties] | None = field(factory=lambda: [VisualTooltipProperties()])
