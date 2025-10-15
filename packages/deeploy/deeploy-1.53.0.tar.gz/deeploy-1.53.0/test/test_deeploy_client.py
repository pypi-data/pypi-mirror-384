import pytest
import requests_mock

from deeploy.client import Client
from deeploy.enums import ExplainerType, ModelType
from deeploy.enums.external_url_authentication_method import ExternalUrlAuthenticationMethod
from deeploy.models import (
    CreateAzureMLDeployment,
    CreateExternalDeployment,
    CreateRegistrationDeployment,
    Deployment,
    Repository,
    RequestLog,
)
from deeploy.models.get_request_logs_options import GetRequestLogsOptions
from deeploy.services import DeeployService

WORKSPACE_ID = "abc"


@pytest.fixture(scope="session")
def deeploy_client():
    return Client(
        host="test.deeploy.ml",
        access_key="abc",
        secret_key="def",
        workspace_id="abc",
    )


def test_get_repositories(deeploy_client):
    WORKSPACE_ID = "abc"
    return_object = [
        {
            "id": "def",
            "teamId": "hij",
            "name": "repo 1",
            "status": 1,
            "workspaceId": WORKSPACE_ID,
            "isPublic": False,
            "remotePath": "git@github.com/example/example.git",
            "createdAt": "2021-03-17T12:55:10.983Z",
            "updatedAt": "2021-03-17T12:55:10.983Z",
        },
        {
            "id": "ghi",
            "teamId": "klm",
            "name": "repo 2",
            "status": 0,
            "workspaceId": WORKSPACE_ID,
            "remotePath": "git@gitlab.com/example/example.git",
            "createdAt": "2021-03-17T12:55:10.983Z",
            "updatedAt": "2021-03-17T12:55:10.983Z",
        },
    ]
    expected_output = [
        Repository(
            id="def",
            teamId="hij",
            name="repo 1",
            status=1,
            workspaceId=WORKSPACE_ID,
            isPublic=False,
            remotePath="git@github.com/example/example.git",
            createdAt="2021-03-17T12:55:10.983Z",
            updatedAt="2021-03-17T12:55:10.983Z",
        ),
        Repository(
            id="ghi",
            teamId="klm",
            name="repo 2",
            status=0,
            workspaceId=WORKSPACE_ID,
            remotePath="git@gitlab.com/example/example.git",
            createdAt="2021-03-17T12:55:10.983Z",
            updatedAt="2021-03-17T12:55:10.983Z",
        ),
    ]
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.test.deeploy.ml/workspaces/%s/repositories" % WORKSPACE_ID,
            json=return_object,
        )
        repositories = deeploy_client.get_repositories()
        assert repositories == expected_output


def test_create_azure_ml_deployment(deeploy_client):
    return_object = {
        "id": "63921818-f908-44d6-af72-17e9beef7b6c",
        "teamId": "63921818-f908-44d6-af72-17e9beef7b6c",
        "name": "client test",
        "workspaceId": WORKSPACE_ID,
        "riskClassification": "unclassified",
        "ownerId": "9f39d8b4-b661-43ef-a81f-e8f8dded8c5a",
        "publicURL": "https://api.ute.deeploy.ml/workspaces/e7942eeb-3e7e-4d27-a413-23f49a0f24f3/"
        + "deployments/63921818-f908-44d6-af72-17e9beef7b6c/predict",
        "description": "the first test",
        "status": 1,
        "createdAt": "2021-03-17T14:59:35.203Z",
        "updatedAt": "2021-03-17T14:59:35.203Z",
    }
    expected_output = Deployment(
        **{
            "id": "63921818-f908-44d6-af72-17e9beef7b6c",
            "teamId": "63921818-f908-44d6-af72-17e9beef7b6c",
            "name": "client test",
            "workspaceId": WORKSPACE_ID,
            "riskClassification": "unclassified",
            "ownerId": "9f39d8b4-b661-43ef-a81f-e8f8dded8c5a",
            "publicURL": "https://api.ute.deeploy.ml/workspaces/e7942eeb-3e7e-4d27-a413-23f49a0f24f3/"
            + "deployments/63921818-f908-44d6-af72-17e9beef7b6c/predict",
            "description": "the first test",
            "status": 1,
            "createdAt": "2021-03-17T14:59:35.203Z",
            "updatedAt": "2021-03-17T14:59:35.203Z",
        }
    )
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.test.deeploy.ml/workspaces/%s/deployments" % WORKSPACE_ID,
            json=return_object,
        )
        deployment = deeploy_client.create_azure_ml_deployment(
            CreateAzureMLDeployment(
                **{
                    "name": "client test",
                    "description": "the first test",
                    "repository_id": "dcd35835-5e5a-4d9a-9116-8732131ed6e2",
                    "branch_name": "master",
                    "commit": "978b9cd9-f6cf-4f93-83de-ac669046a3e8",
                    "model_type": ModelType.SKLEARN,
                    "model_serverless": False,
                    "explainer_type": ExplainerType.SHAP_KERNEL,
                    "explainer_serverless": False,
                }
            ),
        )
        assert deployment == expected_output


def test_create_external_deployment(deeploy_client):
    return_object = {
        "id": "63921818-f908-44d6-af72-17e9beef7b6c",
        "teamId": "63921818-f908-44d6-af72-17e9beef7b6c",
        "name": "client test",
        "workspaceId": WORKSPACE_ID,
        "riskClassification": "unclassified",
        "ownerId": "9f39d8b4-b661-43ef-a81f-e8f8dded8c5a",
        "publicURL": "https://api.ute.deeploy.ml/workspaces/e7942eeb-3e7e-4d27-a413-23f49a0f24f3/"
        + "deployments/63921818-f908-44d6-af72-17e9beef7b6c/predict",
        "description": "the first test",
        "status": 1,
        "createdAt": "2021-03-17T14:59:35.203Z",
        "updatedAt": "2021-03-17T14:59:35.203Z",
    }
    expected_output = Deployment(
        **{
            "id": "63921818-f908-44d6-af72-17e9beef7b6c",
            "teamId": "63921818-f908-44d6-af72-17e9beef7b6c",
            "name": "client test",
            "workspaceId": WORKSPACE_ID,
            "riskClassification": "unclassified",
            "ownerId": "9f39d8b4-b661-43ef-a81f-e8f8dded8c5a",
            "publicURL": "https://api.ute.deeploy.ml/workspaces/e7942eeb-3e7e-4d27-a413-23f49a0f24f3/"
            + "deployments/63921818-f908-44d6-af72-17e9beef7b6c/predict",
            "description": "the first test",
            "status": 1,
            "createdAt": "2021-03-17T14:59:35.203Z",
            "updatedAt": "2021-03-17T14:59:35.203Z",
        }
    )
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.test.deeploy.ml/workspaces/%s/deployments" % WORKSPACE_ID,
            json=return_object,
        )
        deployment = deeploy_client.create_external_deployment(
            CreateExternalDeployment(
                **{
                    "name": "client test",
                    "description": "the first test",
                    "url": "https://testurl.com",
                    "repository_id": None,
                    "branch_name": None,
                    "commit": None,
                    "authentication": ExternalUrlAuthenticationMethod.NONE.value,
                }
            ),
        )
        assert deployment == expected_output


def test_create_registration_deployment(deeploy_client):
    return_object = {
        "id": "63921818-f908-44d6-af72-17e9beef7b6c",
        "teamId": "63921818-f908-44d6-af72-17e9beef7b6c",
        "name": "client test",
        "workspaceId": WORKSPACE_ID,
        "riskClassification": "unclassified",
        "ownerId": "9f39d8b4-b661-43ef-a81f-e8f8dded8c5a",
        "publicURL": "https://api.ute.deeploy.ml/workspaces/e7942eeb-3e7e-4d27-a413-23f49a0f24f3/"
        + "deployments/63921818-f908-44d6-af72-17e9beef7b6c/predict",
        "description": "the first test",
        "status": 1,
        "createdAt": "2021-03-17T14:59:35.203Z",
        "updatedAt": "2021-03-17T14:59:35.203Z",
    }
    expected_output = Deployment(
        **{
            "id": "63921818-f908-44d6-af72-17e9beef7b6c",
            "teamId": "63921818-f908-44d6-af72-17e9beef7b6c",
            "name": "client test",
            "workspaceId": WORKSPACE_ID,
            "riskClassification": "unclassified",
            "ownerId": "9f39d8b4-b661-43ef-a81f-e8f8dded8c5a",
            "publicURL": "https://api.ute.deeploy.ml/workspaces/e7942eeb-3e7e-4d27-a413-23f49a0f24f3/"
            + "deployments/63921818-f908-44d6-af72-17e9beef7b6c/predict",
            "description": "the first test",
            "status": 1,
            "createdAt": "2021-03-17T14:59:35.203Z",
            "updatedAt": "2021-03-17T14:59:35.203Z",
        }
    )
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.test.deeploy.ml/workspaces/%s/deployments" % WORKSPACE_ID,
            json=return_object,
        )
        deployment = deeploy_client.create_registration_deployment(
            CreateRegistrationDeployment(
                **{
                    "name": "client test",
                    "description": "the first test",
                    "repository_id": "dcd35835-5e5a-4d9a-9116-8732131ed6e2",
                    "branch_name": "master",
                    "commit": "978b9cd9-f6cf-4f93-83de-ac669046a3e8",
                }
            ),
        )
        assert deployment == expected_output

    deployment_id = "abc"
    return_object = {
        "data": {
            "id": deployment_id,
            "teamId": "63921818-f908-44d6-af72-17e9beef7b6c",
            "name": "client test",
            "workspaceId": WORKSPACE_ID,
            "riskClassification": "unclassified",
            "ownerId": "9f39d8b4-b661-43ef-a81f-e8f8dded8c5a",
            "publicURL": "https://api.ute.deeploy.ml/workspaces/e7942eeb-3e7e-4d27-a413-23f49a0f24f3/"
            + "deployments/63921818-f908-44d6-af72-17e9beef7b6c/predict",
            "description": "client test",
            "status": 1,
            "createdAt": "2021-03-17T14:59:35.203Z",
            "updatedAt": "2021-03-17T14:59:35.203Z",
        }
    }
    expected_output = Deployment(
        **{
            "id": deployment_id,
            "teamId": "63921818-f908-44d6-af72-17e9beef7b6c",
            "name": "client test",
            "workspaceId": WORKSPACE_ID,
            "riskClassification": "unclassified",
            "ownerId": "9f39d8b4-b661-43ef-a81f-e8f8dded8c5a",
            "publicURL": "https://api.ute.deeploy.ml/workspaces/e7942eeb-3e7e-4d27-a413-23f49a0f24f3/"
            + "deployments/63921818-f908-44d6-af72-17e9beef7b6c/predict",
            "description": "client test",
            "status": 1,
            "createdAt": "2021-03-17T14:59:35.203Z",
            "updatedAt": "2021-03-17T14:59:35.203Z",
        }
    )


def test_get_request_logs(deeploy_client):
    return_object = [
        {
            "id": "bac4848a-e7bd-4af6-821d-2e384dc016cc",
            "teamId": "bac4848a-e7bd-4af6-821d-2e384dc016cc",
            "deploymentId": "ccadb1a1-9036-418c-9936-3f7ac6c4ec8c",
            "commit": "4c1a62d",
            "requestContentType": "application/json",
            "responseTimeMS": 26,
            "statusCode": 500,
            "tokenId": "b6d8c781-2526-4e03-9b43-4c1a62d064db",
            "createdAt": "2021-05-06T15:36:07.597Z",
        }
    ]

    expected_output = [
        RequestLog(
            **{
                "id": "bac4848a-e7bd-4af6-821d-2e384dc016cc",
                "teamId": "bac4848a-e7bd-4af6-821d-2e384dc016cc",
                "deploymentId": "ccadb1a1-9036-418c-9936-3f7ac6c4ec8c",
                "commit": "4c1a62d",
                "requestContentType": "application/json",
                "responseTimeMS": 26,
                "statusCode": 500,
                "tokenId": "b6d8c781-2526-4e03-9b43-4c1a62d064db",
                "createdAt": "2021-05-06T15:36:07.597Z",
            }
        ),
    ]

    with requests_mock.Mocker() as m:
        m.get(
            "https://api.test.deeploy.ml/workspaces/%s/deployments/%s/requestLogs"
            % (WORKSPACE_ID, "20c2593d-e09d-4246-be84-46f81a40a7d4"),
            json=return_object,
        )
        logs = deeploy_client.get_request_logs(
            deployment_id="20c2593d-e09d-4246-be84-46f81a40a7d4",
            params=GetRequestLogsOptions(**{}),
        )
        assert logs == expected_output

    with requests_mock.Mocker() as m:
        m.get(
            "https://api.test.deeploy.ml/workspaces/%s/deployments/%s/requestLogs"
            % (WORKSPACE_ID, "20c2593d-e09d-4246-be84-46f81a40a7d4"),
            status_code=400,
        )
        with pytest.raises(Exception):
            deeploy_client.get_request_logs(
                workspace_id=WORKSPACE_ID,
                deployment_id="20c2593d-e09d-4246-be84-46f81a40a7d4",
            )


def test_evaluate(deeploy_client: DeeployService):
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.test.deeploy.ml/workspaces/%s/deployments/%s/requestLogs/%s/predictionLogs/%s/evaluations"
            % (WORKSPACE_ID, "20c2593d-e09d-4246-be84-46f81a40a7d4", "abc", "abc"),
            status_code=401,
        )
        with pytest.raises(Exception):
            deeploy_client.evaluate(
                deployment_id="20c2593d-e09d-4246-be84-46f81a40a7d4",
                request_log_id="abc",
                prediction_log_id="abc",
                evaluation_input={},
            )
