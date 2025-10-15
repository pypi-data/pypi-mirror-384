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
from typing import Dict

import kserve


class TransformerWrapper:
    logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

    def __init__(self):
        """Initializes the Transformer Wrapper Class"""

    def _preprocess(self, payload: Dict) -> Dict:
        """Preprocess transformation before model prediction
        Parameters:
            payload (Dict): \
                Receives the entire request payload that needs to be transformed before model prediction \
                  {
                    "instances": [
                        [
                        3.5,
                        5.1,
                        1.4,
                        0.2
                        ]
                    ]
                  }

        Returns
            transformed payload as Dict 
                Note: For no transformation return payload
        """
        raise NotImplementedError

    def _postprocess(self, response: Dict) -> Dict:
        """Postprocess transformation on model prediction output
        Parameters:
            response (Dict): \
                Receive the entire response of model that needs modification \
                    {
                    "predictions": [
                        [
                        true
                        ]
                    ]
                    }

        Returns
            transformed response as Dict 
                Note: For no transformation return response
        """
        raise NotImplementedError


class JobSchedulesInstancesTransformerWrapper:
    logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

    def __init__(self):
        """Initializes the Transformer Wrapper Class"""

    def _predict(self, payload: Dict):
        raise NotImplementedError
