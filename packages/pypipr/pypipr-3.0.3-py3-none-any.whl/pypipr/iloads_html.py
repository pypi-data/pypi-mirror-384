import lxml

from .ijoin import ijoin


def iloads_html(html):
    """
    Mengambil data yang berupa list `<ul>`, dan table `<table>` dari html
    dan menjadikannya data python berupa list.
    setiap data yang ditemukan akan dibungkus dengan tuple sebagai separator.

    ```
    list (<ul>)     -> list         -> list satu dimensi
    table (<table>) -> list[list]   -> list satu dimensi didalam list
    ```
    
    apabila data berupa ul maka dapat dicek type(data) -> html_ul
    apabila data berupa ol maka dapat dicek type(data) -> html_ol
    apabila data berupa dl maka dapat dicek type(data) -> html_dl
    apabila data berupa table maka dapat dicek type(data) -> html_table

    ```python
    import pprint
    pprint.pprint(iloads_html(iopen("https://harga-emas.org/")), depth=10)
    pprint.pprint(iloads_html(iopen("https://harga-emas.org/1-gram/")), depth=10)
    ```
    """

    def xpath(e, x):
        """
        Fungsi ini sangat krusial/menentukan. Fungsi ini dibuat
        supaya xpath yang diberikan diproses dari element saat ini.
        Sedangkan xpath pada element lxml akan mengecek syntax xpath dari
        root paling awal document.
        """
        if not isinstance(e, str):
            e = lxml.html.tostring(e, encoding="unicode")
        e = lxml.html.fromstring(e)
        return (e, e.xpath(x))

    def parse(e):
        parser = {
            "ul": parse_ul,
            "ol": parse_ol,
            "dl": parse_dl,
            "table": parse_table,
        }
        try:
            return parser[e.tag.lower()](e)
        except Exception:
            raise Exception("Tidak ditemukan parse fungsi untuk element : ", e)

    def parse_list(ul):
        """
        Simple parse html list.
        """
        result = []
        _, li = xpath(ul, "li")
        for i in li:
            u = iloads_html(i)
            t = i.text.strip() if i.text else ""
            if t and t != u:
                result.append({t: u})
            else:
                result.append(u)
        return result

    def parse_ul(ul):
        return html_ul(parse_list(ul))

    def parse_ol(ol):
        return html_ol(parse_list(ol))

    def parse_dl(dl):
        """
        Simple parse dl-dt-dd.
        """
        result = html_dl()
        _, di = xpath(dl, "dt|dd")
        d = iter(di)
        try:
            while True:
                i = next(d)
                k = i.tag.lower()
                v = iloads_html(i)
                if k == "dt":
                    result.append(["", []])
                    result[-1][0] = v
                elif k == "dd":
                    result[-1][-1].append(v)
        except Exception:
            pass

        return result

    def parse_table(table):
        """
        Mengambil children tr dari table.
        tr diambil dari thead atau tbody atau langsung tr.
        tr dari thead atau tbody akan dianggap sama.
        """
        result = html_table()
        _, tr = xpath(table, "//tr[not(ancestor::tr)]")
        for itr in tr:
            d = []
            _, td = xpath(itr, "th|td")
            for itd in td:
                d.append(iloads_html(itd))
            result.append(d.copy())
        return result

    def text_content(e):
        """
        mengambil semua text dalam element secara recursive.
        karena tidak ditemukan data dalam element.
        """
        return ijoin(e.itertext(), str_strip=True)

    element, childs = xpath(
        html,
        "//*[self::ul | self::ol | self::dl | self::table]"
        "[not(ancestor::ul | ancestor::ol | ancestor::dl | ancestor::table)]",
    )
    if childs:
        return tuple((parse(data) for data in childs))
    else:
        return text_content(element)


class html_ul(list):
    """
    Class ini digunakan untuk idumps dan iloads html
    """

    pass


class html_ol(list):
    """
    Class ini digunakan untuk idumps dan iloads html
    """

    pass


class html_dl(list):
    """
    Class ini digunakan untuk idumps dan iloads html
    """

    pass


class html_table(list):
    """
    Class ini digunakan untuk idumps dan iloads html
    """

    pass
