import os
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from dotenv import load_dotenv
load_dotenv() 


class App:
  def __init__(self):
    # load environment variables to local
    self.GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    self.GOOGLE_GENAI_USE_VERTEXAI=os.environ["GOOGLE_GENAI_USE_VERTEXAI"]
    self.GOOGLE_CLOUD_PROJECT=os.environ["GOOGLE_CLOUD_PROJECT"]
    self.GOOGLE_CLOUD_LOCATION=os.environ["GOOGLE_CLOUD_LOCATION"]
    self.SEC_API_KEY=os.environ["SEC_API_KEY"]
    self.ZOOMINFO_USERNAME=os.environ["ZOOMINFO_USERNAME"]
    self.ZOOMINFO_PASSWORD=os.environ["ZOOMINFO_PASSWORD"]

  def set_up(self) -> None:
    # load environment variables to remote from local
    os.environ["GOOGLE_API_KEY"]=self.GOOGLE_API_KEY
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"]=self.GOOGLE_GENAI_USE_VERTEXAI
    os.environ["GOOGLE_CLOUD_PROJECT"]=self.GOOGLE_CLOUD_PROJECT
    os.environ["GOOGLE_CLOUD_LOCATION"]=self.GOOGLE_CLOUD_LOCATION
    os.environ["SEC_API_KEY"]=self.SEC_API_KEY
    os.environ["ZOOMINFO_USERNAME"]=self.ZOOMINFO_USERNAME
    os.environ["ZOOMINFO_PASSWORD"]=self.ZOOMINFO_PASSWORD

    from agent import corporate_analyst_agent
    from agents.artifacts import InMemoryArtifactService
    from agents.sessions import InMemorySessionService
    from agents import Runner
     
    self.agent = corporate_analyst_agent
    self.artifact_service = InMemoryArtifactService()
    self.session_service = InMemorySessionService()
    self.runner = Runner(
        app_name="Corporate Analyst Agent",
        agent=self.agent,
        artifact_service=self.artifact_service,
        session_service=self.session_service,
    )

  from agents.sessions import Session
  def get_session(self, session_id: str) -> Session:
    session = self.session_service.get("Corporate Analyst Agent", "user", session_id)
    if not session:
      raise HTTPException(status_code=404, detail="Session not found")
    return session

  def list_sessions(self) -> list[str]:
    return self.session_service.list_sessions("Corporate Analyst Agent", "user")

  def create_session(
      self, session_id: str, context: Optional[dict[str, Any]] = None
  ) -> Session:
    return self.session_service.create(
        "Corporate Analyst Agent", "user", context, session_id=session_id
    )

  def delete_session(self, session_id: str):
    self.session_service.delete("Corporate Analyst Agent", "user", session_id)

  from agents.events import Event
  def agent_run(self, session_id: str, message: str) -> list[Event]:
    from google.genai import types
    #session = self.session_service.get("Corporate Analyst Agent", "user", session_id)
    session = self.get_session(session_id)
    if not session:
      raise HTTPException(status_code=404, detail="Session not found")

    return list(
        self.runner.run(
            session=session,
            new_message=types.Content.model_validate_json(message),
        )
    )

  def register_operations(self) -> Dict[str, List[str]]:
    return {
        "": [
            "get_session",
            "list_sessions",
            "create_session",
            "delete_session",
            "agent_run",
        ],
    }

def deploy_agent_engine_app():
    """Deploy the agent engine app to Vertex AI."""
    
    import vertexai
    from vertexai.preview import reasoning_engines
    GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
    GOOGLE_CLOUD_LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]


    staging_bucket = f"gs://{GOOGLE_CLOUD_PROJECT}-agent-engine-deploy"
    sts = True
    try:
      from google.cloud import storage
      storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
      bucket = storage_client.get_bucket(staging_bucket.replace("gs://", ""))
    except Exception as e:
      print(f"Bucket {staging_bucket} does not exist. Creating it now.")
      from google.cloud import storage
      storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
      bucket = storage_client.create_bucket(staging_bucket.replace("gs://", ""), location=GOOGLE_CLOUD_LOCATION)
      print(f"Bucket {bucket.name} created.")
      sts = False
    if sts:
      print(f"Bucket {staging_bucket} already exists.")

    vertexai.init(
      project=GOOGLE_CLOUD_PROJECT,
      location=GOOGLE_CLOUD_LOCATION,
      #api_endpoint=api_endpoint,
      staging_bucket=staging_bucket,
    )

    with open('requirements.txt', 'r') as file:
      reqs = file.read().splitlines()

    agent_config =  {
        "reasoning_engine" : App(),
        "display_name" : "Corporate Analyst",
        "requirements" : reqs+[
            "google_genai_agents-0.0.2.dev20250204+723246417-py3-none-any.whl",
            "google_cloud_aiplatform",
            "google_genai",
            "cloudpickle==3.1.1",
            "pydantic==2.10.6",
            "pytest",
            "overrides",
        ],
        "extra_packages" : [
            "google_genai_agents-0.0.2.dev20250204+723246417-py3-none-any.whl",
            "agent.py",
            "sec10ktool.py",
            "zoominfotool.py"
        ],
    }
  

    existing_agents=reasoning_engines.ReasoningEngine.list(filter='display_name="Corporate Analyst"')

    if existing_agents:
      #update the existing agent
      remote_app = existing_agents[0].update(**agent_config)
    else:
      #create a new agent
      remote_app = reasoning_engines.ReasoningEngine.create(**agent_config)
      
    return remote_app


if __name__ == "__main__":
    deploy_agent_engine_app()

