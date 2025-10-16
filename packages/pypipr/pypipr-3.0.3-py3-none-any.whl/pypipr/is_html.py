from lxml import html


def is_html(text):
    try:
        document = html.fromstring(text)
        return bool(len(document))
    except Exception:
        return False
