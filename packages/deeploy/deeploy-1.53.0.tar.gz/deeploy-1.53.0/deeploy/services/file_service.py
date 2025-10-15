import json
import logging
import os
from typing import Union

from deeploy.common.functions import (
    directory_exists,
    file_exists,
)
from deeploy.models import (
    CreateExplainerReference,
    CreateModelReference,
    CreateTransformerReference,
)
from deeploy.models.reference_json import (
    ExplainerReferenceJson,
    ModelReferenceJson,
    TransformerReferenceJson,
)


class FileService:
    """
    A class for to manage json files
    """

    def __init__(self):
        pass

    def generate_metadata_json(self, path: str, metadata_input: dict) -> None:
        self.__create_json_file(path, "metadata", metadata_input)

    def generate_reference_json(
        self,
        path: str,
        reference_input: Union[
            CreateModelReference, CreateExplainerReference, CreateTransformerReference
        ],
    ) -> Union[ModelReferenceJson, ExplainerReferenceJson, TransformerReferenceJson]:
        reference_type = self.__get_reference_type(reference_input)
        self.__create_directory(path, reference_type)
        reference_config = reference_input.get_reference()
        reference = {"reference": reference_config}
        model_path = os.path.join(path, reference_type)
        data = self.__remove_null_values(reference)
        self.__create_json_file(model_path, "reference", data)
        return data

    def __create_json_file(self, path: str, name: str, data: dict) -> str:
        file_location = os.path.join(path, f"{name}.json")

        if file_exists(file_location):
            raise Exception(f"File {name} already exists at {path}")
        else:
            try:
                with open(file_location, "w") as file:
                    json.dump(data, file)
            except OSError as e:
                logging.error(f"Creation of the file {name} failed")
                raise e
        return file_location

    def __create_directory(self, path: str, name: str) -> None:
        dir_location = os.path.join(path, name)

        if directory_exists(dir_location):
            raise Exception(f"Directory {name} already exists at {path}")
        else:
            try:
                os.mkdir(dir_location)
            except OSError:
                logging.error(f"Creation of the directory {name} failed")

    def __remove_null_values(self, d: dict) -> dict:
        def empty(x):
            return x is None or x == {} or x == []

        if not isinstance(d, (dict, list)):
            return d
        elif isinstance(d, list):
            return [v for v in (self.__remove_null_values(v) for v in d) if not empty(v)]
        else:
            return {
                k: v
                for k, v in ((k, self.__remove_null_values(v)) for k, v in d.items())
                if not empty(v)
            }

    def __get_reference_type(
        self,
        reference_input: Union[
            CreateModelReference, CreateExplainerReference, CreateTransformerReference
        ],
    ) -> str:
        if isinstance(reference_input, CreateModelReference):
            return "model"
        elif isinstance(reference_input, CreateExplainerReference):
            return "explainer"
        elif isinstance(reference_input, CreateTransformerReference):
            return "transformer"
        else:
            return ""
