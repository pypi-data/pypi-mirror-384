from http_client import HttpClient, ApiError

API_KEY = "d9eb2842bb95039bfc31196432a82998bc5930f4"

if __name__ == "__main__":
    client = HttpClient(api_key=API_KEY)

    try:        
        resp = client.api_key_model_service.get_list_platforms_support()
        print(resp)
        print(resp.status)

    except ApiError as e:
        print(e)
        # print(e.status)
        # print(e.message)

