LOCATION="us-central1"
PROJECT_ID="agentspace-demo-1145-b"
RESOURCE_ID="91347426035630080"

curl -X DELETE \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json; charset=utf-8" \
     -d "{"force" : true}" \
     "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines/${RESOURCE_ID}"