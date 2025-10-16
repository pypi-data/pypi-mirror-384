import json

import yaml

from .iloads_html import iloads_html


def iloads(data, syntax="yaml"):
    """
    Mengubah string data hasil dari idumps menjadi variabel.
    String data adalah berupa syntax YAML.

    ```python
    data = {
        'a': 123,
        't': ['disini', 'senang', 'disana', 'senang'],
        'l': (12, 23, [12, 42]),
    }
    s = idumps(data)
    print(iloads(s))
    ```
    """
    if syntax == "yaml":
        return yaml.full_load(data)
    if syntax == "json":
        return json.load(data)
    if syntax == "html":
        return iloads_html(data)
    raise Exception(f"Syntax tidak didukung {syntax}")
