import lxml


def idumps_html(data, indent=None):
    """
    Serialisasi python variabel menjadi HTML.

    ```html
    List -> <ul>...</ul>
    Dict -> <table>...</table>
    ```

    ```python
    data = {
        'abc': 123,
        'list': [1, 2, 3, 4, 5],
        'dict': {'a': 1, 'b':2, 'c':3},
    }
    print(idumps_html(data))
    ```
    """

    def to_ul(data):
        ul = lxml.etree.Element("ul")
        for i in data:
            li = lxml.etree.SubElement(ul, "li")
            li.append(to_html(i))
        return ul

    def to_table(data: dict):
        table = lxml.etree.Element("table")
        tbody = lxml.etree.SubElement(table, "tbody")
        for i, v in data.items():
            tr = lxml.etree.SubElement(tbody, "tr")
            th = lxml.etree.SubElement(tr, "th")
            th.text = str(i)
            td = lxml.etree.SubElement(tr, "td")
            td.append(to_html(v))
        return table

    def to_text(data):
        span = lxml.etree.Element("span")
        span.text = str(data)
        return span

    def to_html(data):
        struct = {
            dict: to_table,
            list: to_ul,
            tuple: to_ul,
            set: to_ul,
        }
        return struct.get(type(data), to_text)(data)

    html = to_html(data)
    if indent:
        lxml.etree.indent(html, space=" " * indent)
    return lxml.etree.tostring(html, pretty_print=True, encoding="unicode")
