# Layout JSON

The layout JSON file defines the structure and arrangement of visual elements within a report. Below is a description of its primary elements and their purpose.

## Primary Elements

### 1. Sections
- **Purpose**: Represents individual pages or tabs within a Power BI report.
- **Key Properties**:
  - `name`: The name of the section.
  - `displayName`: The user-friendly name displayed in the report.
  - `visualContainers`: A collection of visual elements (charts, tables, etc.) contained within the section.

### 2. VisualContainers
- **Purpose**: Defines the individual visual elements within a section.
- **Key Properties**:
  - `x`, `y`: Coordinates specifying the position of the visual on the page.
  - `width`, `height`: Dimensions of the visual.
  - `config`: Configuration settings for the visual, including data bindings and formatting.

### 3. Filters
- **Purpose**: Specifies filters applied to the report or individual visuals.
- **Key Properties**:
  - `filterType`: The type of filter (e.g., basic, advanced).
  - `filterValues`: The values used for filtering.

### 4. Bookmarks
- **Purpose**: Represents saved states of the report, allowing users to switch between predefined views.
- **Key Properties**:
  - `name`: The name of the bookmark.
  - `displayName`: The user-friendly name displayed in the report.
  - `state`: The state of the report when the bookmark is applied.

### 5. Settings
- **Purpose**: Contains global settings for the report layout.
- **Key Properties**:
  - `theme`: The theme applied to the report.
  - `gridSettings`: Settings for the grid layout, including spacing and alignment.

