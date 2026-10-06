import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()
client = bigquery.Client(project=os.environ["GCP_PROJECT_ID"])
print(list(client.query("SELECT 1 AS ok").result()))