# Overview of SSAS and Power BI Integration

SSAS is the Query Engine behind Power BI. It is responsible for storing the data model, executing DAX queries, and returning the results to Power BI visuals. Each SSAS database also contains metadata tables about the data, measures, columns, tables, etc. in the data model. This metadata is used by Power BI to populate the Fields pane and to provide IntelliSense for DAX queries.

# Unmapped Tables

There are some metadata tables in SSAS that are not currently mapped in the pbi_core library. These tables are not commonly used in Power BI reports, but they may be useful for advanced scenarios. The following is a list of unmapped tables in SSAS. If you submit a `pbix` file that contains any of these tables, please open an issue on the [pbi_core GitHub repository](https://github.com/douglassimonsen/pbi_core/issues).

Unmapped Tables:

-   alternate_of[Alternate Of]
-   annotations[Annotations]
-   calculation_group[Calculation Group]
-   calculation_item[Calculation Item]
-   data_source[Data Source]
-   detail_row_definition[Detail Row Definition]
-   extended_property[Extended Property]
-   format_string_definition[Format String Definition]
-   object_translation[Object Translation]
-   perspective_column[Perspective Column]
-   perspective_hierarchy[Perspective Hierarchy]
-   perspective_measure[Perspective Measure]
-   perspective_set[Perspective Set]
-   perspective_table[Perspective Table]
-   perspective[Perspective]
-   refresh_policy[Refresh Policy]
-   related_column_detail[Related Column Detail]
-   set[Set]