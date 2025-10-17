```mermaid
---
title: Filter
---
graph 
AggregationSource[<a href='/layout/erd/AggregationSource'>AggregationSource</a>]
style AggregationSource stroke:#ff0000,stroke-width:1px
ArithmeticSource[<a href='/layout/erd/ArithmeticSource'>ArithmeticSource</a>]
style ArithmeticSource stroke:#ff0000,stroke-width:1px
CachedDisplayNames[CachedDisplayNames]
ColumnSource[<a href='/layout/erd/ColumnSource'>ColumnSource</a>]
style ColumnSource stroke:#ff0000,stroke-width:1px
ExpressionName[ExpressionName]
Filter[<a href='/layout/erd/Filter'>Filter</a>]
FilterObjects[FilterObjects]
FilterProperties[<a href='/layout/erd/FilterProperties'>FilterProperties</a>]
style FilterProperties stroke:#ff0000,stroke-width:1px
FilterPropertiesContainer[FilterPropertiesContainer]
GroupSource[<a href='/layout/erd/GroupSource'>GroupSource</a>]
style GroupSource stroke:#ff0000,stroke-width:1px
HierarchyLevelSource[<a href='/layout/erd/HierarchyLevelSource'>HierarchyLevelSource</a>]
style HierarchyLevelSource stroke:#ff0000,stroke-width:1px
LiteralSource[<a href='/layout/erd/LiteralSource'>LiteralSource</a>]
style LiteralSource stroke:#ff0000,stroke-width:1px
MeasureSource[<a href='/layout/erd/MeasureSource'>MeasureSource</a>]
style MeasureSource stroke:#ff0000,stroke-width:1px
ProtoSource[ProtoSource]
ProtoSourceRef[ProtoSourceRef]
PrototypeQuery[<a href='/layout/erd/PrototypeQuery'>PrototypeQuery</a>]
style PrototypeQuery stroke:#ff0000,stroke-width:1px
RoleRef[RoleRef]
Scope[<a href='/layout/erd/Scope'>Scope</a>]
style Scope stroke:#ff0000,stroke-width:1px
SelectRef[SelectRef]
TransformOutputRoleRef[TransformOutputRoleRef]
Filter ---> ColumnSource
FilterPropertiesContainer ---> FilterProperties
Filter ---> MeasureSource
Filter --->|expression| ProtoSourceRef
Filter ---> HierarchyLevelSource
ProtoSourceRef --->|SourceRef| ProtoSource
CachedDisplayNames ---> Scope
Filter ---> AggregationSource
Filter --->|objects| FilterObjects
Filter ---> GroupSource
TransformOutputRoleRef --->|TransformOutputRoleRef| RoleRef
Filter ---> ArithmeticSource
Filter ---> LiteralSource
Filter --->|expression| TransformOutputRoleRef
Filter --->|cachedDisplayNames| CachedDisplayNames
SelectRef --->|SelectRef| ExpressionName
Filter --->|expression| SelectRef
FilterObjects --->|general| FilterPropertiesContainer
Filter ---> PrototypeQuery
```