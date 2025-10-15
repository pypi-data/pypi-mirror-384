from typing import Dict, Union

from kserve import Model
from kserve.errors import InferenceError
from kserve.protocol.infer_type import InferRequest, InferResponse
from kserve.utils.utils import get_predict_input, get_predict_response

from deeploy.cli.wrappers.model_wrapper import ModelWrapper


class DeeployCustomModel(Model):
    def __init__(
        self,
        name: str,
        nthread: int,
        model_path: object,
        model_wrapper: ModelWrapper,
    ):
        """Initializes the Deeploy Model Class
        Parameters:
            name (str): Name of the model
            nthread (int): Number of processing threads.
            model_path: (str): Path to the local pre trained model file
            model_wrapper (ModelWrapper): User defined model wrapper
        """
        super().__init__(name)
        self.name = name
        self.nthread = nthread
        self.model = model_wrapper(model_path, nthread)
        self.ready = True

    def load(self) -> bool:
        return True

    def predict(
        self, payload: Union[Dict, InferRequest], headers: Dict[str, str] = None
    ) -> Union[Dict, InferResponse]:
        """
        Parameters:
            payload (Dict|InferRequest): Prediction inputs.
            headers (Dict): Request headers.

        Returns:
            Dict|InferResponse: Return the prediction result.
        """
        try:
            instances = get_predict_input(payload)
            result = self.model._predict(instances)
            return get_predict_response(payload, result, self.name)
        except Exception as e:
            raise InferenceError(str(e)) from e
