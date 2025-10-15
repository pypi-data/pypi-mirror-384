from typing import Dict

from kserve import Model
from kserve.errors import InferenceError
from kserve.model import PredictorConfig

from deeploy.cli.wrappers.transformer_wrapper import (
    JobSchedulesInstancesTransformerWrapper,
    TransformerWrapper,
)


class DeeployCustomTransformer(Model):
    def __init__(
        self,
        name: str,
        predictor_host: str,
        explainer_host: str,
        transformer_wrapper: TransformerWrapper,
    ):
        """Initializes the Deeploy Model Class
        Parameters:
            name (str): Name of the transformer
            predictor_host (str): Interface to model deployment,
            explainer_host (str): Interface to explainer deployment
            transformer_wrapper (TransformerWrapper): User defined transformer wrapper
        """
        super().__init__(name, PredictorConfig(predictor_host))
        self.predictor_host = predictor_host
        self.explainer_host = explainer_host
        self.transformer = transformer_wrapper()
        self.ready = True

    def preprocess(self, payload: Dict, headers: Dict[str, str] = None) -> Dict:
        """
        Parameters:
            payload (Dict): To be predicted input values for model.
            headers (Dict): Request headers.

        Returns:
            Dict: Return the pre model prediction transformed inputs.
        """
        try:
            return self.transformer._preprocess(payload=payload)
        except Exception as e:
            raise InferenceError(str(e)) from e

    def postprocess(self, response: Dict, headers: Dict[str, str] = None) -> Dict:
        """
        Parameters:
            payload (Dict): Predicted values from model.
            headers (Dict): Request headers.

        Returns:
            Dict: Return the post model prediction transformed result.
        """
        try:
            return self.transformer._postprocess(response=response)
        except Exception as e:
            raise InferenceError(str(e)) from e


class DeeployCustomJobSchedulesInstancesTransformer(Model):
    def __init__(self, instances_transformer_wrapper: JobSchedulesInstancesTransformerWrapper):
        """Initializes the _request_instances endpoint, which can be used to return data for input of job schedule predictions requests
        Parameters:
            name (str): Name of the transformer
            instances_transformer_wrapper (JobSchedulesInstancesTransformerWrapper): User defined transformer wrapper
        """
        name = "_request_instances"
        super().__init__(name)
        self.transformer = instances_transformer_wrapper()
        self.ready = True

    def predict(self, payload: Dict, headers: Dict[str, str] = None) -> Dict:
        try:
            return self.transformer._predict(payload)
        except Exception as e:
            raise InferenceError(str(e)) from e
