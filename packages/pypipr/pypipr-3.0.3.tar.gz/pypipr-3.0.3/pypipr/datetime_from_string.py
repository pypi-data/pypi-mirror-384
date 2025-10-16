import datetime
import zoneinfo


def datetime_from_string(iso_string, timezone="UTC"):
    """
    Parse iso_string menjadi datetime object.
    Mempermudah untuk konversi timezone
    """
    return datetime.datetime.fromisoformat(iso_string).replace(
        tzinfo=zoneinfo.ZoneInfo(timezone)
    )


def test():
    print(datetime_from_string("2022-12-12 15:40:13").isoformat())
    print(datetime_from_string("2022-12-12 15:40:13", timezone="Asia/Jakarta"))
