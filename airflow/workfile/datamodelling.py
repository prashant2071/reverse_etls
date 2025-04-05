import pandas as pd
import json
from airflow.providers.postgres.hooks.postgres import PostgresHook

POSTGRES_CONN_ID='postgres_default'
url = "https://raw.githubusercontent.com/prashant2071/bank_csv_files/refs/heads/main/titanic.csv"
df = pd.read_csv(url)

data = df.to_dict(orient = 'records')

def modelling_data(data):
    """Modelling the data."""
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    # Adjusted schema with appropriate data types
  
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS titanic(
                   passengerId INT, 
                   survived INT,  
                   pclass VARCHAR(255),    
                   name VARCHAR(255),
                   sex VARCHAR(255),
                   age INT,       
                   parch INT,   
                   ticket VARCHAR(255),
                   fare VARCHAR(255)
                   )
        """)
    
    # Validate and insert data
    for item in data:
        try:
            survived = int(item["Survived"]) if pd.notnull(item["Survived"]) else None
            age = int(item["Age"]) if pd.notnull(item["Age"]) else None
            parch = int(item["Parch"]) if pd.notnull(item["Age"]) else None

            cursor.execute("""
         INSERT INTO titanic(passengerId, survived, pclass, name, sex, age, parch, ticket, fare)
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
         """, (item["PassengerId"],survived, item['Pclass'], item["Name"], item["Sex"], age, parch, item["Ticket"], item["Fare"]))
        except (ValueError, TypeError) as e:
            print(f"invalid record: {item}, Error: {e}")
    
    conn.commit()
    cursor.close()

modelling_data(data)