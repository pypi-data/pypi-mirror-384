```mermaid
---
title: ResourcePackage
---
graph 
ResourcePackage[<a href='/layout/erd/ResourcePackage'>ResourcePackage</a>]
ResourcePackageDetails[ResourcePackageDetails]
ResourcePackageItem[ResourcePackageItem]
ResourcePackageDetails --->|items| ResourcePackageItem
ResourcePackage --->|resourcePackage| ResourcePackageDetails
```