import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "agentspace-demo-1145-b"
LOCATION = "us-central1"
vertexai.init(
      project=PROJECT_ID,
      location=LOCATION,
      # api_endpoint="us-central1-aiplatform.googleapis.com",
  )
engines = reasoning_engines.ReasoningEngine.list(filter='display_name="Corporate Analyst"')

if not engines:
    print("Reasoning engine for Corporate Analyst missing")
    exit

print (engines[0].resource_name)

engine = reasoning_engines.ReasoningEngine(engines[0].resource_name)

session = engine.create_session(session_id="session1")
session = engine.get_session(session_id="session1")


from google.genai import types
output = engine.agent_run(
    session_id="session1",
    message=types.Content(
        parts=[types.Part(text="AAPL")],
        role="user",
    ).model_dump_json(),
)

print(output)

