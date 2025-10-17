from typing import Callable
from fastapi import FastAPI


class BirdieAPI(FastAPI):
    def __init__(self,
                 init_func: Callable,
                 interact_func: Callable,
                 input_func: Callable,
                 **kwargs
                 ):
        super().__init__(**kwargs)
        self.add_api_route("/initialize", init_func, methods=["POST"])
        self.add_api_route("/interact", interact_func, methods=["POST"])
        self.add_api_route("/input", input_func, methods=["GET"])
