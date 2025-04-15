import vertexai
import os
from vertexai import agent_engines
from dotenv import load_dotenv

class App:
    def __init__(self):
        load_dotenv()
        self.GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
        self.GOOGLE_CLOUD_LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]
        self.SEC_API_KEY=os.environ["SEC_API_KEY"]
        self.ZOOMINFO_USERNAME=os.environ["ZOOMINFO_USERNAME"]
        self.ZOOMINFO_PASSWORD=os.environ["ZOOMINFO_PASSWORD"]
        self.PROXYCURL_API_KEY=os.environ["PROXYCURL_API_KEY"]
        self.DB_USER=os.environ["DB_USER"]
        self.DB_PASS=os.environ["DB_PASS"]
        self.DB_NAME=os.environ["DB_NAME"]
        self.DB_CONNECTION_NAME=os.environ["DB_CONNECTION_NAME"]
        self.ENABLE_SEC_API_CALLS=os.environ["ENABLE_SEC_API_CALLS"]
        self.ENABLE_ZOOMINFO_API_CALLS=os.environ["ENABLE_ZOOMINFO_API_CALLS"]
        self.ENABLE_NUBELA_API_CALLS=os.environ["ENABLE_NUBELA_API_CALLS"]
        self.NUBELA_ENRICHMENT_DATA_TIMELIMIT=os.environ["NUBELA_ENRICHMENT_DATA_TIMELIMIT"]
        

    def set_up(self):

        import os

        os.environ["GOOGLE_CLOUD_PROJECT"] = self.GOOGLE_CLOUD_PROJECT
        os.environ["GOOGLE_CLOUD_LOCATION"] = self.GOOGLE_CLOUD_LOCATION
        os.environ["SEC_API_KEY"] = self.SEC_API_KEY
        os.environ["ZOOMINFO_USERNAME"] = self.ZOOMINFO_USERNAME
        os.environ["ZOOMINFO_PASSWORD"] = self.ZOOMINFO_PASSWORD
        os.environ["PROXYCURL_API_KEY"] = self.PROXYCURL_API_KEY
        os.environ["DB_USER"] = self.DB_USER
        os.environ["DB_PASS"] = self.DB_PASS
        os.environ["DB_NAME"] = self.DB_NAME
        os.environ["DB_CONNECTION_NAME"] = self.DB_CONNECTION_NAME
        os.environ["ENABLE_SEC_API_CALLS"] = self.ENABLE_SEC_API_CALLS
        os.environ["ENABLE_ZOOMINFO_API_CALLS"] = self.ENABLE_ZOOMINFO_API_CALLS
        os.environ["ENABLE_NUBELA_API_CALLS"] = self.ENABLE_NUBELA_API_CALLS
        os.environ["NUBELA_ENRICHMENT_DATA_TIMELIMIT"] = self.NUBELA_ENRICHMENT_DATA_TIMELIMIT
        

        from agent import root_agent
        ROOT_AGENT=root_agent # the name of the root agent in agent.py
        
        from vertexai.preview.reasoning_engines import AdkApp

        self.app = AdkApp(
            agent=ROOT_AGENT,
            enable_tracing=True,
        )
    def create_session(self, **kw_args):
        return self.app.create_session(**kw_args)
    
    def delete_session(self, **kw_args):
        return self.app.delete_session(**kw_args)
    
    def list_sessions(self, **kw_args):
        return self.app.list_sessions(**kw_args)
    
    def get_session(self, **kw_args):
        return self.app.get_session(**kw_args)
    
    def streaming_agent_run_with_events(self, **kw_args):
        return self.app.streaming_agent_run_with_events(**kw_args)
    
    def stream_query(self, **kw_args):
        return self.app.stream_query(**kw_args)
    
    
    def register_operations(self):
        return {
            "": [
                "get_session",
                "list_sessions",
                "create_session",
                "delete_session",
            ],
            "stream": [
                "streaming_agent_run_with_events",
                "stream_query",
                ],
        }
        

def deploy_agent_engine_app():
    load_dotenv() 

    GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
    GOOGLE_CLOUD_LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]
    STAGING_BUCKET = f"gs://{GOOGLE_CLOUD_PROJECT}-agent-engine-deploy"
    #WHL_FILE =  "google_adk-0.0.2.dev20250404+nightly743987168-py3-none-any.whl"
    AGENT_DISPLAY_NAME="Corporate Analyst"
    #AGENT_APP_NAME="corporate_analyst_app"
  
    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    with open('requirements.txt', 'r') as file:
        reqs = file.read().splitlines()

    agent_config =  {
        "agent_engine" : App(),
        "display_name" : AGENT_DISPLAY_NAME,
        "requirements" : reqs+[
             #WHL_FILE,
            #"google-cloud-aiplatform[agent_engines] @ git+https://github.com/googleapis/python-aiplatform.git@copybara_738852226",
            "google-cloud-aiplatform[agent_engines,adk]",
            "cloudpickle==3.1.1",
        ],
        "extra_packages" : [
            #WHL_FILE,
            "agent.py",
            "sec10ktool.py",
            "zoominfotool.py",
            "nubelatool.py",
        ],
    }

    existing_agents=list(agent_engines.list(filter=f'display_name="{AGENT_DISPLAY_NAME}"'))

    if existing_agents:
         print("Number of existing agents found for {AGENT_DISPLAY_NAME}:" + str(len(list(existing_agents))))
         print(existing_agents[0].resource_name)
    #     print(existing_agents[1].resource_name)
        
    if existing_agents:
      #update the existing agent
      remote_app = agent_engines.update(resource_name=existing_agents[0].resource_name,**agent_config)
    else:
      #create a new agent
      remote_app = agent_engines.create(**agent_config)
    
    return None


if __name__ == "__main__":
    deploy_agent_engine_app()


