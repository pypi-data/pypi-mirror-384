from typing import Dict, List, Optional, Union

from deeploy.enums.artifact import Artifact
from deeploy.models import (
    ActualResponse,
    ClientConfig,
    CreateActuals,
    CreateAzureMLDeployment,
    CreateDeployment,
    CreateEvaluation,
    CreateExplainerReference,
    CreateExternalDeployment,
    CreateModelReference,
    CreateRegistrationDeployment,
    CreateSageMakerDeployment,
    CreateTransformerReference,
    Deployment,
    GetPredictionLogsOptions,
    UpdateAzureMLDeployment,
    UpdateDeployment,
    UpdateDeploymentDescription,
    UpdateExternalDeployment,
    UpdateRegistrationDeployment,
    UpdateSageMakerDeployment,
)
from deeploy.models.create_environment_variable import CreateEnvironmentVariable
from deeploy.models.create_guardrail import CreateGuardrail
from deeploy.models.create_job_schedule import CreateJobSchedule
from deeploy.models.custom_metric import (
    CreateCustomMetric,
    CreateCustomMetricDataPoint,
    CustomMetric,
    CustomMetricDataPoint,
    CustomMetricGraphData,
    UpdateCustomMetric,
)
from deeploy.models.environment_variable import EnvironmentVariable
from deeploy.models.get_request_logs_options import GetRequestLogsOptions
from deeploy.models.guardrail import Guardrail
from deeploy.models.job_schedule import JobSchedule
from deeploy.models.prediction_log import PredictionLog, RequestLog
from deeploy.models.reference_json import (
    ExplainerReferenceJson,
    ModelReferenceJson,
    TransformerReferenceJson,
)
from deeploy.models.repository import Repository
from deeploy.models.test_job_schedule import TestJobSchedule
from deeploy.models.update_job_schedule import UpdateJobSchedule
from deeploy.services import (
    DeeployService,
    FileService,
)


class Client:
    """
    A class for interacting with Deeploy
    """

    def __init__(
        self,
        host: str,
        workspace_id: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        deployment_token: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> None:
        """Initialise the Deeploy client
        Parameters:
            host (str): The host at which Deeploy is located, i.e. deeploy.example.com
            workspace_id (str): The ID of the workspace in which your repository
                is located
            access_key (str, optional): Personal Access Key generated from the Deeploy UI
            secret_key (str, optional): Secret Access Key generated from the Deeploy UI
            deployment_token (str, optional): Can be a Deployment token generated from the Deeploy UI or JWT
                when using OpenID Connect
            organization_id (str, optional): Provide your organization ID only when authenticating to Deeploy cloud
                using OpenID Connect
        """

        self.__config = ClientConfig(
            **{
                "host": host,
                "workspace_id": workspace_id,
                "access_key": access_key,
                "secret_key": secret_key,
                "token": deployment_token,
                "organization_id": organization_id,
            }
        )

        self.__deeploy_service = DeeployService(
            host, access_key, secret_key, deployment_token, organization_id
        )

        self.__file_service = FileService()

    def create_environment_variable(
        self, options: Union[CreateEnvironmentVariable, dict]
    ) -> EnvironmentVariable:
        """Create an environment variable in a Workspace"
        Parameters:
            options (CreateEnvironmentVariable): An instance of the CreateEnvironmentVariable class
                containing the environment variable configuration options
        """
        if isinstance(options, dict):
            options = CreateEnvironmentVariable(**options)

        return EnvironmentVariable.model_validate(
            self.__deeploy_service.create_environment_variable(self.__config.workspace_id, options)
        )

    def get_all_environment_variables(self) -> List[EnvironmentVariable]:
        """Get all environment variables from your Workspace"""

        return self.__deeploy_service.get_all_environment_variables(self.__config.workspace_id)

    def get_environment_variable_ids_for_deployment_artifact(
        self, deployment_id: str, artifact: Artifact
    ) -> List[str]:
        """Get the current environment variable IDs for an artifact of your Deployment
        This method can be used to help update your Deployment
        Parameters:
            deployment_id (str): The uuid of the Deployment of which to retrieve the environment variable IDs
            artifact (str): The artifact of which to retrieve the environment variable IDs from
        """

        return self.__deeploy_service.get_environment_variable_ids_for_deployment_artifact(
            self.__config.workspace_id, deployment_id, artifact
        )

    def create_deployment(self, options: Union[CreateDeployment, dict]) -> Deployment:
        """Create a Deployment on Deeploy
        Parameters:
            options (CreateDeployment): An instance of the CreateDeployment class
                containing the deployment configuration options
        """
        if isinstance(options, dict):
            options = CreateDeployment(**options)

        return self.__deeploy_service.create_deployment(self.__config.workspace_id, options)

    def create_sagemaker_deployment(
        self,
        options: Union[CreateSageMakerDeployment, dict],
    ) -> Deployment:
        """Create a SageMaker Deployment on Deeploy
        Parameters:
            options (CreateSageMakerDeployment): An instance of the CreateSageMakerDeployment class
                containing the deployment configuration options
        """
        if isinstance(options, dict):
            options = CreateSageMakerDeployment(**options)

        return self.__deeploy_service.create_sagemaker_deployment(
            self.__config.workspace_id, options
        )

    def create_azure_ml_deployment(
        self,
        options: Union[CreateAzureMLDeployment, dict],
    ) -> Deployment:
        """Create an Azure Machine Learning Deployment on Deeploy
        Parameters:
            options (CreateAzureMLDeployment): An instance of the CreateAzureMLDeployment class
                containing the deployment configuration options
        """
        if isinstance(options, dict):
            options = CreateAzureMLDeployment(**options)

        return Deployment.model_validate(
            self.__deeploy_service.create_azure_ml_deployment(self.__config.workspace_id, options)
        )

    def create_external_deployment(
        self,
        options: Union[CreateExternalDeployment, dict],
    ) -> Deployment:
        """Create a Deployment on Deeploy
        Parameters:
            options (CreateExternalDeployment): An instance of the CreateExternalDeployment class
                containing the deployment configuration options
        """

        if isinstance(options, dict):
            options = CreateExternalDeployment(**options)

        return Deployment.model_validate(
            self.__deeploy_service.create_external_deployment(self.__config.workspace_id, options)
        )

    def create_registration_deployment(
        self,
        options: Union[CreateRegistrationDeployment, dict],
    ) -> Deployment:
        """Create a Deployment on Deeploy
        Parameters:
            options (CreateRegistrationDeployment): An instance of the CreateRegistrationDeployment class
                containing the deployment configuration options
        """
        if isinstance(options, dict):
            options = CreateRegistrationDeployment(**options)

        return Deployment.model_validate(
            self.__deeploy_service.create_registration_deployment(
                self.__config.workspace_id, options
            )
        )

    def get_repositories(self) -> List[Repository]:
        """Get all repositories from your Workspace

        Returns:
            dict: A dictionary containing information about repositories in the workspace
        """

        repositories = self.__deeploy_service.get_repositories(self.__config.workspace_id)
        return [Repository.model_validate(item) for item in repositories]

    def update_deployment(
        self,
        deployment_id: str,
        options: Union[UpdateDeployment, dict],
    ) -> Deployment:
        """Update a Deployment on Deeploy
        Parameters:
            deployment_id (str): The uuid of the Deployment to update
            options (UpdateDeployment): An instance of the UpdateDeployment class
                containing the deployment configuration options
        """
        if isinstance(options, dict):
            options = UpdateDeployment(**options)

        current_deployment = self.__deeploy_service.get_deployment(
            self.__config.workspace_id, deployment_id
        )

        if not (current_deployment):
            raise Exception(
                "Deployment was not found in the Deeploy Workspace. \
                 Make sure the deployment_id is correct."
            )

        return self.__deeploy_service.update_deployment(
            self.__config.workspace_id, deployment_id, options
        )

    def update_sagemaker_deployment(
        self,
        deployment_id: str,
        options: UpdateSageMakerDeployment,
    ) -> Deployment:
        """Update a SageMaker Deployment on Deeploy
        Parameters:
            deployment_id (str): The uuid of the Deployment to update
            options (UpdateSageMakerDeployment): An instance of the UpdateSageMakerDeployment class
                containing the deployment configuration options
        """

        current_deployment = self.__deeploy_service.get_deployment(
            self.__config.workspace_id, deployment_id
        )

        if not (current_deployment):
            raise Exception(
                "Deployment was not found in the Deeploy Workspace. \
                 Make sure the deployment_id is correct."
            )

        return self.__deeploy_service.update_sagemaker_deployment(
            self.__config.workspace_id, deployment_id, UpdateSageMakerDeployment(**options)
        )

    def update_azure_ml_deployment(
        self,
        deployment_id: str,
        options: UpdateAzureMLDeployment,
    ) -> Deployment:
        """Update an Azure Machine Learning Deployment on Deeploy
        Parameters:
            deployment_id (str): The uuid of the Deployment to update
            options (UpdateAzureMLDeployment): An instance of the UpdateAzureMLDeployment class
                containing the deployment configuration options
        """

        current_deployment = self.__deeploy_service.get_deployment(
            self.__config.workspace_id, deployment_id
        )

        if not (current_deployment):
            raise Exception(
                "Deployment was not found in the Deeploy Workspace. \
                 Make sure the deployment_id is correct."
            )

        return self.__deeploy_service.update_azure_ml_deployment(
            self.__config.workspace_id, deployment_id, UpdateAzureMLDeployment(**options)
        )

    def update_external_deployment(
        self,
        deployment_id: str,
        options: UpdateExternalDeployment,
    ) -> Deployment:
        """Update a Deployment on Deeploy
        Parameters:
            deployment_id (str): The uuid of the Deployment to update
            options (UpdateExternalDeployment): An instance of the UpdateExternalDeployment class
                containing the deployment configuration options
        """

        current_deployment = self.__deeploy_service.get_deployment(
            self.__config.workspace_id, deployment_id
        )

        if not (current_deployment):
            raise Exception(
                "Deployment was not found in the Deeploy Workspace. \
                 Make sure the deployment_id is correct."
            )

        return self.__deeploy_service.update_external_deployment(
            self.__config.workspace_id, deployment_id, UpdateExternalDeployment(**options)
        )

    def update_registration_deployment(
        self,
        deployment_id: str,
        options: UpdateRegistrationDeployment,
    ) -> Deployment:
        """Update a Deployment on Deeploy
        Parameters:
            deployment_id (str): The uuid of the Deployment to update
            options (UpdateRegistrationDeployment): An instance of the UpdateRegistrationDeployment class
                containing the deployment configuration options
        """

        current_deployment = self.__deeploy_service.get_deployment(
            self.__config.workspace_id, deployment_id
        )

        if not (current_deployment):
            raise Exception(
                "Deployment was not found in the Deeploy Workspace. \
                 Make sure the deployment_id is correct."
            )

        return self.__deeploy_service.update_registration_deployment(
            self.__config.workspace_id, deployment_id, UpdateRegistrationDeployment(**options)
        )

    def update_deployment_description(
        self, deployment_id: str, options: UpdateDeploymentDescription
    ) -> Deployment:
        """Update the description of a Deployment on Deeploy
        Parameters:
            deployment_id (str): The uuid of the Deployment to update
            options (UpdateDeploymentDescription): An instance of the UpdateDeploymentDescription class
                containing the deployment description options
        """

        current_deployment = self.__deeploy_service.get_deployment(
            self.__config.workspace_id, deployment_id
        )

        if not (current_deployment):
            raise Exception(
                "Deployment was not found in the Deeploy Workspace. \
                 Make sure the deployment_id is correct."
            )

        return self.__deeploy_service.update_deployment_description(
            self.__config.workspace_id, deployment_id, UpdateDeploymentDescription(**options)
        )

    def create_job_schedule(self, options: Union[CreateJobSchedule, dict]) -> List[Dict]:
        """Create a job schedule in a Workspace"
        Parameters:
            options (CreateJobSchedule): An instance of the CreateJobSchedule class
                containing the job schedule configuration options
        """
        if isinstance(options, dict):
            options = CreateJobSchedule(**options)

        return self.__deeploy_service.create_job_schedule(self.__config.workspace_id, options)

    def test_job_schedule(self, options: Union[TestJobSchedule, dict]) -> JobSchedule:
        """Test a job schedule in a Workspace"
        Parameters:
            options (TestJobSchedule): An instance of the TestJobSchedule class
                containing the test job schedule configuration options
        """
        if isinstance(options, dict):
            options = TestJobSchedule(**options)

        return self.__deeploy_service.test_job_schedule(self.__config.workspace_id, options)

    def update_job_schedule(self, job_schedule_id: str, options: UpdateJobSchedule) -> JobSchedule:
        """Update a job schedule in a Workspace"
        Parameters:
            job_schedule_id (str): The uuid of the job schedule to update
            options (UpdateJobSchedule): An instance of the UpdateJobSchedule class
                containing the job schedule configuration options
        """

        return self.__deeploy_service.update_job_schedule(
            self.__config.workspace_id, job_schedule_id, UpdateJobSchedule(**options)
        )

    def deactivate_job_schedule(self, job_schedule_id: str) -> JobSchedule:
        """Deactivate a job schedule in a Workspace"
        Parameters:
            job_schedule_id (str): The uuid of the job schedule to deactivate
        """

        return self.__deeploy_service.deactivate_job_schedule(
            self.__config.workspace_id, job_schedule_id
        )

    def activate_job_schedule(self, job_schedule_id: str) -> JobSchedule:
        """Activate a job schedule in a Workspace"
        Parameters:
            job_schedule_id (str): The uuid of the job schedule to activate
        """

        return self.__deeploy_service.activate_job_schedule(
            self.__config.workspace_id, job_schedule_id
        )

    def get_custom_metrics(self, deployment_id: str) -> List[CustomMetric]:
        """Get all custom metrics in a Deployment"
        Parameters:
            deployment_id (str): The uuid of the deployment
        """

        return self.__deeploy_service.get_custom_metrics(self.__config.workspace_id, deployment_id)

    def get_custom_metrics_with_chart_data(self, deployment_id: str) -> List[CustomMetricGraphData]:
        """Get all custom metrics with graph data in a Deployment"
        Parameters:
            deployment_id (str): The uuid of the deployment
        """

        return self.__deeploy_service.get_custom_metrics_with_chart_data(
            self.__config.workspace_id, deployment_id
        )

    def create_custom_metric(
        self, deployment_id: str, options: Union[CreateCustomMetric, dict]
    ) -> CustomMetric:
        """Create a custom metric in a Deployment"
        Parameters:
            deployment_id (str): The uuid of the deployment
            options (CreateCustomMetric): An instance of the CreateCustomMetric class
                containing the custom metric configuration options
        """
        if isinstance(options, dict):
            options = CreateCustomMetric(**options)

        return self.__deeploy_service.create_custom_metric(
            self.__config.workspace_id, deployment_id, options
        )

    def update_custom_metric(
        self, deployment_id: str, custom_metric_id: str, options: UpdateCustomMetric
    ) -> CustomMetric:
        """Update a custom metric in a Deployment"
        Parameters:
            deployment_id (str): The uuid of the deployment
            custom_metric_id (str): The uuid of the custom metric to update
            options (UpdateCustomMetric): An instance of the UpdateCustomMetric class
                containing the custom metric configuration options
        """

        return self.__deeploy_service.update_custom_metric(
            self.__config.workspace_id,
            deployment_id,
            custom_metric_id,
            UpdateCustomMetric(**options),
        )

    def delete_custom_metric(self, deployment_id: str, custom_metric_id: str) -> List[Dict]:
        """Delete a custom metric in a Deployment"
        Parameters:
            deployment_id (str): The uuid of the deployment
            custom_metric_id (str): The uuid of the custom metric to delete
        """

        return self.__deeploy_service.delete_custom_metric(
            self.__config.workspace_id, deployment_id, custom_metric_id
        )

    def create_custom_metric_data_points(
        self,
        deployment_id: str,
        custom_metric_id: str,
        options_list: List[CreateCustomMetricDataPoint],
    ) -> List[CustomMetricDataPoint]:
        """Add custom metric datapoints to a custom metric in a Deployment"
        Parameters:
            deployment_id (str): The uuid of the deployment
            custom_metric_id (str): The uuid of the custom metric to add data points to.
            options (List[CreateCustomMetric]): An instance list of create custom metric data points configuration options
        """

        metric_to_add = [CreateCustomMetricDataPoint(**options) for options in options_list]

        return self.__deeploy_service.create_custom_metric_data_points(
            self.__config.workspace_id, deployment_id, custom_metric_id, metric_to_add
        )

    def clear_custom_metric_data_points(
        self, deployment_id: str, custom_metric_id: str
    ) -> List[Dict]:
        """Clear custom metric datapoints of a custom metric in a Deployment"
        Parameters:
            deployment_id (str): The uuid of the deployment
            custom_metric_id (str): The uuid of the custom metric to clear
        """

        return self.__deeploy_service.clear_custom_metric_data_points(
            self.__config.workspace_id, deployment_id, custom_metric_id
        )

    def predict(self, deployment_id: str, request_body: dict) -> dict:
        """Make a predict call
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            request_body (dict): Request body with input data for the model
        """

        return self.__deeploy_service.predict(
            self.__config.workspace_id, deployment_id, request_body
        )

    def explain(self, deployment_id: str, request_body: dict, image: bool = False) -> object:
        """Make an explain call
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            request_body (dict): Request body with input data for the model
            image (bool): Return image or not
        """

        return self.__deeploy_service.explain(
            self.__config.workspace_id, deployment_id, request_body, image
        )

    def completions(self, deployment_id: str, request_body: dict, explain: bool = False) -> object:
        """Make a completion call
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            request_body (dict): Request body with input data for the model
            explain (bool): Return explanation if standard explainer is deployed
        """

        return self.__deeploy_service.completions(
            self.__config.workspace_id, deployment_id, request_body, explain
        )

    def chat_completions(self, deployment_id: str, request_body: dict) -> object:
        """Make a completion call
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            request_body (dict): Request body with input data for the model
        """

        return self.__deeploy_service.chat_completions(
            self.__config.workspace_id, deployment_id, request_body
        )

    def embeddings(self, deployment_id: str, request_body: dict) -> object:
        """Make a embedding call
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            request_body (dict): Request body with input data for the model
        """

        return self.__deeploy_service.embeddings(
            self.__config.workspace_id, deployment_id, request_body
        )

    def get_request_logs(
        self,
        deployment_id: str,
        params: Union[GetRequestLogsOptions, dict],
        include_raw_body: bool = False,
    ) -> List[RequestLog]:
        """Retrieve request logs
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            params (GetRequestLogsOptions): An instance of the GetRequestLogsOptions class
                containing the params used for the retrieval of request logs
            include_raw_body (bool): Whether to include the raw request and response body in the logs
        """
        if isinstance(params, dict):
            params = GetRequestLogsOptions(**params)

        request_logs = self.__deeploy_service.get_request_logs(
            self.__config.workspace_id, deployment_id, params, include_raw_body
        )
        return [RequestLog.model_validate(item) for item in request_logs]

    def get_prediction_logs(
        self, deployment_id: str, params: Union[GetPredictionLogsOptions, dict]
    ) -> List[PredictionLog]:
        """Retrieve prediction logs
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            params (GetPredictionLogsOptions): An instance of the GetPredictionLogsOptions class
                containing the params used for the retrieval of prediction logs
        """
        if isinstance(params, dict):
            params = GetPredictionLogsOptions(**params)

        prediction_logs = self.__deeploy_service.get_prediction_logs(
            self.__config.workspace_id, deployment_id, params
        )
        return [PredictionLog.model_validate(item) for item in prediction_logs]

    def evaluate(
        self,
        deployment_id: str,
        prediction_log_id: str,
        evaluation_input: CreateEvaluation,
    ) -> dict:
        """Evaluate a prediction log
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            log_id (int): ID of the log to be evaluated
            evaluation_input (CreateEvaluation): An instance of the CreateEvaluation class
                containing the evaluation input
        """

        return self.__deeploy_service.evaluate(
            self.__config.workspace_id,
            deployment_id,
            prediction_log_id,
            CreateEvaluation(**evaluation_input),
        )

    def upload_actuals(
        self, deployment_id: str, actuals_input: CreateActuals
    ) -> List[ActualResponse]:
        """Upload actuals for prediction logs
        Parameters:
            deployment_id (str): ID of the Deeploy deployment
            actuals_input (CreateActuals): An instance of the CreateActuals class
                containing the prediction log id's and corresponding actuals
        """

        return self.__deeploy_service.actuals(
            self.__config.workspace_id, deployment_id, CreateActuals(**actuals_input)
        )

    def generate_metadata_json(self, target_path: str, metadata_input: dict) -> str:
        """Generate a metadata.json file
        Parameters:
            target_path (str): Absolute path to the directory in which the
                metadata.json should be saved.
            metadata_input (dict, Metadata): The keys and values you would like to include
                in your metadata.json
        """
        # validate against metadata class
        return self.__file_service.generate_metadata_json(target_path, metadata_input)

    def generate_model_reference_json(
        self, target_path: str, reference_input: Union[CreateModelReference, dict]
    ) -> ModelReferenceJson:
        """Generate a reference.json file for your model
        Parameters:
            target_path (str): Absolute path to the directory in which the
                model directory with reference.json file should be saved.
            reference_input (CreateModelReference): An instance of the CreateModelReference
                class containing the configuration options of your model
        """
        if isinstance(reference_input, dict):
            reference_input = CreateModelReference(**reference_input)

        return self.__file_service.generate_reference_json(target_path, reference_input)

    def generate_explainer_reference_json(
        self, target_path: str, reference_input: CreateExplainerReference
    ) -> ExplainerReferenceJson:
        """Generate a reference.json file for your explainer
        Parameters:
            target_path (str): Absolute path to the directory in which the
                explainer directory with reference.json file should be saved.
            reference_input (CreateExplainerReference): An instance of the CreateExplainerReference
                class containing the configuration options of your explainer
        """

        return self.__file_service.generate_reference_json(
            target_path, CreateExplainerReference(**reference_input)
        )

    def generate_transformer_reference_json(
        self, target_path: str, reference_input: CreateTransformerReference
    ) -> TransformerReferenceJson:
        """Generate a reference.json file for your transformer
        Parameters:
            target_path (str): Absolute path to the directory in which the
                transformer directory with reference.json file should be saved.
            reference_input (CreateTransformerReference): An instance of the CreateTransformerReference
                class containing the configuration options of your transformer
        """

        return self.__file_service.generate_reference_json(
            target_path, CreateTransformerReference(**reference_input)
        )

    def set_deployment_token(self, deployment_token) -> None:
        """Sets a new deployment token for future requests, usefull when using short lived JWTs
        Parameters:
            deployment_token (str): token used for authenticating with Deployments
        """
        self.__deeploy_service.set_token(deployment_token)

    def create_guardrail(
        self, options: Union[CreateGuardrail, dict]
    ) -> Guardrail:
        """Create a guardrail in a Workspace"
        Parameters:
            options (CreateGuardrail): An instance of the CreateGuardrail class
                containing the guardrail configuration options
        """
        if isinstance(options, dict):
            options = CreateGuardrail(**options)

        return Guardrail.model_validate(
            self.__deeploy_service.create_guardrail(self.__config.workspace_id, options)
        )

    def get_all_guardrails_for_workspace(self) -> List[Guardrail]:
        """Get all guardrails from your Workspace"""

        return self.__deeploy_service.get_all_guardrails_for_workspace(self.__config.workspace_id)
