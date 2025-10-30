# flash-results-projections

## python

### Running FastAPI Server
```bash
source venv/bin/activate
fastapi dev app.py
```

FastAPI docs: <a>localhost:8000/docs<a>


FastAPI application to store and alter track data

Run locally:
```bash
cd python
pip install virtual env
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS="GOOGLE_APPLICATION_CREDENTIALS.json" # reach out for this file
uvicorn app:app --reload
```

Building and deploying python code:

The python deployment takes too long in github actions so just do it locally.

```bash
gcloud auth login
gcloud config set project flash-results-projections
cd python
gcloud builds submit --tag gcr.io/flash-results-projections/flash-results-projections # Build and tag docker image
gcloud run deploy utm-generator \
  --image gcr.io/flash-results-projections/flash-results-projections \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

### pubsub overview
1. File uploaded to gs://projections-data/merged-start-lists/ bucket
2. GCS publishes a JSON message about this file to the start_list_uploads Pub/Sub topic.
3. Any Cloud Function subscribed to this topic receives the message and can process the file.

```bash
# create pub/sub topic

# topics 
gcloud pubsub topics create merged_start_list_uploads # create pub/sub topic
gcloud pubsub topics delete merged_start_list_uploads # delete a pubsub topic

# notifications
gsutil notification list gs://projections-data
gsutil notification create \
  -t merged_start_list_uploads \
  -f json \
  -e OBJECT_FINALIZE \
  -p "merged-start-lists/" \
  gs://projections-data
gsutil notification delete projects/_/buckets/projections-data/notificationConfigs/2

# subscriptions
gcloud pubsub subscriptions list
gcloud pubsub subscriptions create merged_start_list_uploads_sub --topic=merged_start_list_uploads 
gcloud pubsub subscriptions delete merged_start_list_uploads_sub
```