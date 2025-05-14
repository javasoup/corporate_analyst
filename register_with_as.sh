export PROJECT_NUMBER="329601266737"
export PROJECT_ID="lisboa-baixa"
export AS_APP="enterprise-search-17387918_1738791880078"

export REASONING_ENGINE="projects/${PROJECT_ID}/locations/us-central1/reasoningEngines/3001869053967990784" #new name. We should do a list query to make sure it exists
export AGENT_DISPLAY_NAME="Corporate Guru"
export AGENT_DESCRIPTION="The agent can analyze a corporation given its ticker symbol and generates a report from SEC 10K report and other sources"
export AGENT_ID="corp_analyst_agent"

echo "REASONING_ENGINE: $REASONING_ENGINE"
echo "PROJECT_NUMBER: $PROJECT_NUMBER"
echo "PROJECT_ID: $PROJECT_ID"

curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "x-goog-user-project: ${PROJECT_ID}" \
https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${AS_APP}/assistants/default_assistant?updateMask=agent_configs -d '{
    "name": "projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${AS_APP}/assistants/default_assistant",
    "displayName": "Default Assistant",
    "agentConfigs": [{
      "displayName": "'"${AGENT_DISPLAY_NAME}"'",
      "vertexAiSdkAgentConnectionInfo": {
        "reasoningEngine": "'"${REASONING_ENGINE}"'"
      },
      "toolDescription": "'"${AGENT_DESCRIPTION}"'",
      "icon": {
        "uri": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/corporate_fare/default/24px.svg"
      },
      "id": "'"${AGENT_ID}"'"
    }]
  }'
