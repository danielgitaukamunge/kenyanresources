import requests
from django.conf import settings

def get_access_token():
    """
    Fetch the access token from the Daraja API.
    """
    auth_url = f"{settings.MPESA_API_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(
        auth_url,
        auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
    )
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception("Failed to fetch access token")