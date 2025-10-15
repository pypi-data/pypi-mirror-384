import json
import requests
from das.common.config import load_verify_ssl


def get_data(url, headers=None, params=None):
    """
    Fetch data from a REST API endpoint.

    Args:
        url (str): The API endpoint URL.
        headers (dict, optional): Headers to include in the request.
        params (dict, optional): Query parameters for the request.

    Returns:
        dict: The JSON response from the API or an error message.
    """
    try:
        response = requests.get(url, headers=headers, params=params, verify=load_verify_ssl())
        response.raise_for_status()  # Raise an error for HTTP errors
        try:
            return response.json()
        except json.JSONDecodeError as json_err:
            print(f"Error decoding JSON response: {json_err}")
            return {"error": f"Invalid JSON response: {json_err}", "raw_content": response.text[:200]}
    except requests.RequestException as e:
        print(f"Error fetching API data: {e}")
        return {"error": str(e)}

def get_binary_response(url, headers=None, params=None, stream=True):
    """
    Perform a GET request expected to return binary content.

    Returns the raw requests.Response so callers can inspect headers
    and stream content to disk.
    """
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            verify=load_verify_ssl(),
            stream=stream,
        )
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        return {"error": str(e)}

def post_data(url, headers=None, data=None):
    """
    Send data to a REST API endpoint.

    Args:
        url (str): The API endpoint URL.
        headers (dict, optional): Headers to include in the request.
        data (dict, optional): The data to send in the request body.

    Returns:
        dict: The JSON response from the API or an error message.
    """
    try:
        response = requests.post(url, headers=headers, json=data, verify=load_verify_ssl())
        response.raise_for_status()  # Raise an error for HTTP errors
        try:
            return response.json()
        except json.JSONDecodeError as json_err:
            print(f"Error decoding JSON response: {json_err}")
            return {"error": f"Invalid JSON response: {json_err}", "raw_content": response.text[:200]}
    except requests.RequestException as e:
        print(f"Error posting API data: {e}")
        return {"error": str(e)}
    
def put_data(url, headers=None, data=None):
    """
    Update data at a REST API endpoint.

    Args:
        url (str): The API endpoint URL.
        headers (dict, optional): Headers to include in the request.
        data (dict, optional): The data to send in the request body.

    Returns:
        dict: The JSON response from the API or an error message.
    """
    try:
        response = requests.put(url, headers=headers, json=data, verify=load_verify_ssl())
        response.raise_for_status()  # Raise an error for HTTP errors
        try:
            return response.json()
        except json.JSONDecodeError as json_err:
            print(f"Error decoding JSON response: {json_err}")
            return {"error": f"Invalid JSON response: {json_err}", "raw_content": response.text[:200]}
    except requests.RequestException as e:
        print(f"Error updating API data: {e}")
        return {"error": str(e)}    
    
def delete_data(url, headers=None, data=None):
    """
    Delete data from a REST API endpoint.

    Args:
        url (str): The API endpoint URL.
        headers (dict, optional): Headers to include in the request.
        data (dict, optional): The data to send in the request body.

    Returns:
        dict: The JSON response from the API or an error message.
    """
    try:
        response = requests.delete(url, headers=headers, json=data, verify=load_verify_ssl())
        response.raise_for_status()  # Raise an error for HTTP errors
        try:
            return response.json()
        except json.JSONDecodeError as json_err:
            print(f"Error decoding JSON response: {json_err}")
            return {"error": f"Invalid JSON response: {json_err}", "raw_content": response.text[:200]}
    except requests.RequestException as e:
        print(f"Error deleting API data: {e}")
        return {"error": str(e)}