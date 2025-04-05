import requests
from airflow.exceptions import AirflowException
from datetime import timedelta
# Airbyte Application Credentials
CLIENT_ID = "e146d038-d69b-4ff0-a565-04d465d6a86c"
CLIENT_SECRET = "dPaBEdG6P2vsZ9bjC8pZsa1xsJ344Sr9"
AIRBYTE_TRIGGER_URL = "https://api.airbyte.com/v1/jobs"
# Airbyte Configuration
AIRBYTE_CONNECTION_ID = "d22193d6-ce77-4ca2-b336-03826b5174c3"
TOKEN_URL = "https://api.airbyte.com/v1/applications/token"
def get_airbyte_bearer_token(client_id, client_secret):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
    }
    payload = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    try:
        response = requests.post(TOKEN_URL, json=payload, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise Exception("Failed to retrieve access token")
            print(f"Access token retrieved: {access_token}")
            return access_token
        else:
            raise Exception(
                f"Failed to retrieve token. "
                f"Status code: {response.status_code}, Response: {response.text}"
            )
    except requests.RequestException as e:
        raise AirflowException(f"An error occurred: {str(e)}")
def trigger_airbyte_sync(**context):
    bearer_token = get_airbyte_bearer_token(CLIENT_ID, CLIENT_SECRET)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    sync_payload = {
        "connectionId": AIRBYTE_CONNECTION_ID,
        "jobType": "sync"
        }
    sync_response = requests.post(AIRBYTE_TRIGGER_URL, json=sync_payload, headers=headers)
    if sync_response.status_code == 200:
        response_json = sync_response.json()
        job_id = response_json.get("jobId")
        context['ti'].xcom_push(key='job_id', value=job_id)
        print(f"Connection triggered successfully. Job ID: {job_id}")
        return job_id
    else:
        raise AirflowException(
            f"Failed to trigger Airbyte connection. Response: {sync_response.text}"
        )
trigger_airbyte_sync()