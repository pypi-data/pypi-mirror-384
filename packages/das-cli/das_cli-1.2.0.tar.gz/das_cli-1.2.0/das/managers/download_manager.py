import json
import time
from das.common.config import load_api_url
from das.services.downloads import DownloadRequestService
from das.services.entries import EntriesService


class DownloadManager:

    def __init__(self):
        base_url = load_api_url()

        if (base_url is None or base_url == ""):
            raise ValueError(f"Base URL is required - {self.__class__.__name__}")

        self.download_request_service = DownloadRequestService(base_url)
        self.entry_service = EntriesService(base_url)

    def create_download_request(self, request_data: dict):
        """
        Create a new download request.

        Args:
            request_data (dict): A dictionary where keys are entry codes and values are lists of codes of the files. Also includes a 'name' key for the download request name.
        """

        requests = {
            'items': []
        }

        if 'name' not in request_data or not request_data['name']:
            request_data['name'] = f"Download Request at {time.strftime('%Y-%m-%d %H:%M:%S')}"

        erros = []

        for entry_code in request_data.keys():
            # Validate that the entry exists
            if entry_code == 'name':
                continue
            response = self.entry_service.get_entry(code=entry_code)
            if response.get('entry', None) is None:
                erros.append(f"Entry with code '{entry_code}' does not exist.")
            else:
                attribute_id = response.get('attributeId', None)
                digital_objects_json = response.get('entry').get('6', None)  # Assuming '6' is the attribute ID for digital objects
                if digital_objects_json is None:
                    erros.append(f"Entry with code '{entry_code}' has no digital objects.")
                    continue

                # convert digital_objects_json to a array of dicts
                digital_objects = []
                try:
                    digital_objects = json.loads(digital_objects_json)
                except Exception as e:
                    erros.append(f"Error parsing digital objects for entry '{entry_code}': {str(e)}")
                    continue

                entry = response.get('entry')

                if request_data[entry_code] is None or len(request_data[entry_code]) == 0:
                    filtered_digital_objects = digital_objects
                else:
                    filtered_digital_objects = [obj for obj in digital_objects if obj.get('code') in request_data[entry_code]]

                if len(filtered_digital_objects) == 0:
                    erros.append(f"No matching digital objects found for entry '{entry_code}' with the provided file codes.")
                    continue
                for digital_object in filtered_digital_objects:
                    request = {
                        'name': request_data['name'],
                        'sourceId': entry.get('id'),
                        'sourceAttributeId': attribute_id,
                        'id': digital_object.get('id')
                    }
                    requests['items'].append(request)

        if erros:
            return {"errors": erros}

        return self.download_request_service.create(requests)
    
    def delete_download_request(self, request_id: str):
        """
        Delete a download request by ID.

        Args:
            request_id (str): The ID of the download request to delete.
        """
        return self.download_request_service.delete(request_id)

    def get_my_requests(self):
        """Get all download requests for the current user."""
        return self.download_request_service.get_my_requests()

    def download_files(self, request_id: str):
        """Return streaming response for files of a download request."""
        return self.download_request_service.download_files(request_id)

    def save_download(self, request_id: str, output_path: str, overwrite: bool = False) -> str:
        """
        Download and save the request bundle to disk.

        Returns the path to the saved file.
        """
        import os

        resp = self.download_files(request_id)
        # If an error structure was returned from lower layer
        if isinstance(resp, dict) and resp.get('error'):
            raise ValueError(resp['error'])

        # Determine filename from headers if available
        filename = f"download_{request_id}.zip"
        try:
            cd = resp.headers.get('Content-Disposition') if hasattr(resp, 'headers') else None
            if cd and 'filename=' in cd:
                filename = cd.split('filename=')[-1].strip('"')
        except Exception:
            pass

        # If output_path is a directory, join with filename
        target_path = output_path
        if os.path.isdir(output_path) or output_path.endswith(os.path.sep):
            target_path = os.path.join(output_path, filename)

        if os.path.exists(target_path) and not overwrite:
            raise FileExistsError(f"File already exists: {target_path}. Use overwrite to replace.")

        # Stream to disk
        with open(target_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return target_path