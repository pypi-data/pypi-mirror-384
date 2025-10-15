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

from deeploy.cli.custom_instances.transformer import (
    DeeployCustomJobSchedulesInstancesTransformer,
    DeeployCustomTransformer,
)
from deeploy.cli.parsers.parser_transformer import parse_args_transformer

# pylint:disable=no-name-in-module
from deeploy.cli.wrappers.transformer_wrapper import (
    JobSchedulesInstancesTransformerWrapper,
    TransformerWrapper,
)

logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)


class DeeployTransformerLoader:
    def __init__(
        self,
    ) -> None:
        """Initialize the Deeploy Transformer Object"""
        args = parse_args_transformer(sys.argv)
        if "IS_PYTORCH_MODEL" in os.environ and os.environ["IS_PYTORCH_MODEL"] == "True":
            self.model_name = "model"  ## Torch specific name 'model'
        else:
            self.model_name = args.model_name

        self.predictor_host = args.predictor_host
        self.explainer_host = args.explainer_host

    def transformer_serve(
        self,
        transformer_wrapper: Optional[TransformerWrapper] = None,
        instances_transformer_wrapper: Optional[JobSchedulesInstancesTransformerWrapper] = None,
    ) -> None:
        """Deploys the transformer
        Parameters:
            transformer_wrapper (TransformerWrapper): \
                The user defined deeploy transformer wrapper
            instances_transformer_wrapper: (JobSchedulesInstancesTransformerWrapper)
                The user defined deeploy transformer wrapper for job schedule instance endpoints
        """
        if not transformer_wrapper and not instances_transformer_wrapper:
            raise ValueError("Provide atleast 1 Transformer or InstancesTransformer object")

        models = []

        if transformer_wrapper:
            custom_transformer = DeeployCustomTransformer(
                self.model_name,
                self.predictor_host,
                self.explainer_host,
                transformer_wrapper,
            )
            models.append(custom_transformer)

        if instances_transformer_wrapper:
            custom_instances_transformer = DeeployCustomJobSchedulesInstancesTransformer(
                instances_transformer_wrapper,
            )
            models.append(custom_instances_transformer)

        kserve.ModelServer().start(models=models)
