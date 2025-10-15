# This is derived from Kserve and modified by Deeploy
# Copyright 2021 The KServe Authors.
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
import asyncio
import json
import logging
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Union

import kserve
import nest_asyncio
import numpy as np
from kserve import Model
from kserve.errors import InferenceError
from kserve.model import PredictorConfig

from deeploy.cli.wrappers.explainer_wrapper import ExplainerWrapper

nest_asyncio.apply()

logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)


class ExplainerMethod(Enum):
    custom = "Custom"

    def __str__(self):
        return self.value


class DeeployCustomExplainer(Model):
    def __init__(  # pylint:disable=too-many-arguments
        self,
        name: str,
        predictor_host: str,
        explainer_wrapper: ExplainerWrapper,
        config: Mapping,
        explainer: Optional[object] = None,
    ):
        """Initializes the Deeploy Explainer Class
        Parameters:
            name (str): Name of the explainer
            predictor_host: (str): Endpoint to communicate with the model
            explainer_wrapper (ExplainerWrapper): User defined Explainer \
                than inherits from Explainer Wrapper,
            config (mapping): Provides configuration to the explainer,
            explainer (object): The explainer artifact that is passed for deployment
        """
        super().__init__(name, PredictorConfig(predictor_host))
        logging.info("Predict URL set to %s", self.predictor_host)
        self.wrapper = explainer_wrapper(self._predict_fn, explainer, **config)
        self.ready = True

    def load(self) -> bool:
        """State loading status"""
        return True

    def _predict_fn(self, arr: Union[np.ndarray, List]) -> np.ndarray:
        """Provides interface to predict with the deployed model
        Parameters:
            arr : Array of inputs for model prediction.
        """
        instances = []
        for req_data in arr:
            if isinstance(req_data, np.ndarray):
                instances.append(req_data.tolist())
            else:
                instances.append(req_data)
        loop = asyncio.get_running_loop()  # type: ignore
        resp = loop.run_until_complete(self.predict({"instances": instances}))
        return np.array(resp["predictions"])

    def explain(
        self, request: Dict, headers: Dict[str, str] = None, explain_image: bool = False
    ) -> Any:
        """Provides explanations interface
        Parameters:
            request : Body of request.
            headers: Headers of request.
            explain_images (boolean): Boolean stating if the explanation is an image.
        """
        try:
            explanation = self.wrapper.explain(request["instances"], explain_image)
            if explain_image:
                logging.info("Returning an image as explanation.")
                response = explanation
            else:
                explanation_as_json_str = json.dumps(explanation)
                logging.info("Explanation: %s", explanation_as_json_str)
                response = json.loads(explanation_as_json_str)
            return response
        except Exception as e:
            raise InferenceError(str(e)) from e
