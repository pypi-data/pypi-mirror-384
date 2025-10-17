## Basic Functionality

This basic example tests that your PowerBI report can be parsed and reassembled by ``pbi_core``. 


```python3 linenums="1"

from pbi_core import LocalReport

report = LocalReport.load_pbix("example.pbix")  # (1)!
report.save_pbix("example_out.pbix")  # (1)!
```

!!! danger "Common Issue"

    One of the current limitations in the `pbi_core` library is the incomplete [pydantic](https://docs.pydantic.dev/latest/) typing of the Layout file. This generally appears as a message like: 

    ```shell
    pydantic_core._pydantic_core.ValidationError: 2 validation errors for Layout
    sections.0.visualContainers.1.config.singleVisual.TableChart.objects.columnHeaders.0.properties.underline
    Extra inputs are not permitted [type=extra_forbidden, input_value={'expr': {'Literal': {'Value': 'true'}}}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
    sections.0.visualContainers.1.config.singleVisual.TableChart.objects.values.0.properties.underline
    Extra inputs are not permitted [type=extra_forbidden, input_value={'expr': {'Literal': {'Value': 'true'}}}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
    ```

    If you encounter an error message like this, please do the following:

    1. Create an issue on the [Github page](https://github.com/douglassimonsen/pbi_core/issues) with the error message. If you're able, attaching a `pbix` file will make the fix quicker and can be added to the test suite to ensure the issue doesn't re-appear in future versions
    2. Add  `--allow-extra` to your python call. This will tell Pydantic to [include extra arguments](https://github.com/pydantic/pydantic/issues/6145#issuecomment-1592568675) as standard JSON lists/dicts/strings/ints

## Altering Data model

This example shows how you can add automatic descriptions to PowerBI columns (possibly from some governance tool??)


```python3 linenums="1"

from pbi_core import LocalReport

report = LocalReport.load_pbix("example.pbix")
for column in report.ssas.columns:
    column.description = "pbi_core has touched this"
    column.alter()  # saves the changes to the SSAS DB

report.save_pbix("example_out.pbix")
```

## Finding records in SSAS tables

This example shows how to find SSAS records and extract data from report columns

```python3 linenums="1"
from pbi_core import LocalReport

report = LocalReport.load_pbix("example.pbix")
values = report.ssas.columns.find({"explicit_name": "a"}).data()
print(values)
values2 = report.ssas.tables.find({"name": "Table"}).data()
print(values2)

measure = report.ssas.measures.find({"name": "Measure"})
column = measure.table().columns()[1]  
# Note: the first column is a hidden row-count column that can't be used in measures
values3 = measure.data(column, head=10)
print(values3)
```

## pbi_core Lineage Chart

This example displays a lineage chart in HTML:

```python3 linenums="1"
from pbi_core import LocalReport

report = LocalReport.load_pbix("example.pbix", kill_ssas_on_exit=True)
col = report.ssas.columns.find({"explicit_name": "MeasureColumn"})
col.get_lineage("parents").to_mermaid().show()
```

## Improved Multilanguage Support

This example displays the ability to easily convert PBIX reports to alternate languages:

```python linenums="1"
from pbi_core import LocalReport
from pbi_core.misc.internationalization import get_static_elements, set_static_elements

report = LocalReport.load_pbix("example.pbix", kill_ssas_on_exit=True)
x = get_static_elements(report.static_files.layout)
x.to_excel("multilang.xlsx")

set_static_elements("multilang1.xlsx", "example.pbix")
```

## Automatic Data Model Cleaning

One of the core tensions in PowerBI is the size of the data model. In development, you want to have many measures, columns, and tables to simplify new visual creation. After developing the report, the additional elements create two issues:

1. It's difficult to understand which elements are being used and how they relate to each other
2. The additional columns and tables can slow down visual rendering times, negatively impacting UX

pbi_core has an automatic element culler that allows you to remove unnecessary elements after the report has been designed:

```python linenums="1"

from pbi_core import LocalReport

report = LocalReport.load_pbix("example_pbis/api.pbix")
report.cleanse_ssas_model()
report.save_pbix("cull_out.pbix")
```

## Performance Analysis

This example shows how to analyze the performance of a Power BI report's visual:

!!! warning

    In the previous implementations, the performance trace occassionally hangs for 2-5 minutes. The library has solved this by pinging the SSAS server during the trace with a trivial `EVALUATE {1}` command. Although this seems to have fixed the issue, it clearly doesn't touch the root issue. Therefore, if the trace hangs, you may need to kill and restart the process.


```python linenums="1"

from pbi_core import LocalReport

report = LocalReport.load_pbix("example_pbis/example_section_visibility.pbix")
# x = report.static_files.layout.sections[0].visualContainers[0].get_performance(report.ssas)
perf = report.static_files.layout.sections[0].get_performance(report.ssas)
print(perf)
print("=================")
print(perf[0].pprint())
```

Which generates the following output.

```shell
2025-07-05 14:07:31 [info     ] Loading PBIX                   path=example_pbis/example_section_visibility.pbix
2025-07-05 14:07:33 [warning  ] Removing old version of PBIX data model for new version db_name=example_section_visibility
2025-07-05 14:07:33 [info     ] Tabular Model load complete   
2025-07-05 14:07:35 [info     ] Beginning trace               
2025-07-05 14:07:38 [info     ] Running DAX commands          
2025-07-05 14:07:41 [info     ] Terminating trace             
[Performance(rows=5, total_duration=0.0, total_cpu_time=0.0, peak_consumption=1.0 MiB]
=================
Performance(
    Command:

        DEFINE VAR __DS0Core =
                SUMMARIZECOLUMNS('example'[b], "Suma", CALCULATE(SUM('example'[a])))

        EVALUATE
                __DS0Core

    Start Time: 2025-07-05T19:07:38.450000+00:00
    End Time: 2025-07-05T19:07:38.453000+00:00
    Total Duration: 4 ms
    Total CPU Time: 0 ms
    Query CPU Time: 0 ms
    Vertipaq CPU Time: 0 ms
    Execution Delay: 0 ms
    Approximate Peak Consumption: 1.0 MiB
    Rows Returned: 5
)

```

### Custom DAX Commands

You can also trace custom DAX commands like so:


```python linenums="1"
import pbi_core

command = "EVALUATE {1}"
report = pbi_core.LocalReport.load_pbix("example_pbis/api.pbix")
with report.ssas.get_performance_trace() as perf_trace:
    perf = perf_trace.get_performance(command)
print(perf[0])
```   

Which generates the following output:

```shell
2025-10-16 16:02:44 [info     ] Loading PBIX report            load_ssas=True load_static_files=True path=example_pbis/api.pbix
2025-10-16 16:02:44 [info     ] Loading PBIX SSAS              path=example_pbis/api.pbix
2025-10-16 16:02:44 [info     ] Re-using existing local SSAS instance port=52125
2025-10-16 16:02:44 [warning  ] Removing old version of PBIX data model for new version db_name=api
2025-10-16 16:02:44 [info     ] Tabular Model load complete   
2025-10-16 16:02:44 [info     ] Syncing from SSAS              db_name=api
2025-10-16 16:02:44 [info     ] Loading PBIX Static Files      path=example_pbis/api.pbix
2025-10-16 16:02:44 [info     ] Loaded PBIX report             components=ssas+static
2025-10-16 16:02:44 [info     ] Beginning trace               
2025-10-16 16:02:46 [info     ] Running DAX commands          
2025-10-16 16:02:47 [info     ] Terminating trace             
[Performance(rows=1, total_duration=0.0, total_cpu_time=0.0, peak_consumption=0.0 B]
```

## Styling Layout Elements

This example shows how to apply style changes to elements in a PowerBI report globally. This ensures consistent styling and protects hands from carpal tunnel.

!!! note "Alternate Selection Methods"

    We also included two alternate methods of finding elements on lines 8 and 9. You can pass dictionaries of attribute/value pairs or a function returning a boolean and only elements matching those will return. One downside of these methods in this case is that `Slicer` is a more specific type than `BaseVisual`. The return of the `find_all` method returns `list[<input type>]`, so the more specific type of `Slicer` will provide better autocompletion if your IDE supports it. For instance, the `Slicer` class knows there's an `objects` attribute and it's children, but the `BaseVisual` doesn't.

```python linenums="1"
from pbi_core import LocalReport
from pbi_core.static_files.layout.visuals.properties.base import SolidColorExpression
from pbi_core.static_files.layout.visuals.slicer import Slicer

report = LocalReport.load_pbix("example_pbis/api.pbix", load_ssas=False, load_static_files=True)
slicers = report.static_files.layout.find_all(Slicer)
# from pbi_core.static_files.layout.visuals.base import BaseVisual
# slicers = report.static_files.layout.find_all(BaseVisual, {"visualType": "slicer"})
# slicers = report.static_files.layout.find_all(BaseVisual, lambda v: v.visualType == "slicer")
for s in slicers:
    new_color = SolidColorExpression.from_hex("#FF0000")
    s.objects.header[0].properties.fontColor = new_color
    s.objects.items[0].properties.fontColor = new_color
report.save_pbix("example_out.pbix")

```