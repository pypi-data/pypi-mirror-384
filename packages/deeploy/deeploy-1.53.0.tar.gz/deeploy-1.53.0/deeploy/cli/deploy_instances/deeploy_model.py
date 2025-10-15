# This is derived from Kserve and modified by Deeploy
# Copyright 2019 kubeflow.org.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import sys
from typing import Optional

import kserve
from kserve.errors import ModelMissingError
from kserve.storage import Storage

from deeploy.cli.custom_instances.model import DeeployCustomModel
from deeploy.cli.custom_instances.model_repository import (
    DeeployCustomModelRepository,
)
from deeploy.cli.parsers.parser_model import parse_args_model

# pylint:disable=no-name-in-module
from deeploy.cli.wrappers.model_wrapper import ModelWrapper

logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

ARTEFACT_FILE_NAME = "model"
ENV_VARIABLE_MODEL_NAME = "K_CONFIGURATION"


class DeeployModelLoader:
    def __init__(self, local_model_object_path: Optional[str] = None) -> None:
        """Initialise the Deeploy Model Object
        Parameters:
            local_model_object_path (Optional) : Path to the local model file \
                within the image if local image is to be provided.
        """
        args = parse_args_model(sys.argv)
        self.name = os.getenv(ENV_VARIABLE_MODEL_NAME).split("-predictor")[0]
        # self.name = args.model_name
        # No support to pass model name as argument currently
        self.nthread = args.nthread
        if not local_model_object_path:
            self.model_dir = args.model_dir
            self.local = False
        else:
            self.model_dir = local_model_object_path
            self.local = True

        model_path = self.load()

        if model_path is None:
            raise Exception("Deeploy Custom Model requires a pre trained model")
        else:
            self.model_path = model_path

    def load(self) -> object:
        if self.local:
            if os.path.exists(self.model_dir):
                model_path = self.model_dir
            else:
                raise FileNotFoundError
        else:
            model_path = Storage.download(self.model_dir)
            model_files = []
            for file in os.listdir(model_path):
                file_path = os.path.join(model_path, file)
                if os.path.isfile(file_path):
                    model_files.append(file_path)
            if len(model_files) == 0:
                raise ModelMissingError(model_path)
            elif len(model_files) > 1:
                raise RuntimeError(
                    "More than one model file is detected, "
                    f"Only one is allowed within model_dir: {model_files}"
                )
            model_path = model_files[0]

        return model_path

    def model_serve(
        self,
        model_wrapper: ModelWrapper,
    ) -> None:
        """Deploys the model and serve it at predict endpoint
        Parameters:
            model_wrapper (ModelWrapper): The user defined deeploy model wrapper
        """
        custom_model = DeeployCustomModel(
            self.name,
            self.nthread,
            self.model_path,
            model_wrapper,
        )
        kserve.ModelServer(
            registered_models=DeeployCustomModelRepository(
                self.model_dir, self.nthread, custom_model
            )
        ).start(models=[custom_model])
