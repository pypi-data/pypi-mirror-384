```mermaid
---
title: PrototypeQuery
---
graph 
AggregationSource[<a href='/layout/erd/AggregationSource'>AggregationSource</a>]
style AggregationSource stroke:#ff0000,stroke-width:1px
ArithmeticSource[<a href='/layout/erd/ArithmeticSource'>ArithmeticSource</a>]
style ArithmeticSource stroke:#ff0000,stroke-width:1px
ColumnSource[<a href='/layout/erd/ColumnSource'>ColumnSource</a>]
style ColumnSource stroke:#ff0000,stroke-width:1px
Condition[<a href='/layout/erd/Condition'>Condition</a>]
style Condition stroke:#ff0000,stroke-width:1px
ExpressionName[ExpressionName]
GroupSource[<a href='/layout/erd/GroupSource'>GroupSource</a>]
style GroupSource stroke:#ff0000,stroke-width:1px
HierarchyLevelSource[<a href='/layout/erd/HierarchyLevelSource'>HierarchyLevelSource</a>]
style HierarchyLevelSource stroke:#ff0000,stroke-width:1px
LiteralSource[<a href='/layout/erd/LiteralSource'>LiteralSource</a>]
style LiteralSource stroke:#ff0000,stroke-width:1px
MeasureSource[<a href='/layout/erd/MeasureSource'>MeasureSource</a>]
style MeasureSource stroke:#ff0000,stroke-width:1px
Orderby[Orderby]
ProtoSource[ProtoSource]
ProtoSourceRef[ProtoSourceRef]
PrototypeQuery[<a href='/layout/erd/PrototypeQuery'>PrototypeQuery</a>]
RoleRef[RoleRef]
SelectRef[SelectRef]
TransformMeta[<a href='/layout/erd/TransformMeta'>TransformMeta</a>]
style TransformMeta stroke:#ff0000,stroke-width:1px
TransformOutputRoleRef[TransformOutputRoleRef]
PrototypeQuery ---> Condition
Orderby ---> AggregationSource
PrototypeQuery ---> AggregationSource
PrototypeQuery ---> MeasureSource
ProtoSourceRef --->|SourceRef| ProtoSource
PrototypeQuery --->|OrderBy| Orderby
PrototypeQuery --->|Select| ProtoSourceRef
Orderby --->|Expression| TransformOutputRoleRef
TransformOutputRoleRef --->|TransformOutputRoleRef| RoleRef
PrototypeQuery --->|Select| SelectRef
Orderby ---> HierarchyLevelSource
PrototypeQuery ---> GroupSource
Orderby ---> ColumnSource
Orderby ---> LiteralSource
Orderby ---> MeasureSource
SelectRef --->|SelectRef| ExpressionName
PrototypeQuery ---> LiteralSource
PrototypeQuery --->|Select| TransformOutputRoleRef
Orderby ---> ArithmeticSource
Orderby --->|Expression| ProtoSourceRef
PrototypeQuery ---> ColumnSource
PrototypeQuery ---> HierarchyLevelSource
Orderby --->|Expression| SelectRef
PrototypeQuery ---> TransformMeta
PrototypeQuery ---> ArithmeticSource
Orderby ---> GroupSource
```