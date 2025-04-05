from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.exceptions import AirflowException
import requests
import time
from datetime import datetime,timedelta

def print_welcome():
    print('Welcome to Airflow!')
CLIENT_ID = "13c4ddd8-83c3-457d-8a57-22e8f3a1d73a"
CLIENT_SECRET = "JpYLjSu8ObVYhmZT9CCAl9zw2JJXjhtV"
AIRBYTE_TRIGGER_URL = "https://api.airbyte.com/v1/jobs"
# Airbyte Configuration
AIRBYTE_CONNECTION_ID = "d22193d6-ce77-4ca2-b336-03826b5174c3"
TOKEN_URL = "https://api.airbyte.com/v1/applications/token"
WORK_DIRECTORY = "/usr/local/airflow/workfile"
DBT_DIRECTORY = "/usr/local/airflow/dags/reverse_etl"
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
        time.sleep(15)
        return job_id
    else:
        raise AirflowException(
            f"Failed to trigger Airbyte connection. Response: {sync_response.text}"
        )
default_args = {
    'owner': 'airflow',
    'depend_on_past': False,
    'start_date': datetime(2025, 3, 8),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    dag_id='fetch_and_store_data',  # Fixed typo here
    default_args=default_args,
    description='A simple DAG to fetch data',
    schedule_interval=timedelta(days=1),
    catchup=False
)

starting_program = PythonOperator(
    task_id='welcome_task',  # Changed task_id to be more descriptive
    python_callable=print_welcome,
    dag=dag
)
fetching_and_modelling = BashOperator(
    task_id ="fetching_and_modelling",
    bash_command=f' cd {WORK_DIRECTORY} && python datamodelling.py',
    dag=dag
)
connecting_airbyte = PythonOperator(
    task_id ="retriving_data_from_postgres",
    python_callable=trigger_airbyte_sync,
    dag=dag
)
dbt_run = BashOperator(
    task_id ="trigger_dbt_run",
    bash_command=f' cd {DBT_DIRECTORY} && dbt run',
    dag=dag
)



starting_program >> fetching_and_modelling >>connecting_airbyte >> dbt_run