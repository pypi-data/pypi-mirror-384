from das.common.api import post_data, get_data, get_binary_response
from das.common.config import load_token


class DownloadRequestService:
    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/DownloadRequest"
        self.download_files_url = f"{base_url}/File/DownloadRequestSet"

    def create(self, request_data: list[dict]):
        """Create a new download request."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/Create"

        response = post_data(url, data=request_data, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        else:
            raise ValueError(response.get('error'))        
        
    def delete(self, request_id: str):
        """Delete a download request by ID."""

        #check if request_id is valid uuid
        if not isinstance(request_id, str) or len(request_id) != 36:
            raise ValueError("Invalid request ID")

        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/Delete?downloadRequestId={request_id}"

        response = post_data(url, data={}, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        else:
            raise ValueError(response.get('error'))

    def get_my_requests(self):
        """Get all download requests for the current user."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        url = f"{self.base_url}/GetMyRequests"
        response = get_data(url, headers=headers)

        # Expected API response shape:
        # { success: true, result: { totalCount: number, items: [...] }, ... }
        if isinstance(response, dict) and response.get('success') is True:
            return response.get('result')
        # Some backends might already return the result without 'success'
        if isinstance(response, dict) and 'result' in response and 'success' not in response:
            return response.get('result')
        # If the API directly returns the payload (result), pass it through
        if isinstance(response, dict) and 'items' in response and 'totalCount' in response:
            return response
        # Otherwise raise a meaningful error
        error_msg = None
        if isinstance(response, dict):
            error_msg = response.get('error') or response.get('message')
        raise ValueError(error_msg or 'Failed to fetch download requests')

    def download_files(self, request_id: str):
        """Return a streaming HTTP response for the download bundle of a request."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")
            
        headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"{self.download_files_url}?requestId={request_id}"

        response = get_binary_response(url, headers=headers, params=None, stream=True)
        return response