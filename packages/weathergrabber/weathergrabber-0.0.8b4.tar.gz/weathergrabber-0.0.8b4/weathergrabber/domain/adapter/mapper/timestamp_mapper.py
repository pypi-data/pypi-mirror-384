from weathergrabber.domain.timestamp import Timestamp

def timestamp_to_dict(ts: Timestamp) -> dict:
    return {
        "time": ts.time,
        "gmt": ts.gmt,
        "text": ts.text,
    }
