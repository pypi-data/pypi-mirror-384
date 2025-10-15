import os
import sys
from math import ceil
from os.path import exists
import json
from base64 import b64encode
from das.common.api import post_data
from das.common.config import load_token, load_verify_ssl
from pathlib import Path
import math
import uuid
import requests

CHUNK_SIZE = 1000000 # 1MB
class DigitalObjectsService:
    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/DigitalObject"
        # Common possible upload endpoints observed across deployments
        self.upload_digital_object_url = f"{base_url}/File/UploadDigitalObject"

    def link_existing_digital_objects(self, attribute_id: int, entry_id: str, digital_object_id_list: list[str], is_unlink: bool = False):
        """Link existing digital objects to an entry."""
        token = load_token()

        if token is None or token == "":
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "attributeId": attribute_id,
            "attributeValueId": entry_id,
            "digitalObjects": [],
        }

        for digital_object_id in digital_object_id_list:
            payload["digitalObjects"].append(
                {
                    "attributeId": attribute_id,
                    "attributeValueId": entry_id,
                    "digitalObjectId": digital_object_id,
                    "isDeleted": is_unlink,
                }
            )

        response = post_data(
            f"{self.base_url}/LinkExistingDigitalObject", data=payload, headers=headers
        )

        return response.get("success")

    # This is our chunk reader. This is what gets the next chunk of data ready to send.
    def __read_in_chunks(self, file_object, chunk_size):
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data


    def upload_digital_object(self,  file_description: str, digital_object_type_id: str, file_path: str):

        if not exists(file_path):
            raise ValueError(f"File '{file_path}' does not exist")

        head, tail = os.path.split(file_path)

        metadata = {
            "fileName": tail,
            "fileSize": os.path.getsize(file_path),
            "description": file_description,
            "digitalObjectTypeId": digital_object_type_id,
            "id": str(uuid.uuid4()).lower(),
            "description": file_description,
            "totalCount": ceil(os.path.getsize(file_path) / CHUNK_SIZE),
            "index": 0,
        }

        binary_file = open(file_path, "rb")
        index = 0
        offset = 0
        digital_object_id = None        
        headers = {}

        try:
            for chunk in self.__read_in_chunks(binary_file, CHUNK_SIZE):
                offset = index + len(chunk)
                headers['Content-Range'] = 'bytes %s-%s/%s' % (index, offset - 1, metadata.get('fileSize'))
                index = offset   
                json_metadata = json.dumps(metadata)
                base654_bytes = b64encode(json_metadata.encode('utf-8')).decode('ascii')
                headers['metadata'] = base654_bytes               

                r = self.upload_file(chunk, metadata, headers)

                if r.get('result', None) is None:                    
                    continue

                digital_object_id = r.get('result').get('id')
                metadata['index'] = index + 1
                
            binary_file.close()               

        except Exception as e:
            raise ValueError(f"Error uploading file '{file_path}': {str(e)}")
        finally:
            binary_file.close()

            return digital_object_id

        

    def upload_file(self, file, body, headers):
        """Upload a file to the digital object service."""
        token = load_token()
        headers.update({
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            # Do NOT set Content-Type here when sending files; requests will set proper multipart boundary
        })

        files = {
            "file": ("chunk", file, "application/octet-stream"),
        }

        try:
            response = requests.post(self.upload_digital_object_url, headers=headers, files=files, verify=load_verify_ssl())
            response.raise_for_status()
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"Error uploading file: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            raise ValueError(f"Error uploading file: {str(e)}")


    


