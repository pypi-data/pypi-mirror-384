from weathergrabber.domain.label_value import LabelValue

def label_value_to_dict(lv: LabelValue) -> dict:
    return {
        "label": lv.label,
        "value": lv.value,
    }
