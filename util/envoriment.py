import os

def get_auth():
    return {
        "BASE_URL":os.environ["BASE_URL"],
        "API_KEY":os.environ["API_KEY"]
    }

