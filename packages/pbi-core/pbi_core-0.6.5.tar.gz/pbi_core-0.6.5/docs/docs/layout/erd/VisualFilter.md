```mermaid
---
title: VisualFilter
---
graph 
AggregationSource[<a href='/layout/erd/AggregationSource'>AggregationSource</a>]
style AggregationSource stroke:#ff0000,stroke-width:1px
AndCondition[<a href='/layout/erd/AndCondition'>AndCondition</a>]
style AndCondition stroke:#ff0000,stroke-width:1px
ArithmeticSource[<a href='/layout/erd/ArithmeticSource'>ArithmeticSource</a>]
style ArithmeticSource stroke:#ff0000,stroke-width:1px
CachedDisplayNames[CachedDisplayNames]
CachedValueItems[CachedValueItems]
ColumnSource[<a href='/layout/erd/ColumnSource'>ColumnSource</a>]
style ColumnSource stroke:#ff0000,stroke-width:1px
ComparisonCondition[<a href='/layout/erd/ComparisonCondition'>ComparisonCondition</a>]
style ComparisonCondition stroke:#ff0000,stroke-width:1px
ContainsCondition[<a href='/layout/erd/ContainsCondition'>ContainsCondition</a>]
style ContainsCondition stroke:#ff0000,stroke-width:1px
DecomposedFilterExpressionMetadata[DecomposedFilterExpressionMetadata]
DecomposedIdentities[DecomposedIdentities]
ExistsCondition[<a href='/layout/erd/ExistsCondition'>ExistsCondition</a>]
style ExistsCondition stroke:#ff0000,stroke-width:1px
ExpressionName[ExpressionName]
FilterExpressionMetadata[FilterExpressionMetadata]
FilterObjects[FilterObjects]
FilterProperties[<a href='/layout/erd/FilterProperties'>FilterProperties</a>]
style FilterProperties stroke:#ff0000,stroke-width:1px
FilterPropertiesContainer[FilterPropertiesContainer]
GroupSource[<a href='/layout/erd/GroupSource'>GroupSource</a>]
style GroupSource stroke:#ff0000,stroke-width:1px
HierarchyLevelSource[<a href='/layout/erd/HierarchyLevelSource'>HierarchyLevelSource</a>]
style HierarchyLevelSource stroke:#ff0000,stroke-width:1px
HighlightScope[HighlightScope]
InCondition[<a href='/layout/erd/InCondition'>InCondition</a>]
style InCondition stroke:#ff0000,stroke-width:1px
JsonFilter[JsonFilter]
LiteralSource[<a href='/layout/erd/LiteralSource'>LiteralSource</a>]
style LiteralSource stroke:#ff0000,stroke-width:1px
MeasureSource[<a href='/layout/erd/MeasureSource'>MeasureSource</a>]
style MeasureSource stroke:#ff0000,stroke-width:1px
NotCondition[<a href='/layout/erd/NotCondition'>NotCondition</a>]
style NotCondition stroke:#ff0000,stroke-width:1px
OrCondition[<a href='/layout/erd/OrCondition'>OrCondition</a>]
style OrCondition stroke:#ff0000,stroke-width:1px
ProtoSource[ProtoSource]
ProtoSourceRef[ProtoSourceRef]
PrototypeQuery[<a href='/layout/erd/PrototypeQuery'>PrototypeQuery</a>]
style PrototypeQuery stroke:#ff0000,stroke-width:1px
RoleRef[RoleRef]
Scope[<a href='/layout/erd/Scope'>Scope</a>]
style Scope stroke:#ff0000,stroke-width:1px
SelectRef[SelectRef]
TransformOutputRoleRef[TransformOutputRoleRef]
VisualFilter[<a href='/layout/erd/VisualFilter'>VisualFilter</a>]
HighlightScope ---> ContainsCondition
HighlightScope ---> OrCondition
FilterPropertiesContainer ---> FilterProperties
VisualFilter ---> PrototypeQuery
VisualFilter --->|cachedDisplayNames| CachedDisplayNames
FilterExpressionMetadata --->|expressions| ProtoSourceRef
DecomposedFilterExpressionMetadata --->|decomposedIdentities| DecomposedIdentities
VisualFilter ---> ColumnSource
HighlightScope ---> ExistsCondition
FilterExpressionMetadata --->|expressions| TransformOutputRoleRef
DecomposedFilterExpressionMetadata ---> ArithmeticSource
DecomposedFilterExpressionMetadata ---> GroupSource
FilterExpressionMetadata ---> ArithmeticSource
HighlightScope ---> NotCondition
DecomposedIdentities ---> GroupSource
CachedValueItems --->|identities| HighlightScope
ProtoSourceRef --->|SourceRef| ProtoSource
DecomposedIdentities ---> ArithmeticSource
VisualFilter ---> HierarchyLevelSource
CachedDisplayNames ---> Scope
VisualFilter --->|expression| SelectRef
VisualFilter --->|filterExpressionMetadata| DecomposedFilterExpressionMetadata
DecomposedFilterExpressionMetadata --->|jsonFilter| JsonFilter
FilterExpressionMetadata ---> ColumnSource
DecomposedIdentities --->|values| SelectRef
DecomposedIdentities ---> AggregationSource
TransformOutputRoleRef --->|TransformOutputRoleRef| RoleRef
VisualFilter ---> MeasureSource
HighlightScope ---> AndCondition
FilterExpressionMetadata --->|cachedValueItems| CachedValueItems
DecomposedFilterExpressionMetadata --->|expressions| SelectRef
VisualFilter --->|filterExpressionMetadata| FilterExpressionMetadata
DecomposedFilterExpressionMetadata ---> LiteralSource
VisualFilter ---> ArithmeticSource
DecomposedIdentities ---> ColumnSource
HighlightScope ---> ComparisonCondition
FilterExpressionMetadata ---> LiteralSource
DecomposedFilterExpressionMetadata ---> HierarchyLevelSource
DecomposedIdentities ---> LiteralSource
DecomposedFilterExpressionMetadata ---> MeasureSource
VisualFilter ---> LiteralSource
VisualFilter ---> AggregationSource
VisualFilter --->|expression| TransformOutputRoleRef
VisualFilter --->|expression| ProtoSourceRef
VisualFilter --->|objects| FilterObjects
FilterExpressionMetadata --->|expressions| SelectRef
SelectRef --->|SelectRef| ExpressionName
FilterExpressionMetadata ---> HierarchyLevelSource
DecomposedIdentities ---> MeasureSource
DecomposedFilterExpressionMetadata ---> ColumnSource
DecomposedIdentities ---> HierarchyLevelSource
FilterExpressionMetadata ---> GroupSource
FilterExpressionMetadata ---> MeasureSource
HighlightScope ---> InCondition
FilterExpressionMetadata ---> AggregationSource
VisualFilter ---> GroupSource
DecomposedFilterExpressionMetadata --->|expressions| ProtoSourceRef
DecomposedFilterExpressionMetadata --->|expressions| TransformOutputRoleRef
FilterObjects --->|general| FilterPropertiesContainer
DecomposedIdentities --->|values| TransformOutputRoleRef
DecomposedIdentities --->|values| ProtoSourceRef
DecomposedFilterExpressionMetadata ---> AggregationSource
```