import requests

def send(endpoint, cmd):
    """
    """
    headers  =  {"Content-Type": "application/json"}
    response = requests.post(endpoint, json=cmd, headers=headers)
    return response