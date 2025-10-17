```mermaid
---
title: ResourcePackageAccess
---
graph 
ResourcePackageAccess[<a href='/layout/erd/ResourcePackageAccess'>ResourcePackageAccess</a>]
ResourcePackageAccessExpression[ResourcePackageAccessExpression]
ResourcePackageItem[ResourcePackageItem]
ResourcePackageAccess --->|expr| ResourcePackageAccessExpression
ResourcePackageAccessExpression --->|ResourcePackageItem| ResourcePackageItem
```