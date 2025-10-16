from weathergrabber.domain.uv_index import UVIndex

def uv_index_to_dict(uv: UVIndex) -> dict:
    return {
        "string_value": uv.string_value,
        "index": uv.index,
        "of": uv.of,
        "label": uv.label,
    }
