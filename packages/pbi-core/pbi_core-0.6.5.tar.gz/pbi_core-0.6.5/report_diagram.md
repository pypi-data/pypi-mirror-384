```mermaid
---
title: Report Hierarchy
---
graph 
BaseStaticReport ---> BaseReport
BaseReport ---> LocalReport
BaseSsasReport ---> BaseReport
BaseStaticReport ---> LocalStaticReport
BaseSsasReport ---> LocalSsasReport
LocalStaticReport ---> LocalReport
LocalSsasReport ---> LocalReport

```