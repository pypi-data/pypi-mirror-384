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
from typing import Dict, Union

import kserve
import numpy as np
import pandas as pd
from kserve.protocol.infer_type import InferRequest


class ModelWrapper:
    logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

    def __init__(self, model_path: str, nthreads: int):
        """Initializes the Model Wrapper Class
        Parameters:
            model_path (str): On deployment the model object path is passed here
            ntrhread (int): Number of processing threads.
        """
        self.model_path = model_path
        self.nthread = nthreads
        self.model = None

    def _predict(self, payload: Union[np.ndarray, pd.DataFrame]) -> Union[Dict, InferRequest]:
        """Define predict function for the custom model
        Parameters:
            payload (np.ndarray or pd.DataFrame): Inference input to predict

        Returns
            predicted output by model
        """
        raise NotImplementedError
