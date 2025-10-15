import json
from http_client import HttpClient, ApiError
from aioz_api_client.exceptions import ApiException

API_KEY = "d9eb2842bb95039bfc31196432a82998bc5930f4"

if __name__ == "__main__":
    client = HttpClient(api_key=API_KEY)

    try:        
        resp = client.api_key_service.get_task_histories(10,7)
        print(resp)
        print(resp.status)

    except ApiError as e:
        print(e)
        print(e.status)
        print(e.message)

