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
./deploy.sh
```
