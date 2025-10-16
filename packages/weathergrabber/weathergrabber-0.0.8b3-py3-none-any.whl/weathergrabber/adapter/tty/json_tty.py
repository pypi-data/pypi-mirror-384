from weathergrabber.usecase.use_case import UseCase
from weathergrabber.domain.adapter.params import Params
from weathergrabber.domain.adapter.mapper.forecast_mapper import forecast_to_dict
import logging
import json

class JsonTTY:

    def __init__(self, use_case: UseCase):
        self.logger = logging.getLogger(__name__)
        self.use_case = use_case
        pass

    def execute(self, params: Params) -> None:
        self.logger.info("Executing JSON output")
        forecast = self.use_case.execute(params)
        output: dict = forecast_to_dict(forecast)
        output_json = json.dumps(output)
        print(output_json)