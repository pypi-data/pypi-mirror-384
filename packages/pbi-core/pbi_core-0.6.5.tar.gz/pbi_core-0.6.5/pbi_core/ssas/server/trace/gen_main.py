import time
from pathlib import Path

import bs4
import requests
from structlog import get_logger

logger = get_logger()

BASE_URL = "https://learn.microsoft.com/en-us/analysis-services/trace-events"
SEP = "\n" * 3


def gen_trace_enums(class_name: str, url: str) -> str:
    logger.info("Processing Events")
    ret = [f"class {class_name}(Enum):"]
    page = requests.get(BASE_URL + url, timeout=10)
    content = bs4.BeautifulSoup(page.content, features="lxml")
    for table in content.find_all("table"):
        for row in list(table.find_all("tr"))[1:]:  # pyright: ignore reportAttributeAccessIssue
            children = list(row.find_all("td"))  # pyright: ignore reportAttributeAccessIssue
            ret.append(
                f"\t{str(children[1].text).replace(' ', '_').upper()} = {children[0].text}  # {children[2].text}",
            )
    return "\n".join(ret) + SEP


def gen_event_enums(url: str) -> str:
    logger.info("Processing Columns", url=url)
    time.sleep(2)  # needed to avoid rate limiting
    ret: list[str] = []
    page = requests.get(BASE_URL + url, timeout=10)
    content = bs4.BeautifulSoup(page.content, features="lxml")
    headers: list[str] = [x.text for x in content.find_all("h2")][1:-3]
    headers = [x[: (x + " Class—Data").index(" Class—Data")].replace(" ", "") + "Columns" for x in headers]
    tables = content.find_all("table")
    tables = tables[len(tables) - len(headers) :]
    for header, table in zip(headers, tables, strict=False):
        ret2 = [f"class {header}(Enum):"]
        if table.find("tr").find("th").text != "Column Name":  # pyright: ignore reportAttributeAccessIssue
            continue
        for row in list(table.find_all("tr"))[1:]:  # pyright: ignore reportAttributeAccessIssue
            children = list(row.find_all("td"))  # pyright: ignore reportAttributeAccessIssue
            comment = children[len(children) - 1].text.replace("\n", " ")
            ret2.append(f"\t{str(children[0].text).replace(' ', '_').upper()} = {children[1].text}  # {comment}")
        ret.append("\n".join(ret2) + SEP)
    return "\n".join(ret)


with (Path(__file__).parent / "trace_enums.py").open("w", encoding="utf-8") as f:
    f.write("from enum import Enum" + SEP)
    f.write(gen_trace_enums("TraceEvents", "/analysis-services-trace-events"))
    # f.write(gen_event_enums("/command-events-data-columns"))
    f.write(gen_event_enums("/discover-events-data-columns"))
    f.write(gen_event_enums("/discover-server-state-events-data-columns"))
    f.write(gen_event_enums("/errors-and-warnings-events-data-columns"))
    f.write(gen_event_enums("/file-load-and-save-data-columns"))
    f.write(gen_event_enums("/lock-events-data-columns"))
    # f.write(gen_event_enums("/progress-reports-data-columns"))
    f.write(gen_event_enums("/security-audit-data-columns"))
    # f.write(gen_event_enums("/jobgraph-events-data-columns"))
    f.write(gen_event_enums("/notification-events-data-columns"))
    f.write(gen_event_enums("/queries-events-data-columns"))
    f.write(gen_event_enums("/query-processing-events-data-column"))
    f.write(gen_event_enums("/session-events-data-columns"))
