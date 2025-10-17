```mermaid
---
title: SelectRefExpression
---
graph 
ExpressionName[ExpressionName]
SelectRef[SelectRef]
SelectRefExpression[<a href='/layout/erd/SelectRefExpression'>SelectRefExpression</a>]
SelectRefExpression --->|expr| SelectRef
SelectRef --->|SelectRef| ExpressionName
```