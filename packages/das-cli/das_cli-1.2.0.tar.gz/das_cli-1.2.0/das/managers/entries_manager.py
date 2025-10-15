import json
from das.common.config import load_api_url
from das.managers.search_manager import SearchManager
from das.services.attributes import AttributesService
from das.services.entry_fields import EntryFieldsService
from das.services.entries import EntriesService
from das.common.entry_fields_constants import DIGITAL_OBJECT_INPUT, SELECT_COMBO_INPUT
from das.services.search import SearchService
from das.services.users import UsersService


class EntryManager:
    def __init__(self):
        
        base_url = load_api_url()
        
        if (base_url is None or base_url == ""):
            raise ValueError(f"Base URL is required - {self.__class__.__name__} - You must be authenticated.")
        
        self.entry_service = EntriesService(base_url)
        self.entry_fields_service = EntryFieldsService(base_url)
        self.search_service = SearchService(base_url)
        self.attribute_service = AttributesService(base_url)
        self.user_service = UsersService(base_url)

    def get_entry(self, entry_id: str):
        """Get entry details by ID"""
        if not entry_id:
            raise ValueError("Entry ID is required")
            
        return self.get(id=entry_id)
        
    def get(self, id: str = None, code: str = None):
        """Get entry by id or code. The client parameter is not used but kept for backward compatibility."""
        
        try:
            entry_response = self.entry_service.get(id=id, code=code)
            
            if not entry_response or not isinstance(entry_response, dict):
                raise ValueError(f"Invalid entry response format: {type(entry_response)}")
                
            if "attributeId" not in entry_response:
                raise ValueError(f"Missing attributeId in entry response: {entry_response}")

            fields = self.entry_fields_service.get_entry_fields(attribute_id=entry_response.get("attributeId"))

            if not fields or not isinstance(fields, dict):
                raise ValueError(f"Invalid fields response: {fields}")
            
            entry = {}
            entry_raw = entry_response.get('entry', {})
            
            if "result" not in fields or "items" not in fields.get("result", {}):
                raise ValueError(f"Missing fields data in response")
                
            if (entry_raw.get("id") is not None):
                entry["ID"] = entry_raw.get("id")

            for field in fields.get("result").get("items"):
                field_name = field.get("displayName")
                field_value = self.__get_field_value(entry_raw, field)

                if field_value is None:
                    field_value = ""

                entry[field_name] = field_value

            if (entry_raw.get("creationtime") is not None):
                entry["Created At"] = entry_raw.get("creationtime")

            if (entry_raw.get("lastmodificationtime") is not None):
                entry["Updated At"] = entry_raw.get("lastmodificationtime")

            return entry
        except Exception as e:
            raise ValueError(f"Error processing entry data: {e}")
        
    def create(self, attribute: str, entry: dict = None, entries: list = None) -> list:
        """
        Create one or more new entries.
        
        Args:
            attribute (str): The attribute name
            entry (dict, optional): Single entry data
            entries (list, optional): List of entry data for creating multiple entries
            
        Returns:
            list: List of created entry IDs with status information
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if not attribute:
            raise ValueError("Attribute name is required")
            
        if entries is not None:
            # Multiple entries creation
            if not isinstance(entries, list):
                raise ValueError("Entries must be a list")
            
            if not entries:
                raise ValueError("Entries list is empty")
                
            results = []
            for entry_data in entries:
                if not isinstance(entry_data, dict):
                    raise ValueError(f"Invalid entry data: {entry_data}")
                
                try:
                    result = self._create_single_entry(attribute, entry_data)
                    results.append({"id": result, "status": "success"})
                except Exception as e:
                    results.append({"error": str(e), "status": "error"})
            
            return results
            
        elif entry is not None:
            # Single entry creation
            result = self._create_single_entry(attribute, entry)
            return [{"id": result, "status": "success"}]
            
        else:
            raise ValueError("Either 'entry' or 'entries' must be provided")

    def _create_single_entry(self, attribute: str, entry: dict) -> str:
        """Internal method to create a single entry."""
        if not attribute:
            raise ValueError("Attribute name is required")

        attribute_id = self.attribute_service.get_id(name=attribute)

        if not entry or not isinstance(entry, dict):
            raise ValueError("Entry data must be a non-empty dictionary")

        entry_fields_response = self.entry_fields_service.get_entry_fields(attribute_id=attribute_id)

        fields = entry_fields_response.get("result", {}).get("items", [])

        if not fields or not isinstance(fields, list):
            raise ValueError(f"Invalid fields response: {fields}")

        if not all(isinstance(item, dict) for item in fields):
            raise ValueError(f"Invalid fields data format: {fields}")

        new_entry = {}

        for field in fields:
            field_name = field.get("displayName")
            column_name = field.get("column").lower()

            if field_name in entry:
                new_entry[column_name] = self.__get_value(field, entry[field_name])
            else:
                new_entry[column_name] = None

        return self.entry_service.create(attribute_id=attribute_id, entry=new_entry)
    
    def update(self, attribute: str, code: str = None, entry: dict = None, entries: list = None) -> list:
        """
        Update one or more existing entries.
        
        If 'code' and 'entry' are provided, updates a single entry.
        If 'entries' is provided, updates multiple entries based on the code in each entry.
        
        Args:
            attribute (str): The attribute name
            code (str, optional): The entry code for single entry update
            entry (dict, optional): The entry data for single entry update
            entries (list, optional): List of entry data for multiple updates
            
        Returns:
            list: List of updated entry IDs
        
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if entries is not None:
            # Multiple entries update
            if not isinstance(entries, list):
                raise ValueError("Entries must be a list")
            
            if not entries:
                raise ValueError("Entries list is empty")
                
            results = []
            for entry_data in entries:
                if not isinstance(entry_data, dict):
                    raise ValueError(f"Invalid entry data: {entry_data}")
                
                # Each entry must have a Code field
                entry_code = next((entry_data.get(key) for key in entry_data if key.lower() == 'code'), None)
                if not entry_code:
                    raise ValueError(f"Entry code is missing in entry data: {entry_data}")
                
                try:
                    result = self._update_single_entry(attribute, entry_code, entry_data)
                    results.append({"code": entry_code, "id": result, "status": "success"})
                except Exception as e:
                    results.append({"code": entry_code, "error": str(e), "status": "error"})
            
            return results
        
        elif code and entry:
            # Single entry update
            result = self._update_single_entry(attribute, code, entry)
            return [{"code": code, "id": result, "status": "success"}]
        
        else:
            raise ValueError("Either 'code' and 'entry' or 'entries' must be provided")
    
    def _update_single_entry(self, attribute: str, code: str, entry: dict) -> str:
        """Internal method to update a single entry."""
        if not code:
            raise ValueError("Entry code is required")

        if not entry or not isinstance(entry, dict):
            raise ValueError("Entry data must be a non-empty dictionary")

        existing_entry_response = self.entry_service.get_entry(code=code)

        if not existing_entry_response or not isinstance(existing_entry_response, dict):
            raise ValueError(f"Invalid existing entry response: {existing_entry_response}")

        attribute_id = existing_entry_response.get("attributeId")

        if not attribute_id:
            raise ValueError("Attribute ID is missing in the existing entry")

        entry_fields_response = self.entry_fields_service.get_entry_fields(attribute_id=attribute_id)

        fields = entry_fields_response.get("result", {}).get("items", [])

        if not fields or not isinstance(fields, list):
            raise ValueError(f"Invalid fields response: {fields}")

        if not all(isinstance(item, dict) for item in fields):
            raise ValueError(f"Invalid fields data format: {fields}")

        updated_entry = existing_entry_response.get('entry', {})

        for field in fields:
            field_name = field.get("displayName")
            column_name = field.get("column").lower()

            if field_name in entry:
                updated_entry[column_name] = self.__get_value(field, entry[field_name])

        return self.entry_service.update(attribute_id=attribute_id, entry=updated_entry)
    

    def __get_value(self, field, source: str):
        """Helper method to get field value based on its type."""
        if field.get('inputType') == SELECT_COMBO_INPUT:  # SELECT_COMBO_INPUT
            select_value = self.__get_select_combobox_field_value(field, source)
            return select_value
        else:
            return source    
    
    def __get_select_combobox_field_value(self, field, source: str) -> str:
        """Helper method to get select combobox field value."""

        attribute_id = -1

        if field.get('column').isdigit():
            attribute_id = int(field.get('column'))
        elif field.get('column')[0].isalpha() and field.get('column')[1:].isdigit():
            attribute_id = int(field.get('column')[1:])

        if attribute_id == -1:            
            # then we need to check if the field has the property customdata
            if not field.get('customdata', None) is None:
                try:
                    customdata = json.loads(field.get('customdata'))
                    if (customdata is not None and isinstance(customdata, dict) and "datasource" in customdata):
                        datasource = customdata.get("datasource")
                        if (datasource is not None and isinstance(datasource, dict) and "attributeid" in datasource):
                            attribute_id = datasource.get("attributeid")
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid customdata JSON: {field.get('customdata')}")        

        search_params = {
            "attributeId": attribute_id,            
            "queryString": f"displayname({source});",
            "maxResultCount": 1,
            "skipCount": 0
        }

        search_response = self.search_service.search_entries(**search_params)

        if search_response.get('totalCount', 0) == 0:
            search_params['queryString'] = f"code({source});"
            search_response = self.search_service.search_entries(**search_params)

        if search_response and 'items' in search_response and len(search_response['items']) > 0:
            result = {}
            result['id'] = search_response['items'][0].get('entry', {}).get('id')
            result['name'] = search_response['items'][0].get('entry', {}).get('displayname')
            result['code'] = search_response['items'][0].get('entry', {}).get('code')            
            result['alias'] = search_response['items'][0].get('entry', {}).get('alias', None)
            result['attributeid'] = attribute_id
            # Filter out None values from the result dictionary
            result = {k: v for k, v in result.items() if v is not None}
            return json.dumps([result])
        else:           
            return source
        
    def __get_field_value(self, entry_raw, field):
        """Helper method to safely get field value from entry_raw."""

        if field.get('inputType') == DIGITAL_OBJECT_INPUT:
            digital_object = self.__get_digital_object_field_value(entry_raw, field)
            return digital_object
        elif field.get('inputType') == SELECT_COMBO_INPUT:  # SELECT_COMBO_INPUT
            select_value = self.__get_select_field_value(entry_raw, field)
            return select_value
        else:
            return entry_raw.get(field.get('column').lower(), "")
        

    def __get_select_field_value(self, entry_raw, field):
        """Helper method to get select field"""
        results = []
        select_value = entry_raw.get(field.get('column').lower(), None)

        # checks if its a valid json string
        if select_value is not None:
            try:    
                data = json.loads(select_value)                
                if isinstance(data, list):                    
                    for obj in data:
                        item = {}
                        item["Id"] = obj.get("id")
                        item["Name"] = obj.get("name")
                        results.append(item)
                    return results
                else:
                    return data
                        
            except json.JSONDecodeError:
                return select_value        
        
    def __get_digital_object_field_value(self, entry_raw, field):
        """Helper method to get digital object field value."""
        digital_objects = entry_raw.get(field.get('column').lower(), None)
        
        results = []

        # checks if its a valid json string
        if digital_objects is not None:
            try:    
                data = json.loads(digital_objects)
                
                if isinstance(data, list):
                    for obj in data:
                        digital_object = {
                            "Id": obj.get("id"),
                            "Name": obj.get("name"),
                            "Links": obj.get("needle"),
                            "Type": obj.get("typename")
                        }
                        results.append(digital_object)
                    return results
            except json.JSONDecodeError:
                return digital_objects
            
    def __create_from_json_file(self, attribute: str, file_path: str):
        """Create a set of new entries from a file."""

        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                entries = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing JSON file: {e}")

        if not isinstance(entries, list):
            raise ValueError("JSON file must contain a list of entries")
        
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("Each entry must be a dictionary")
            self.create(attribute=attribute, entry=entry)

    def __create_from_csv_file(self, attribute: str, file_path: str):
        """Create a set of new entries from a file."""

        import csv

        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            entries = [row for row in reader]

        for entry in entries:
            self.create(attribute=attribute, entry=entry)
        

    def __create_from_excel_file(self, attribute: str, file_path: str):
        """Create a set of new entries from a file."""
        import pandas as pd

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")

        entries = df.to_dict(orient='records')

        for entry in entries:
            self.create(attribute=attribute, entry=entry)
                    

    def create_from_file(self, attribute: str, file_path: str):
        """Create a  set of new entries from a file."""
        
        if not attribute:
            raise ValueError("Attribute name is required")
        
        if not file_path:
            raise ValueError("File path is required")
        
        # determine the file type by its extension
        if file_path.endswith('.json'):
            self.__create_from_json_file(attribute, file_path)
        elif file_path.endswith('.csv'):
            self.__create_from_csv_file(attribute, file_path)
        elif file_path.endswith('.xlsx'):
            self.__create_from_excel_file(attribute, file_path)
        else:
            raise ValueError("Unsupported file type. Supported types are: .json, .csv, .xlsx")

    def chown(self, user_name: str, entry_code_list: list[str]):            
        
        user = self.user_service.get_user(user_name)

        if user is None:
            raise ValueError(f"User '{user_name}' not found")

        if not entry_code_list:
            raise ValueError("Entry code list is required")

        entry_list_ids = []

        for entry_code in entry_code_list:
            entry = self.get(code=entry_code)
            entry_list_ids.append(entry.get('ID') if entry.get('ID') else entry.get('id'))

        if not entry_list_ids:
            raise ValueError("Entry list IDs is empty")
            
        return self.entry_service.chown(new_user_id=user.get('id'), entry_list_ids=entry_list_ids)

if __name__ == "__main__":
    manager = EntryManager()
    entry = manager.get(id="8d2841c9-e307-4971-bd2b-70da0d7a7534")
    print(entry)    

   