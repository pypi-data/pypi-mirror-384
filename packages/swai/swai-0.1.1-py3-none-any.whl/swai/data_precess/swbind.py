import os
from pathlib import Path
from swai.utils.log import logger
from swai.data_precess.base_preprocess import BasePreprocess


class SWBind(BasePreprocess):
    def __init__(self, input_json, output_dir):
        self.input_json = input_json
        self.output_dir = output_dir

    def process(self):
        return self.pack(self.input_json)