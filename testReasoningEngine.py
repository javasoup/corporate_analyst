import vertexai
import json
#from vertexai.preview import reasoning_engines
from vertexai import agent_engines

PROJECT_ID = "lisboa-baixa"
#PROJECT_ID = "spark-demo-1114"
LOCATION = "us-central1"
vertexai.init(
      project=PROJECT_ID,
      location=LOCATION,
      # api_endpoint="us-central1-aiplatform.googleapis.com",
  )
engines = list(agent_engines.list(filter='display_name="Corporate Analyst"'))

if not engines:
    print("Reasoning engine for Corporate Analyst missing")
    exit

print ("Reasoning engine: " + engines[0].resource_name)

engine = agent_engines.get(engines[0].resource_name)

print(engine.operation_schemas())

session = engine.create_session(user_id="user1")

# sessions_data = engine.list_sessions(user_id="user1")
# print (sessions_data)


# Check if the response is a string and if so, attempt to parse as JSON
# if isinstance(sessions_data, str):
#   try:
#     sessions_data = json.loads(sessions_data)
#   except json.JSONDecodeError as e:
#       print(f"Error decoding JSON: {e}")
#       print(f"Received string: {sessions_data}")
#       #Handle the error case. maybe return or exit
#       exit()
      

# Now check if it's a dictionary with a 'session_ids' key
# if isinstance(sessions_data, dict) and 'session_ids' in sessions_data:
#     session_ids = sessions_data['session_ids']
#     if not session_ids:  # Check if the list is empty
#         print("Creating new session")
#         session = engine.create_session(session_id="session1", user_id="user1")
#         if isinstance(session, dict):
#             print("Created session: " + session["id"])
#         else:
#             print("Created session: " + session.id)
#     else:
#         print(f"Existing sessions found: {session_ids}")
# else:
#     print(
#         "Unexpected format for session data. Expected a dictionary with a 'session_ids' key."
#     )
#     print(f"Received: {sessions_data}")
#     # Handle the error case. maybe return or exit
#     exit()

session = engine.get_session(session_id=session["id"],user_id="user1")

from google.genai import types
for response in engine.stream_query(
    #session_id="session1",
    message="GOOG",
    user_id="user1",
    ):
    print(response)



