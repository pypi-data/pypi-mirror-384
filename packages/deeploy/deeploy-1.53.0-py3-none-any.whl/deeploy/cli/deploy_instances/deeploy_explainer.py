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

import dill
import kserve
from kserve.storage import Storage

from deeploy.cli.custom_instances.explainer import (
    DeeployCustomExplainer,
)
from deeploy.cli.parsers.parser_explainer import parse_args_explainer
from deeploy.cli.utils import use_transformer

# pylint:disable=no-name-in-module
from deeploy.cli.wrappers.explainer_wrapper import ExplainerWrapper

logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

EXPLAINER_FILENAME = "explainer.dill"


class DeeployExplainerLoader:
    def __init__(self, local_explainer_object_path: Optional[str] = None) -> None:
        """Initialise the Deeploy Explainer Object
        Parameters:
            local_explainer_object_path (Optional) : Path to the local explainer file \
                within the image if local image is to be provided.
        """
        args, extra = parse_args_explainer(sys.argv[1:])
        self.args = args
        self.extra = extra
        self.explainer_model = None
        self.name = args.model_name
        self.predictor_host = args.predictor_host
        if local_explainer_object_path:
            if os.path.exists(local_explainer_object_path):
                explainer_model_path = local_explainer_object_path
            else:
                raise FileNotFoundError
        elif args.storage_uri is not None:
            explainer_model_path = os.path.join(
                Storage.download(args.storage_uri), EXPLAINER_FILENAME
            )
        else:
            raise FileNotFoundError

        try:
            with open(explainer_model_path, "rb") as f:
                logging.info("Loading Explainer")
                self.explainer_model = dill.load(f)  # noqa: S301
                logging.info("Loaded Explainer")
        except Exception as e:
            raise NotImplementedError from e

        if args.transformer:
            self.predictor_host = use_transformer(args.predictor_host)

    def explainer_serve(
        self,
        explainer_wrapper: ExplainerWrapper,
    ) -> None:
        """Deploys the explainer and serve it at explain endpoint
        Parameters:
            explainer_model (DeeployCustomExplainer): The deeploy explain object
        """
        explainer = DeeployCustomExplainer(
            self.name,
            self.predictor_host,
            explainer_wrapper,
            self.extra,
            self.explainer_model,
        )
        explainer.load()
        kserve.ModelServer().start(models=[explainer])
