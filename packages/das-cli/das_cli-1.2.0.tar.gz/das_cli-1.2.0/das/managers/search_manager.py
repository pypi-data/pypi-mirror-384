from das.common.config import load_api_url
from das.services.attributes import AttributesService
from das.services.entry_fields import EntryFieldsService
from das.services.search import SearchService

class SearchManager:
    def __init__(self):        
        base_url = load_api_url()
        if (base_url is None or base_url == ""):
            raise ValueError(f"Base URL is required - {self.__class__.__name__} - You must be authenticated.")
        self.search_service = SearchService(base_url)
        self.attributes_service = AttributesService(base_url)
        self.entry_fields = EntryFieldsService(base_url)

    def __convert_filter(self, entry_fields: list, filter: str) -> str:
        """Converts user-friendly filter to API-compatible filter.""" 
        # The fileter will be in the format: name(*64*);Create at(>2023-01-01);Sampling Location(*North Sea*)       
        # Replace the display names with the column names from entry_fields only for the values outside the parentheses.
        for field in entry_fields:
            display_name = field.get('displayName')
            column_name = field.get('column')
            if display_name and column_name:
                filter = filter.lower().replace(f"{display_name.lower()}(", f"{column_name.lower()}(")
        return filter

    def __convert_sorting(self, entry_fields: list, sort_by: str, sort_order: str) -> str:
        """Converts user-friendly sorting to API-compatible sorting."""
        field = next((ef for ef in entry_fields if ef.get('displayName').lower() == sort_by.lower()), None)
        if field is None:
            raise ValueError(f"Sorting field '{sort_by}' not found in entry fields.")
        return f"{field.get('column')} {sort_order}"

    def search_entries(self, attribute: str, query: str, max_results: int = 10, page: int = 1, sort_by: str = "Name", sort_order: str = "asc"):
        """Search entries based on provided criteria."""
        try:
            # Validate attribute
            attr_response = self.attributes_service.get_attribute(name=attribute)
            if not attr_response or not isinstance(attr_response, dict):
                raise ValueError(f"Invalid attribute response format: {type(attr_response)}")
            items = attr_response.get("result", {}).get("items", [])
            if len(items) == 0:
                raise ValueError(f"Attribute '{attribute}' not found.")
            attribute_id = items[0].get("id")
            if attribute_id is None:
                raise ValueError(f"Attribute ID not found for attribute '{attribute}'.")
            
            entry_fields = self.entry_fields.get_entry_fields(attribute_id=attribute_id).get('result', {}).get('items', [])

            if len(entry_fields) == 0:
                raise ValueError(f"No entry fields found for attribute '{attribute}'.")

            # Perform search
            search_params = {
                "attributeId": attribute_id,
                "queryString": self.__convert_filter(entry_fields, query),
                "maxResultCount": max_results,
                "skipCount": 0 if page <= 0 else (max_results * (page - 1)),
                "sorting": self.__convert_sorting(entry_fields, sort_by, sort_order)
            }
            results = self.search_service.search_entries(**search_params)

            # Build user-friendly items list while preserving totalCount
            friendly_items = []
            for result in results.get('items', []):
                entry = result.get('entry', {}) if isinstance(result, dict) else {}
                friendly_item = {}
                for field in entry_fields:
                    display_name = field.get('displayName')
                    column_name = field.get('column')
                    if display_name and column_name:
                        friendly_item[display_name] = entry.get(column_name)
                friendly_items.append(friendly_item)

            return {
                'items': friendly_items,
                'totalCount': results.get('totalCount', len(friendly_items))
            }
        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")