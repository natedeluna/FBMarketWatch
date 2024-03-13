### Install dependencies
    pip install -r requirements.txt

### To activate the virtual env, make sure you're in the project directory
    source "$(pwd)/venv/bin/activate"

### Start local server using uvicorn
    uvicorn entry:app --host 0.0.0.0 --port 4000