from typing import Dict, List, Optional

import requests

from deeploy.enums import AuthType
from deeploy.enums.artifact import Artifact
from deeploy.models import (
    CreateActuals,
    CreateAzureMLDeployment,
    CreateCustomMetric,
    CreateCustomMetricDataPoint,
    CreateDeployment,
    CreateEnvironmentVariable,
    CreateEvaluation,
    CreateExternalDeployment,
    CreateGuardrail,
    CreateRegistrationDeployment,
    CreateSageMakerDeployment,
    Deployment,
    EnvironmentVariable,
    GetPredictionLogsOptions,
    UpdateAzureMLDeployment,
    UpdateCustomMetric,
    UpdateDeployment,
    UpdateDeploymentDescription,
    UpdateExternalDeployment,
    UpdateRegistrationDeployment,
    UpdateSageMakerDeployment,
)
from deeploy.models.create_job_schedule import CreateJobSchedule
from deeploy.models.get_request_logs_options import GetRequestLogsOptions
from deeploy.models.guardrail import Guardrail
from deeploy.models.test_job_schedule import TestJobSchedule
from deeploy.models.update_job_schedule import UpdateJobSchedule


class DeeployService:
    """
    A class for interacting with the Deeploy API
    """

    request_timeout = 300

    def __init__(
        self,
        host: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        token: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> None:
        if not (access_key and secret_key) and not token:
            raise Exception(
                "No authentication method provided. Please provide a token or personal key pair"
            )
        self.set_config(
            host=host,
            access_key=access_key,
            secret_key=secret_key,
            token=token,
            organization_id=organization_id,
        )

    def set_config(
        self,
        host: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        token: Optional[str] = None,
        organization_id: Optional[str] = None,
        insecure: Optional[bool] = False,
    ):
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__token = token
        self.__host = f"http://api.{host}" if insecure else f"https://api.{host}"
        if not (access_key and secret_key) and not token:
            raise Exception(
                "No authentication method provided. Please provide a token or personal key pair"
            )

        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__token = token
        self.__organization_id = organization_id
        self.__host = f"https://api.{host}"
        self.__request_session = requests.Session()

        if organization_id:
            self.__request_session.headers.update({"organization-id": organization_id})
        if access_key and secret_key:
            self.__request_session.auth = (access_key, secret_key)

    def get_repositories(self, workspace_id: str) -> dict:
        url = "%s/workspaces/%s/repositories" % (self.__host, workspace_id)
        self.__set_auth(AuthType.BASIC)
        repositories_response = self.__request_session.get(
            url,
            timeout=self.request_timeout,
        )

        return repositories_response.json()

    def create_environment_variable(
        self, workspace_id: str, environment_variable: CreateEnvironmentVariable
    ) -> dict:
        url = "%s/workspaces/%s/environmentVariables" % (self.__host, workspace_id)
        data = environment_variable.to_request_body()
        self.__set_auth(AuthType.BASIC)
        environment_variable_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(environment_variable_response):
            raise Exception(
                "Failed to create environment variable: %s"
                % str(environment_variable_response.json())
            )

        return environment_variable_response.json()

    def get_all_environment_variables(self, workspace_id: str) -> List[EnvironmentVariable]:
        url = "%s/workspaces/%s/environmentVariables" % (self.__host, workspace_id)
        self.__set_auth(AuthType.BASIC)
        environment_variables_response = self.__request_session.get(
            url,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(environment_variables_response):
            raise Exception("Failed to get environment variables.")

        return environment_variables_response.json()

    def get_environment_variable_ids_for_deployment_artifact(
        self, workspace_id: str, deployment_id: str, artifact: Artifact
    ) -> List[str]:
        url = "%s/workspaces/%s/environmentVariables/raw" % (self.__host, workspace_id)
        params = {
            "deploymentId": "eq:%s" % deployment_id,
            "artifact": "eq:%s" % artifact,
        }
        self.__set_auth(AuthType.BASIC)
        environment_variables_response = self.__request_session.get(
            url,
            params=params,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(environment_variables_response):
            raise Exception("Failed to get environment variables.")

        raw_environment_variables = environment_variables_response.json()["data"]
        environment_variable_ids = list(map(lambda env: env["id"], raw_environment_variables))

        return environment_variable_ids

    def get_deployment(
        self, workspace_id: str, deployment_id: str, withExamples: bool = False
    ) -> Deployment:
        url = "%s/workspaces/%s/deployments/%s" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        params = {}
        if withExamples:
            params["withExamples"] = withExamples

        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.get(
            url,
            params=params,
            timeout=self.request_timeout,
        )
        if not self.__request_is_successful(deployment_response):
            raise Exception(
                "Failed to retrieve the deployment: %s" % str(deployment_response.json())
            )

        return deployment_response.json()

    def create_deployment(self, workspace_id: str, deployment: CreateDeployment) -> dict:
        url = "%s/workspaces/%s/deployments" % (self.__host, workspace_id)
        data = deployment.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to create the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def create_sagemaker_deployment(
        self, workspace_id: str, deployment: CreateSageMakerDeployment
    ) -> dict:
        url = "%s/workspaces/%s/deployments" % (self.__host, workspace_id)
        data = deployment.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to create the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def create_azure_ml_deployment(
        self, workspace_id: str, deployment: CreateAzureMLDeployment
    ) -> dict:
        url = "%s/workspaces/%s/deployments" % (self.__host, workspace_id)
        data = deployment.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to create the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def create_external_deployment(
        self, workspace_id: str, deployment: CreateExternalDeployment
    ) -> dict:
        url = "%s/workspaces/%s/deployments" % (self.__host, workspace_id)
        data = deployment.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.post(
            url,
            json=data,
            auth=(self.__access_key, self.__secret_key),
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to create the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def create_registration_deployment(
        self, workspace_id: str, deployment: CreateRegistrationDeployment
    ) -> dict:
        url = "%s/workspaces/%s/deployments" % (self.__host, workspace_id)
        data = deployment.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to create the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def update_deployment(
        self, workspace_id: str, deployment_id: str, update: UpdateDeployment
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        data = update.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.patch(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to update the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def update_sagemaker_deployment(
        self, workspace_id: str, deployment_id: str, update: UpdateSageMakerDeployment
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        data = update.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.patch(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to update the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def update_azure_ml_deployment(
        self, workspace_id: str, deployment_id: str, update: UpdateAzureMLDeployment
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        data = update.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.patch(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to update the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def update_external_deployment(
        self, workspace_id: str, deployment_id: str, update: UpdateExternalDeployment
    ) -> Deployment:
        url = "%s/workspaces/%s/deployments/%s" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        data = update.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.patch(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to update the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def update_registration_deployment(
        self, workspace_id: str, deployment_id: str, update: UpdateRegistrationDeployment
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        data = update.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.patch(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to update the Deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def update_deployment_description(
        self, workspace_id: str, deployment_id: str, update: UpdateDeploymentDescription
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s/description" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        data = update.to_request_body()
        self.__set_auth(AuthType.BASIC)
        deployment_response = self.__request_session.patch(
            url,
            json=data,
            timeout=self.request_timeout,
        )
        if not self.__request_is_successful(deployment_response):
            raise Exception("Failed to update the deployment: %s" % str(deployment_response.json()))

        return deployment_response.json()

    def create_job_schedule(self, workspace_id: str, options: CreateJobSchedule) -> dict:
        url = "%s/workspaces/%s/jobSchedules" % (
            self.__host,
            workspace_id,
        )
        data = options.to_request_body()
        self.__set_auth(AuthType.BASIC)
        job_schedule_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(job_schedule_response):
            raise Exception("Failed to create job schedule: %s" % str(job_schedule_response.json()))

        return job_schedule_response.json()

    def test_job_schedule(self, workspace_id: str, options: TestJobSchedule) -> List[Dict]:
        url = "%s/workspaces/%s/jobSchedules/test" % (
            self.__host,
            workspace_id,
        )
        data = options.to_request_body()
        self.__set_auth(AuthType.BASIC)
        data_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(data_response):
            raise Exception("Job schedule test failed: %s" % str(data_response.json()))

        return data_response.json()

    def update_job_schedule(
        self, workspace_id: str, job_schedule_id: str, options: UpdateJobSchedule
    ) -> dict:
        url = "%s/workspaces/%s/jobSchedules/%s" % (
            self.__host,
            workspace_id,
            job_schedule_id,
        )
        data = options.to_request_body()
        self.__set_auth(AuthType.BASIC)
        job_schedule_response = self.__request_session.patch(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(job_schedule_response):
            raise Exception("Failed to update job schedule: %s" % str(job_schedule_response.json()))

        return job_schedule_response.json()

    def deactivate_job_schedule(self, workspace_id: str, job_schedule_id: str) -> dict:
        url = "%s/workspaces/%s/jobSchedules/%s/deactivate" % (
            self.__host,
            workspace_id,
            job_schedule_id,
        )
        self.__set_auth(AuthType.BASIC)
        job_schedule_response = self.__request_session.patch(
            url,
            json={},
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(job_schedule_response):
            raise Exception(
                "Failed to deactivate job schedule: %s" % str(job_schedule_response.json())
            )

        return job_schedule_response.json()

    def activate_job_schedule(self, workspace_id: str, job_schedule_id: str) -> dict:
        url = "%s/workspaces/%s/jobSchedules/%s/activate" % (
            self.__host,
            workspace_id,
            job_schedule_id,
        )
        self.__set_auth(AuthType.BASIC)
        job_schedule_response = self.__request_session.patch(
            url,
            json={},
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(job_schedule_response):
            raise Exception(
                "Failed to activate job schedule: %s" % str(job_schedule_response.json())
            )

        return job_schedule_response.json()

    def predict(self, workspace_id: str, deployment_id: str, request_body: dict) -> dict:
        url = "%s/workspaces/%s/deployments/%s/predict" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        self.__set_auth(AuthType.ALL)
        prediction_response = self.__request_session.post(
            url,
            json=request_body,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(prediction_response):
            raise Exception(f"Failed to call predictive model: {prediction_response.json()}")

        return prediction_response.json()

    def explain(
        self,
        workspace_id: str,
        deployment_id: str,
        request_body: dict,
        image: bool = False,
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s/explain" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        params = {
            "image": str(image).lower(),
        }

        self.__set_auth(AuthType.ALL)
        explanation_response = self.__request_session.post(
            url,
            json=request_body,
            params=params,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(explanation_response):
            raise Exception(f"Failed to call explainer model: {explanation_response.json()}")

        explanation = explanation_response.json()
        return explanation

    def completions(
        self, workspace_id: str, deployment_id: str, request_body: dict, explain: bool = False
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s/completions" % (
            self.__host,
            workspace_id,
            deployment_id,
        )

        if explain:
            url += "?explain=true"

        self.__set_auth(AuthType.ALL)
        completion_response = self.__request_session.post(
            url,
            json=request_body,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(completion_response):
            raise Exception(f"Failed to fetch completion from model: {completion_response.json()}")

        return completion_response.json()

    def chat_completions(self, workspace_id: str, deployment_id: str, request_body: dict) -> dict:
        url = "%s/workspaces/%s/deployments/%s/chat/completions" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        self.__set_auth(AuthType.ALL)
        chat_completion_response = self.__request_session.post(
            url,
            json=request_body,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(chat_completion_response):
            raise Exception(
                f"Failed to fetch chat completion from model: {chat_completion_response.json()}"
            )

        return chat_completion_response.json()

    def embeddings(self, workspace_id: str, deployment_id: str, request_body: dict) -> dict:
        url = "%s/workspaces/%s/deployments/%s/embeddings" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        self.__set_auth(AuthType.ALL)
        embeddings_response = self.__request_session.post(
            url,
            json=request_body,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(embeddings_response):
            raise Exception(f"Failed to fetch embedding from model: {embeddings_response.json()}")

        return embeddings_response.json()

    def get_prediction_logs(
        self, workspace_id: str, deployment_id: str, params: GetPredictionLogsOptions
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s/predictionLogs" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        self.__set_auth(AuthType.ALL)

        logs_response = self.__request_session.get(
            url,
            params=params.to_params(),
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(logs_response):
            raise Exception("Failed to get logs.")

        return logs_response.json()

    def get_request_logs(
        self,
        workspace_id: str,
        deployment_id: str,
        params: GetRequestLogsOptions,
        include_raw_body: bool = False,
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s/requestLogs" % (
            self.__host,
            workspace_id,
            deployment_id,
        )

        params_to_send = params.to_params()
        if include_raw_body:
            params_to_send["includeRawBody"] = include_raw_body

        self.__set_auth(AuthType.ALL)
        logs_response = self.__request_session.get(
            url,
            params=params_to_send,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(logs_response):
            raise Exception("Failed to get logs.")

        return logs_response.json()

    def evaluate(
        self,
        workspace_id: str,
        deployment_id: str,
        prediction_log_id: str,
        evaluation_input: CreateEvaluation,
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s/predictionLogs/%s/evaluatePrediction" % (
            self.__host,
            workspace_id,
            deployment_id,
            prediction_log_id,
        )

        data = evaluation_input.to_request_body()
        self.__set_auth(AuthType.ALL)
        evaluation_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(evaluation_response):
            if evaluation_response.status_code == 409:
                raise Exception("Log has already been evaluated.")
            elif evaluation_response.status_code in (401, 403):
                raise Exception("No permission to perform this action.")
            else:
                raise Exception("Failed to submit evaluation: %s" % evaluation_response.json())

        return evaluation_response.json()

    def actuals(self, workspace_id: str, deployment_id: str, actuals_input: CreateActuals) -> dict:
        url = "%s/workspaces/%s/deployments/%s/actuals" % (
            self.__host,
            workspace_id,
            deployment_id,
        )

        data = actuals_input.to_request_body()
        self.__set_auth(AuthType.ALL)
        actuals_response = self.__request_session.put(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(actuals_response):
            raise Exception("Failed to submit actuals: %s" % actuals_response.json())

        return actuals_response.json()

    def set_token(self, deployment_token) -> None:
        self.__token = deployment_token

    def __request_is_successful(self, request: requests.Response) -> bool:
        return 200 <= request.status_code < 300

    def __set_auth(self, supported_auth: AuthType):
        if (self.__access_key and self.__secret_key) and (
            supported_auth == AuthType.BASIC or supported_auth == AuthType.ALL
        ):
            self.__request_session.auth = (self.__access_key, self.__secret_key)
        elif (self.__token) and (
            supported_auth == AuthType.TOKEN or supported_auth == AuthType.ALL
        ):
            self.__request_session.auth = None
            self.__request_session.headers.update({"Authorization": "Bearer " + self.__token})

        elif (self.__access_key and self.__secret_key) and not (
            supported_auth == AuthType.BASIC or supported_auth == AuthType.ALL
        ):
            raise ValueError(
                "This function currently does not support authenticating with personal access key, please use a deployment token instead."
            )
        else:
            raise ValueError(
                "This function currently does not support authenticating with deployment token, please use a personal access key instead."
            )

    def get_custom_metrics_with_chart_data(
        self, workspace_id: str, deployment_id: str
    ) -> List[dict]:
        url = "%s/workspaces/%s/deployments/%s/customMetricsChartData" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        self.__set_auth(AuthType.ALL)

        logs_response = self.__request_session.get(
            url,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(logs_response):
            raise Exception("Failed to get logs.")

        return logs_response.json()

    def get_custom_metrics(self, workspace_id: str, deployment_id: str) -> dict:
        url = "%s/workspaces/%s/deployments/%s/customMetrics" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        self.__set_auth(AuthType.ALL)

        logs_response = self.__request_session.get(
            url,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(logs_response):
            raise Exception("Failed to get logs.")

        return logs_response.json()

    def create_custom_metric(
        self, workspace_id: str, deployment_id: str, create_custom_metric: CreateCustomMetric
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s/customMetric" % (
            self.__host,
            workspace_id,
            deployment_id,
        )
        data = create_custom_metric.to_request_body()
        self.__set_auth(AuthType.BASIC)
        custom_metric_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(custom_metric_response):
            raise Exception(
                "Failed to create custom metric: %s" % str(custom_metric_response.json())
            )

        return custom_metric_response.json()

    def update_custom_metric(
        self,
        workspace_id: str,
        deployment_id: str,
        custom_metric_id: str,
        update_custom_metric: UpdateCustomMetric,
    ) -> dict:
        url = "%s/workspaces/%s/deployments/%s/customMetric/%s" % (
            self.__host,
            workspace_id,
            deployment_id,
            custom_metric_id,
        )
        data = update_custom_metric.to_request_body()
        self.__set_auth(AuthType.BASIC)
        custom_metric_response = self.__request_session.patch(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(custom_metric_response):
            raise Exception(
                "Failed to update custom metric: %s" % str(custom_metric_response.json())
            )

        return custom_metric_response.json()

    def delete_custom_metric(self, workspace_id: str, deployment_id: str, custom_metric_id: str):
        url = "%s/workspaces/%s/deployments/%s/customMetric/%s" % (
            self.__host,
            workspace_id,
            deployment_id,
            custom_metric_id,
        )
        self.__set_auth(AuthType.BASIC)
        custom_metric_response = self.__request_session.delete(
            url,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(custom_metric_response):
            raise Exception(
                "Failed to delete custom metric: %s" % str(custom_metric_response.json())
            )

        return

    def create_custom_metric_data_points(
        self,
        workspace_id: str,
        deployment_id: str,
        custom_metric_id: str,
        create_custom_metric_data_points: List[CreateCustomMetricDataPoint],
    ) -> List[dict]:
        url = "%s/workspaces/%s/deployments/%s/customMetric/%s/dataPoints" % (
            self.__host,
            workspace_id,
            deployment_id,
            custom_metric_id,
        )
        data = [
            create_custom_metric_data_point.to_request_body()
            for create_custom_metric_data_point in create_custom_metric_data_points
        ]
        self.__set_auth(AuthType.ALL)
        custom_metric_data_points_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(custom_metric_data_points_response):
            raise Exception(
                "Failed to create custom metric: %s"
                % str(custom_metric_data_points_response.json())
            )

        return custom_metric_data_points_response.json()

    def clear_custom_metric_data_points(
        self, workspace_id: str, deployment_id: str, custom_metric_id: str
    ):
        url = "%s/workspaces/%s/deployments/%s/customMetric/%s/dataPoints" % (
            self.__host,
            workspace_id,
            deployment_id,
            custom_metric_id,
        )
        self.__set_auth(AuthType.ALL)
        custom_metric_data_points_response = self.__request_session.delete(
            url,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(custom_metric_data_points_response):
            raise Exception(
                "Failed to delete data points of custom metric: %s"
                % str(custom_metric_data_points_response.json())
            )

        return
    
    def create_guardrail(
        self, workspace_id: str, guardrail: CreateGuardrail
    ) -> dict:
        url = "%s/workspaces/%s/guardrails" % (self.__host, workspace_id)
        data = guardrail.to_request_body()
        self.__set_auth(AuthType.BASIC)
        guardrail_response = self.__request_session.post(
            url,
            json=data,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(guardrail_response):
            raise Exception(
                "Failed to create guardrail: %s"
                % str(guardrail_response.json())
            )

        return guardrail_response.json()

    def get_all_guardrails_for_workspace(self, workspace_id: str) -> List[Guardrail]:
        url = "%s/workspaces/%s/guardrails" % (self.__host, workspace_id)
        self.__set_auth(AuthType.BASIC)
        guardrails_response = self.__request_session.get(
            url,
            timeout=self.request_timeout,
        )

        if not self.__request_is_successful(guardrails_response):
            raise Exception("Failed to get guardrails.")

        return guardrails_response.json()
