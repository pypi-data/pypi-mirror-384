import json
import pathlib
from typing import Any

import bs4
import jinja2
import requests
from structlog import get_logger  # no need to call the package logger file, since this is just a dev utility

logger = get_logger()

COMMAND_MAPPING = {"create": 0, "alter": 1, "delete": 2, "rename": 3, "refresh": 4}
PREFIX = """
  <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:sql="urn:schemas-microsoft-com:xml-sql">
    <xs:element>
      <xs:complexType>
        <xs:sequence>
          <xs:element type="row"/>
        </xs:sequence>
      </xs:complexType>
    </xs:element>
    <xs:complexType name="row">
      <xs:sequence>
"""[1:-1]  # to remove the leading/trailing newlines
SUFFIX = """
      </xs:sequence>
    </xs:complexType>
  </xs:schema>
"""[1:-1]  # to remove the leading/trailing newlines

command_template = jinja2.Template(
    """
<{{component}}>
{{PREFIX}}
{{fields}}
{{SUFFIX}}
  {% raw %}{{rows}}{% endraw %}
</{{component}}>
""".strip(),
)


BASE_PATH = pathlib.Path(__file__).parent / "command_templates" / "schema"
BASE_PATH.mkdir(exist_ok=True)
BASE_URL = "https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-ssas-t"


def read_toc_page() -> dict[Any, Any]:
    resp = requests.get(f"{BASE_URL}/toc.json", timeout=10)
    resp_content: dict[Any, Any] = json.loads(resp.text)["items"]
    alter_folder = [0, 0, 0, 0, 0, 2, 0, 4, 1, 0]
    for index in alter_folder:
        resp_content = resp_content[index]["children"]
    return resp_content


def save_entity(entity: dict[str, str], command: str) -> None:
    if entity["toc_title"] in {
        "3.1.5.2.1.5.1.4 Out-of-Line Bindings",
        "3.1.5.2.1.5.1.5 Pushed Data",
    }:
        return
    logger.info(command, entity=entity["toc_title"])
    component = entity["toc_title"].split()[-1]

    page = entity["href"]

    resp = requests.get(f"{BASE_URL}/{page}", timeout=10)
    command_text = bs4.BeautifulSoup(resp.text, "lxml").find("pre")
    if command_text is None:
        raise ValueError
    command_text = command_text.text.replace("Â\xa0", " ")
    command_text = bs4.BeautifulSoup(command_text, "xml")
    row = command_text.find("xs:complexType", {"name": "row"})
    assert isinstance(row, bs4.element.Tag)
    fields = row.find_all("xs:element")
    field_str = "\n".join(" " * 8 + str(x) for x in fields)
    (BASE_PATH / component).mkdir(parents=True, exist_ok=True)
    (BASE_PATH / component / f"{command}.xml").write_text(
        command_template.render(PREFIX=PREFIX, fields=field_str, SUFFIX=SUFFIX, component=component),
    )


def get_command(command: str, folder: dict[Any, Any]) -> None:
    folder = folder[COMMAND_MAPPING[command]]["children"][0]["children"]
    for page in folder:
        save_entity(page, command)


def main() -> None:
    resp = read_toc_page()
    for command in COMMAND_MAPPING:
        get_command(command, resp)


if __name__ == "__main__":
    main()
