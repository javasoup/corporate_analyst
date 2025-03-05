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
