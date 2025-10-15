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

import logging
from typing import Callable, List, Optional

import kserve

from deeploy.cli.interface import Explanation


class ExplainerWrapper:
    logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

    def __init__(self, predict_fn: Callable, explainer, **kwargs):
        """Initializes the Explainer Wrapper Class
        Parameters:
            predict_fn (Callable): \
                On deployment predict function is passed to wrapper here.
            explainer: On deployment the explainer class is passed here
        """
        if explainer is None:
            raise Exception("Explainer Wrapper requires a built explainer")

        self.predict_fn = predict_fn
        self.kwargs = kwargs
        logging.info("Expainer args %s", self.kwargs)
        self.explainer = explainer

    def validate(self, training_data_url: Optional[str]):
        pass

    def explain(self, inputs: List, explain_image: bool = False) -> Explanation:
        """Initializes the Explainer Wrapper Class
        Parameters:
            inputs (List): Receive array of inputs to generate explanation upon
            explainer_image (boolean): If the input is an image array.

        Returns:
            Explanation
        """
        raise NotImplementedError
