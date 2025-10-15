import os
import sys
from das.common.config import load_api_url
from das.services.search import SearchService
from das.services.entries import EntriesService
from das.services.digital_objects import DigitalObjectsService

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class DigitalObjectsManager:
    """Manager for digital objects."""
    
    def __init__(self):
        base_url = load_api_url()
        if base_url is None or base_url == "":
            raise ValueError(f"Base URL is required - {self.__class__.__name__}")

        self.__attribute_id_digital_object_type = 5;
        self.digital_objects_service = DigitalObjectsService(base_url)
        self.entry_service = EntriesService(base_url)
        self.search_service = SearchService(base_url)

    def link_existing_digital_objects(
        self, entry_code: str, digital_object_code_list: list[str], is_unlink: bool = False
    ) -> bool:
        """Attach or detach (unlink) digital objects to an entry using codes."""
        entry_response = self.entry_service.get_entry(entry_code)

        if entry_response is None:
            raise ValueError(f"Entry with code '{entry_code}' not found")

        entry_payload = entry_response.get("entry")
        if entry_payload is None:
            raise ValueError(f"Entry with code '{entry_code}' not found")

        digital_object_id_list: list[str] = []

        for code in digital_object_code_list:
            do_response = self.entry_service.get_entry(code)
            do_entry = do_response.get("entry") if do_response else None
            if do_entry is None:
                raise ValueError(f"Digital object with code '{code}' not found")
            digital_object_id_list.append(do_entry.get("id"))

        result = self.digital_objects_service.link_existing_digital_objects(
            attribute_id=entry_response.get("attributeId"),
            entry_id=entry_payload.get("id"),
            digital_object_id_list=digital_object_id_list,
            is_unlink=is_unlink,
        )

        return result

    def upload_digital_object(self, entry_code: str, file_description: str, digital_object_type: str, file_path: str):
        """Upload a digital object to the digital object service."""
        response = self.search_service.search_entries(
            queryString=f"displayname({digital_object_type})",
            attributeId=self.__attribute_id_digital_object_type,
            maxResultCount=1,
            skipCount=0
            )

        entry_response = self.entry_service.get_entry(entry_code)
        if entry_response is None:
            raise ValueError(f"Entry with code '{entry_code}' not found")

        if response.get('totalCount', 0) == 0:
            raise ValueError(f"Digital object type '{digital_object_type}' not found")
        
        digital_object_type_id = response.get('items', [])[0].get('entry').get('id')
        digital_object_id = self.digital_objects_service.upload_digital_object(file_description, digital_object_type_id, file_path)
        
        self.digital_objects_service.link_existing_digital_objects(
            attribute_id=entry_response.get('attributeId'), 
            entry_id=entry_response.get('entry').get('id'), 
            digital_object_id_list=[digital_object_id]
        )

        return digital_object_id


if __name__ == "__main__":
    digital_objects_manager = DigitalObjectsManager()
    digital_objects_manager.upload_digital_object(entry_code="zb.b.f7", file_description="test", digital_object_type="Dataset", file_path="my_new_file.txt")
