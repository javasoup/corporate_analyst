import vertexai
import os
from vertexai import agent_engines
from dotenv import load_dotenv
 



def deploy_agent_engine_app():
    load_dotenv() 

    GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
    GOOGLE_CLOUD_LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]
    STAGING_BUCKET = f"gs://{GOOGLE_CLOUD_PROJECT}-agent-engine-deploy"
    WHL_FILE =  "google_adk-0.0.2.dev20250326+nightly740999296-py3-none-any.whl"
    AGENT_DISPLAY_NAME="Corporate Analyst - New"
    AGENT_APP_NAME="corporate_analyst_app"
    
    from agent import root_agent
    ROOT_AGENT=root_agent # the name of the root agent in agent.py
    

    additional_vars= { "SEC_API_KEY": os.environ["SEC_API_KEY"],
                "ZOOMINFO_USERNAME": os.environ["ZOOMINFO_USERNAME"],
                "ZOOMINFO_PASSWORD": os.environ["ZOOMINFO_PASSWORD"],
                "DB_USER": os.environ["DB_USER"],
                "DB_PASS": os.environ["DB_PASS"],
                "DB_NAME": os.environ["DB_NAME"],
                "DB_CONNECTION_NAME": os.environ["DB_CONNECTION_NAME"],
                "ENABLE_SEC_API_CALLS": os.environ["ENABLE_SEC_API_CALLS"],
                "ENABLE_ZOOMINFO_API_CALLS": os.environ["ENABLE_ZOOMINFO_API_CALLS"],
    }


    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    app = agent_engines.ADKApp(
        agent=ROOT_AGENT,
        enable_tracing=True,
        app_name=AGENT_APP_NAME, # optional
        
        env_vars=additional_vars,
    )

    #app.register_operations()

    with open('requirements.txt', 'r') as file:
        reqs = file.read().splitlines()

    agent_config =  {
        "agent_engine" : app,
        "display_name" : AGENT_DISPLAY_NAME,
        "requirements" : reqs+[
             WHL_FILE,
            "google-cloud-aiplatform[agent_engines] @ git+https://github.com/googleapis/python-aiplatform.git@copybara_738852226",
            "cloudpickle==3.1.1",
        ],
        "extra_packages" : [
            WHL_FILE,
            "agent.py",
            "sec10ktool.py",
            "zoominfotool.py",
        ],
    }

    existing_agents=list(agent_engines.list(filter=f'display_name="{AGENT_DISPLAY_NAME}"'))

    if existing_agents:
         print("Number of existing agents found for {AGENT_DISPLAY_NAME}:" + str(len(list(existing_agents))))
         print(existing_agents[0].resource_name)
    #     print(existing_agents[1].resource_name)
        

    if existing_agents:
      #update the existing agent
      remote_app = existing_agents[0].update(**agent_config)
    else:
      #create a new agent
      remote_app = agent_engines.create(**agent_config)
    
    return None


if __name__ == "__main__":
    deploy_agent_engine_app()