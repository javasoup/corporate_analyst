# Corporate Analyst Agent

## Purpose

Given a ticker symbol, this agent downloads the most recent 10-K report from the
SEC and corporate data from Zoominfo. 
It generates a report after analyzing all the information about the company from 
these sources.

## Prerequisites
* Generate an API key from sec-api.io for yourself and add it to the .env file
`SEC_API_KEY= YOUR_API_KEY`
* Add your Zoominfo credentials to the .env file as
`ZOOMINFO_USERNAME=YOUR_ZOOMINFO_USERNAME`
`ZOOMINFO_PASSWORD=YOUR_ZOOMINFO_PASSWORD`
* Add GOOGLE_CLOUD_PROJECT AND GOOGLE_CLOUD_LOCATION to the .env file
`GOOGLE_API_KEY=YOUR_API_KEY`
* Add GOOGLE_API_KEY to the .env file
`GOOGLE_CLOUD_PROJECT=PROJECT_ID`
`GOOGLE_CLOUD_LOCATION=REGION` # currently only us-central1 is supported

* Check requirements.txt for python dependencies

## Setup AlloyDB

Enable AlloyDB in your Google Project
```
gcloud services enable alloydb.googleapis.com --project = $GOOGLE_CLOUD_PROJECT
```

* Install psql client

```
sudo apt-get update
sudo apt-get install postgresql-client
```

Create terraform.tfvars (Recommended):
* Create a file named terraform.tfvars in the same directory as main.tf.
* Add the following lines, replacing the values with your actual values:

```
project_id = "your-project-id"
region = "us-central1"
db_pass = "your-strong-db-password"
#network_name = "your-network-name" # Uncomment if not using the default network
```

```
terraform init
terraform plan
terraform apply
```

Provide `Cloud SQL Client` role to the service account `service-$PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com` in the project where you are deploying the agent and the database.


Add the following additional parameters to the .env file after replacing your PASSWORD and PROJECT_ID

```
DB_USER=corporate-analyst-user
DB_PASS=YOUR-PASSWORD-HERE
DB_NAME=corporate-analyst-db
DB_CONNECTION_NAME="$PROJECT_ID$:us-central1:corporate-analyst-instance"
```


## Deploying the agent to Agent Engine
* Download the latest Agent Framework as a whl file
```
AGENTFRAMEWORK_BUCKET = "gs://agent_framework/latest"
%%capture output
!gsutil ls $AGENTFRAMEWORK_BUCKET
RELEASE_FILE = output.stdout.strip().split("/")[-1]
!gsutil cp {AGENTFRAMEWORK_BUCKET}/{RELEASE_FILE} .
```
Make sure that the agent_config in `agent_engine_app.py` refers to the right `whl` file.

* Create python virtual environment
* Enable Agent Engine API in your project 
* Run `python agent_engine_app.py` to deploy the agent to Agent Engine API. Track the logs in the Logs explorer.

## Test
* Run `python test.py`
