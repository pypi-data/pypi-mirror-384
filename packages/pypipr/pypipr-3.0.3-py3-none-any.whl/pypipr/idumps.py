import json

import yaml

from .idumps_html import idumps_html


def idumps(data, syntax="yaml", indent=4):
    """
    Mengubah variabel data menjadi string untuk yang dapat dibaca untuk disimpan.
    String yang dihasilkan berbentuk syntax YAML/JSON/HTML.

    ```python
    data = {
        'a': 123,
        't': ['disini', 'senang', 'disana', 'senang'],
        'l': (12, 23, [12, 42]),
    }
    print(idumps(data))
    print(idumps(data, syntax='html'))
    ```
    """
    if syntax == "yaml":
        return yaml.dump(data, indent=indent)
    if syntax == "json":
        return json.dumps(data, indent=indent)
    if syntax == "html":
        return idumps_html(data, indent=indent)
    raise Exception(f"Syntax tidak didukung {syntax}")
