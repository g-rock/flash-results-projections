# flash-results-projections

## python

### Running FastAPI Server
```bash
source venv/bin/activate
fastapi dev app.py
```

FastAPI docs: <a>localhost:8000/docs<a>


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