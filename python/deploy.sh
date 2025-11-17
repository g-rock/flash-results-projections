gcloud builds submit --tag gcr.io/flash-results-projections/flash-results-projections # Build and tag docker image
gcloud run deploy flash-results-projections \
  --image gcr.io/flash-results-projections/flash-results-projections \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated