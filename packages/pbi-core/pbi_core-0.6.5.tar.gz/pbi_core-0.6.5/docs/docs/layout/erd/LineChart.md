```mermaid
---
title: LineChart
---
graph 
AggregationExpression[<a href='/layout/erd/AggregationExpression'>AggregationExpression</a>]
style AggregationExpression stroke:#ff0000,stroke-width:1px
AlgorithmExpression[<a href='/layout/erd/AlgorithmExpression'>AlgorithmExpression</a>]
style AlgorithmExpression stroke:#ff0000,stroke-width:1px
AnomalyDetectionProperties[AnomalyDetectionProperties]
CategoryAxisProperties[CategoryAxisProperties]
ColumnExpression[<a href='/layout/erd/ColumnExpression'>ColumnExpression</a>]
style ColumnExpression stroke:#ff0000,stroke-width:1px
ColumnProperty[<a href='/layout/erd/ColumnProperty'>ColumnProperty</a>]
style ColumnProperty stroke:#ff0000,stroke-width:1px
DataPointProperties[DataPointProperties]
Display[Display]
ExpressionList[ExpressionList]
ForecastProperties[ForecastProperties]
GeneralProperties[GeneralProperties]
GeoJsonExpression[<a href='/layout/erd/GeoJsonExpression'>GeoJsonExpression</a>]
style GeoJsonExpression stroke:#ff0000,stroke-width:1px
ImageExpression[<a href='/layout/erd/ImageExpression'>ImageExpression</a>]
style ImageExpression stroke:#ff0000,stroke-width:1px
ImageKindExpression[<a href='/layout/erd/ImageKindExpression'>ImageKindExpression</a>]
style ImageKindExpression stroke:#ff0000,stroke-width:1px
LabelsProperties[LabelsProperties]
LegendProperties[LegendProperties]
LineChart[<a href='/layout/erd/LineChart'>LineChart</a>]
LineChartProperties[LineChartProperties]
LineStylesProperties[LineStylesProperties]
LinearGradient2Expression[<a href='/layout/erd/LinearGradient2Expression'>LinearGradient2Expression</a>]
style LinearGradient2Expression stroke:#ff0000,stroke-width:1px
LinearGradient3Expression[<a href='/layout/erd/LinearGradient3Expression'>LinearGradient3Expression</a>]
style LinearGradient3Expression stroke:#ff0000,stroke-width:1px
LiteralExpression[<a href='/layout/erd/LiteralExpression'>LiteralExpression</a>]
style LiteralExpression stroke:#ff0000,stroke-width:1px
MeasureExpression[<a href='/layout/erd/MeasureExpression'>MeasureExpression</a>]
style MeasureExpression stroke:#ff0000,stroke-width:1px
PlotAreaProperties[PlotAreaProperties]
ProjectionConfig[ProjectionConfig]
PrototypeQuery[<a href='/layout/erd/PrototypeQuery'>PrototypeQuery</a>]
style PrototypeQuery stroke:#ff0000,stroke-width:1px
QueryOptions[QueryOptions]
ResourcePackageAccess[<a href='/layout/erd/ResourcePackageAccess'>ResourcePackageAccess</a>]
style ResourcePackageAccess stroke:#ff0000,stroke-width:1px
SelectRefExpression[<a href='/layout/erd/SelectRefExpression'>SelectRefExpression</a>]
style SelectRefExpression stroke:#ff0000,stroke-width:1px
Selector[<a href='/layout/erd/Selector'>Selector</a>]
style Selector stroke:#ff0000,stroke-width:1px
SolidColorExpression[<a href='/layout/erd/SolidColorExpression'>SolidColorExpression</a>]
style SolidColorExpression stroke:#ff0000,stroke-width:1px
TrendProperties[TrendProperties]
VCProperties[<a href='/layout/erd/VCProperties'>VCProperties</a>]
style VCProperties stroke:#ff0000,stroke-width:1px
ValueAxisProperties[ValueAxisProperties]
Y1AxisReferenceLineProperties[Y1AxisReferenceLineProperties]
Y2AxisProperties[Y2AxisProperties]
ZoomProperties[ZoomProperties]
_AnomalyDetectionPropertiesHelper[_AnomalyDetectionPropertiesHelper]
_CategoryAxisPropertiesHelper[_CategoryAxisPropertiesHelper]
_DataPointPropertiesHelper[_DataPointPropertiesHelper]
_ForecastPropertiesHelper[_ForecastPropertiesHelper]
_GeneralPropertiesHelper[_GeneralPropertiesHelper]
_LabelsPropertiesHelper[_LabelsPropertiesHelper]
_LegendPropertiesHelper[_LegendPropertiesHelper]
_LineStylesPropertiesHelper[_LineStylesPropertiesHelper]
_PlotAreaPropertiesHelper[_PlotAreaPropertiesHelper]
_TrendPropertiesHelper[_TrendPropertiesHelper]
_ValueAxisPropertiesHelper[_ValueAxisPropertiesHelper]
_Y1AxisReferenceLinePropertiesHelper[_Y1AxisReferenceLinePropertiesHelper]
_Y2AxisPropertiesHelper[_Y2AxisPropertiesHelper]
_ZoomPropertiesHelper[_ZoomPropertiesHelper]
LineChartProperties --->|dataPoint| DataPointProperties
_LineStylesPropertiesHelper ---> ResourcePackageAccess
LineChartProperties --->|valueAxis| ValueAxisProperties
_LineStylesPropertiesHelper ---> LiteralExpression
_ZoomPropertiesHelper ---> SolidColorExpression
_ForecastPropertiesHelper ---> AlgorithmExpression
_TrendPropertiesHelper ---> AlgorithmExpression
_LineStylesPropertiesHelper ---> ImageKindExpression
_LegendPropertiesHelper ---> ColumnExpression
_LabelsPropertiesHelper ---> ColumnExpression
_Y1AxisReferenceLinePropertiesHelper ---> ColumnExpression
_LineStylesPropertiesHelper ---> ColumnExpression
_LabelsPropertiesHelper ---> MeasureExpression
_ForecastPropertiesHelper ---> LiteralExpression
_DataPointPropertiesHelper ---> ImageKindExpression
_Y1AxisReferenceLinePropertiesHelper ---> ImageExpression
_Y2AxisPropertiesHelper ---> AggregationExpression
ValueAxisProperties --->|properties| _ValueAxisPropertiesHelper
Y1AxisReferenceLineProperties --->|properties| _Y1AxisReferenceLinePropertiesHelper
LegendProperties --->|properties| _LegendPropertiesHelper
LineChartProperties --->|categoryAxis| CategoryAxisProperties
ForecastProperties ---> Selector
_Y2AxisPropertiesHelper ---> LinearGradient3Expression
LineStylesProperties --->|properties| _LineStylesPropertiesHelper
_LineStylesPropertiesHelper ---> GeoJsonExpression
_ValueAxisPropertiesHelper ---> LinearGradient3Expression
LineChartProperties --->|zoom| ZoomProperties
_Y1AxisReferenceLinePropertiesHelper ---> AggregationExpression
_LegendPropertiesHelper ---> SolidColorExpression
_CategoryAxisPropertiesHelper ---> SolidColorExpression
_ZoomPropertiesHelper ---> LinearGradient2Expression
_TrendPropertiesHelper ---> GeoJsonExpression
_LegendPropertiesHelper ---> ResourcePackageAccess
LineChartProperties --->|plotArea| PlotAreaProperties
_CategoryAxisPropertiesHelper ---> ColumnExpression
_LineStylesPropertiesHelper ---> SolidColorExpression
_CategoryAxisPropertiesHelper --->|axisStyle| ExpressionList
_LabelsPropertiesHelper ---> SelectRefExpression
_LineStylesPropertiesHelper --->|lineStyle| ExpressionList
_LineStylesPropertiesHelper ---> AggregationExpression
_GeneralPropertiesHelper ---> SolidColorExpression
_LabelsPropertiesHelper ---> SolidColorExpression
_CategoryAxisPropertiesHelper ---> AggregationExpression
LineChart --->|objects| LineChartProperties
_LineStylesPropertiesHelper ---> SelectRefExpression
_GeneralPropertiesHelper ---> LinearGradient3Expression
_LabelsPropertiesHelper ---> AggregationExpression
LineChart ---> PrototypeQuery
_Y1AxisReferenceLinePropertiesHelper ---> ImageKindExpression
_LabelsPropertiesHelper --->|backgroundColor| ExpressionList
_GeneralPropertiesHelper ---> MeasureExpression
_CategoryAxisPropertiesHelper ---> MeasureExpression
_TrendPropertiesHelper ---> AggregationExpression
_ForecastPropertiesHelper ---> MeasureExpression
_AnomalyDetectionPropertiesHelper --->|confidenceBandColor| ExpressionList
_PlotAreaPropertiesHelper ---> AlgorithmExpression
_Y1AxisReferenceLinePropertiesHelper ---> LinearGradient2Expression
Y1AxisReferenceLineProperties ---> Selector
_Y2AxisPropertiesHelper --->|show| ExpressionList
_ValueAxisPropertiesHelper ---> SelectRefExpression
Y2AxisProperties --->|properties| _Y2AxisPropertiesHelper
_AnomalyDetectionPropertiesHelper ---> AlgorithmExpression
_ForecastPropertiesHelper ---> GeoJsonExpression
_Y2AxisPropertiesHelper ---> SolidColorExpression
_ZoomPropertiesHelper ---> MeasureExpression
_ValueAxisPropertiesHelper ---> ImageKindExpression
_ForecastPropertiesHelper ---> ResourcePackageAccess
_PlotAreaPropertiesHelper ---> ResourcePackageAccess
_PlotAreaPropertiesHelper ---> ColumnExpression
_AnomalyDetectionPropertiesHelper ---> LinearGradient2Expression
_Y1AxisReferenceLinePropertiesHelper --->|displayName| ExpressionList
LineChartProperties --->|legend| LegendProperties
_CategoryAxisPropertiesHelper ---> SelectRefExpression
_ZoomPropertiesHelper ---> ImageKindExpression
AnomalyDetectionProperties ---> Selector
_Y2AxisPropertiesHelper ---> ImageExpression
DataPointProperties ---> Selector
_CategoryAxisPropertiesHelper ---> AlgorithmExpression
_GeneralPropertiesHelper ---> LiteralExpression
_Y2AxisPropertiesHelper ---> SelectRefExpression
_LegendPropertiesHelper ---> ImageExpression
_Y2AxisPropertiesHelper ---> MeasureExpression
_ForecastPropertiesHelper ---> ColumnExpression
LineChartProperties --->|y1AxisReferenceLine| Y1AxisReferenceLineProperties
_GeneralPropertiesHelper ---> ImageExpression
_Y1AxisReferenceLinePropertiesHelper ---> LinearGradient3Expression
_ForecastPropertiesHelper ---> AggregationExpression
_ZoomPropertiesHelper ---> ResourcePackageAccess
_ValueAxisPropertiesHelper ---> LinearGradient2Expression
_AnomalyDetectionPropertiesHelper ---> LiteralExpression
_GeneralPropertiesHelper ---> AlgorithmExpression
_Y1AxisReferenceLinePropertiesHelper ---> SelectRefExpression
LineChartProperties --->|forecast| ForecastProperties
_DataPointPropertiesHelper ---> ColumnExpression
ForecastProperties --->|properties| _ForecastPropertiesHelper
LineChart --->|display| Display
_LegendPropertiesHelper ---> ImageKindExpression
_AnomalyDetectionPropertiesHelper ---> SelectRefExpression
_TrendPropertiesHelper ---> SolidColorExpression
_Y1AxisReferenceLinePropertiesHelper ---> ResourcePackageAccess
_LabelsPropertiesHelper ---> LinearGradient2Expression
_ValueAxisPropertiesHelper --->|axisScale| ExpressionList
_TrendPropertiesHelper ---> LiteralExpression
_LineStylesPropertiesHelper ---> ImageExpression
_ValueAxisPropertiesHelper ---> AggregationExpression
_Y2AxisPropertiesHelper ---> ResourcePackageAccess
_GeneralPropertiesHelper ---> SelectRefExpression
_ZoomPropertiesHelper ---> ColumnExpression
_AnomalyDetectionPropertiesHelper ---> ResourcePackageAccess
_PlotAreaPropertiesHelper ---> LinearGradient2Expression
_LegendPropertiesHelper ---> LiteralExpression
LineChartProperties --->|trend| TrendProperties
_LineStylesPropertiesHelper ---> AlgorithmExpression
LineChartProperties --->|general| GeneralProperties
_DataPointPropertiesHelper ---> LinearGradient3Expression
_LabelsPropertiesHelper ---> ResourcePackageAccess
_DataPointPropertiesHelper ---> ResourcePackageAccess
_AnomalyDetectionPropertiesHelper ---> AggregationExpression
_LegendPropertiesHelper --->|fontSize| ExpressionList
_Y1AxisReferenceLinePropertiesHelper ---> GeoJsonExpression
_CategoryAxisPropertiesHelper ---> ResourcePackageAccess
LineChart --->|projections| ProjectionConfig
_LegendPropertiesHelper ---> GeoJsonExpression
_TrendPropertiesHelper ---> LinearGradient3Expression
_CategoryAxisPropertiesHelper ---> ImageKindExpression
_Y2AxisPropertiesHelper ---> AlgorithmExpression
_ForecastPropertiesHelper ---> SolidColorExpression
_GeneralPropertiesHelper ---> AggregationExpression
_LineStylesPropertiesHelper ---> LinearGradient2Expression
_GeneralPropertiesHelper ---> ImageKindExpression
_PlotAreaPropertiesHelper ---> ImageKindExpression
_LineStylesPropertiesHelper ---> MeasureExpression
_GeneralPropertiesHelper ---> GeoJsonExpression
_PlotAreaPropertiesHelper ---> SelectRefExpression
_PlotAreaPropertiesHelper --->|transparency| ExpressionList
_Y2AxisPropertiesHelper ---> GeoJsonExpression
_LabelsPropertiesHelper ---> GeoJsonExpression
_PlotAreaPropertiesHelper ---> LinearGradient3Expression
_CategoryAxisPropertiesHelper ---> LiteralExpression
AnomalyDetectionProperties --->|properties| _AnomalyDetectionPropertiesHelper
_ZoomPropertiesHelper ---> LinearGradient3Expression
_LegendPropertiesHelper ---> MeasureExpression
_DataPointPropertiesHelper ---> LinearGradient2Expression
_DataPointPropertiesHelper ---> AggregationExpression
_LabelsPropertiesHelper ---> LinearGradient3Expression
_ValueAxisPropertiesHelper ---> MeasureExpression
_GeneralPropertiesHelper ---> LinearGradient2Expression
LineChart ---> VCProperties
LabelsProperties --->|properties| _LabelsPropertiesHelper
_Y2AxisPropertiesHelper ---> ColumnExpression
_AnomalyDetectionPropertiesHelper ---> MeasureExpression
_PlotAreaPropertiesHelper ---> SolidColorExpression
_DataPointPropertiesHelper --->|borderColorMatchFill| ExpressionList
CategoryAxisProperties --->|properties| _CategoryAxisPropertiesHelper
_LabelsPropertiesHelper ---> LiteralExpression
_CategoryAxisPropertiesHelper ---> ImageExpression
_AnomalyDetectionPropertiesHelper ---> LinearGradient3Expression
_ValueAxisPropertiesHelper ---> LiteralExpression
_PlotAreaPropertiesHelper ---> ImageExpression
_DataPointPropertiesHelper ---> LiteralExpression
_ZoomPropertiesHelper ---> LiteralExpression
_TrendPropertiesHelper ---> MeasureExpression
_CategoryAxisPropertiesHelper ---> LinearGradient2Expression
ZoomProperties --->|properties| _ZoomPropertiesHelper
_ForecastPropertiesHelper ---> ImageExpression
_ValueAxisPropertiesHelper ---> SolidColorExpression
_ForecastPropertiesHelper ---> LinearGradient3Expression
_ForecastPropertiesHelper ---> LinearGradient2Expression
_ZoomPropertiesHelper ---> GeoJsonExpression
_GeneralPropertiesHelper --->|altText| ExpressionList
_DataPointPropertiesHelper ---> GeoJsonExpression
_TrendPropertiesHelper ---> SelectRefExpression
LineChartProperties --->|labels| LabelsProperties
_Y1AxisReferenceLinePropertiesHelper ---> LiteralExpression
_TrendPropertiesHelper ---> ResourcePackageAccess
PlotAreaProperties --->|properties| _PlotAreaPropertiesHelper
_LegendPropertiesHelper ---> SelectRefExpression
_PlotAreaPropertiesHelper ---> MeasureExpression
_DataPointPropertiesHelper ---> ImageExpression
_ZoomPropertiesHelper ---> AggregationExpression
_ForecastPropertiesHelper --->|show| ExpressionList
_ForecastPropertiesHelper ---> ImageKindExpression
_LegendPropertiesHelper ---> AlgorithmExpression
_LegendPropertiesHelper ---> LinearGradient3Expression
_DataPointPropertiesHelper ---> MeasureExpression
LineChartProperties --->|y2Axis| Y2AxisProperties
_LegendPropertiesHelper ---> LinearGradient2Expression
_ValueAxisPropertiesHelper ---> GeoJsonExpression
_GeneralPropertiesHelper ---> ColumnExpression
_PlotAreaPropertiesHelper ---> LiteralExpression
_TrendPropertiesHelper --->|displayName| ExpressionList
_DataPointPropertiesHelper ---> AlgorithmExpression
_AnomalyDetectionPropertiesHelper ---> GeoJsonExpression
_Y1AxisReferenceLinePropertiesHelper ---> AlgorithmExpression
_AnomalyDetectionPropertiesHelper ---> ColumnExpression
_CategoryAxisPropertiesHelper ---> LinearGradient3Expression
_AnomalyDetectionPropertiesHelper ---> ImageKindExpression
_ValueAxisPropertiesHelper ---> ColumnExpression
_ForecastPropertiesHelper ---> SelectRefExpression
_TrendPropertiesHelper ---> LinearGradient2Expression
_GeneralPropertiesHelper ---> ResourcePackageAccess
LineChartProperties --->|anomalyDetection| AnomalyDetectionProperties
_CategoryAxisPropertiesHelper ---> GeoJsonExpression
_ZoomPropertiesHelper --->|show| ExpressionList
_AnomalyDetectionPropertiesHelper ---> ImageExpression
_ValueAxisPropertiesHelper ---> AlgorithmExpression
_ValueAxisPropertiesHelper ---> ImageExpression
_LineStylesPropertiesHelper ---> LinearGradient3Expression
LineChartProperties --->|lineStyles| LineStylesProperties
_ZoomPropertiesHelper ---> SelectRefExpression
_LabelsPropertiesHelper ---> AlgorithmExpression
_ZoomPropertiesHelper ---> ImageExpression
_TrendPropertiesHelper ---> ColumnExpression
_LegendPropertiesHelper ---> AggregationExpression
_DataPointPropertiesHelper ---> SelectRefExpression
_TrendPropertiesHelper ---> ImageExpression
_ZoomPropertiesHelper ---> AlgorithmExpression
LineStylesProperties ---> Selector
DataPointProperties --->|properties| _DataPointPropertiesHelper
GeneralProperties --->|properties| _GeneralPropertiesHelper
_Y2AxisPropertiesHelper ---> LinearGradient2Expression
_DataPointPropertiesHelper ---> SolidColorExpression
_PlotAreaPropertiesHelper ---> GeoJsonExpression
_TrendPropertiesHelper ---> ImageKindExpression
_AnomalyDetectionPropertiesHelper ---> SolidColorExpression
_Y1AxisReferenceLinePropertiesHelper ---> MeasureExpression
_Y1AxisReferenceLinePropertiesHelper ---> SolidColorExpression
_LabelsPropertiesHelper ---> ImageKindExpression
_PlotAreaPropertiesHelper ---> AggregationExpression
_ValueAxisPropertiesHelper ---> ResourcePackageAccess
LineChart --->|queryOptions| QueryOptions
_Y2AxisPropertiesHelper ---> LiteralExpression
_Y2AxisPropertiesHelper ---> ImageKindExpression
LineChart ---> ColumnProperty
TrendProperties --->|properties| _TrendPropertiesHelper
LabelsProperties ---> Selector
_LabelsPropertiesHelper ---> ImageExpression
```