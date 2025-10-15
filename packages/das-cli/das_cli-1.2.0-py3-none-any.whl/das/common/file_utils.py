"""
File utility functions for importing data from various formats
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Union

def load_json_file(file_path: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load data from a JSON file.
    Can load either a single entry (dictionary) or multiple entries (list of dictionaries).
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: The loaded JSON data
        
    Raises:
        ValueError: If the file doesn't exist or isn't a valid JSON file
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    
    if file_path.suffix.lower() != '.json':
        raise ValueError(f"Not a JSON file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file: {e}")

def load_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load data from a CSV file.
    Assumes the first row contains headers and subsequent rows contain values.
    Creates a list of dictionaries, one for each row in the CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing one row from the CSV
        
    Raises:
        ValueError: If the file doesn't exist or isn't a valid CSV file
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    
    if file_path.suffix.lower() != '.csv':
        raise ValueError(f"Not a CSV file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            
            if not headers:
                raise ValueError("CSV file is empty or has no headers")
            
            result = []
            for row in reader:
                if not row:  # Skip empty rows
                    continue
                    
                # Create a dictionary for this row
                entry = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        entry[header] = row[i]
                    else:
                        entry[header] = ""  # Empty value for missing columns
                
                result.append(entry)
            
            if not result:
                raise ValueError("CSV file has headers but no data rows")
                
            return result
    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {e}")
    except UnicodeDecodeError:
        raise ValueError("Unable to decode CSV file, ensure it's saved with UTF-8 encoding")

def load_excel_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load data from an Excel file.
    Assumes the first row contains headers and subsequent rows contain values.
    Creates a list of dictionaries, one for each row in the Excel file.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing one row from the Excel file
        
    Raises:
        ValueError: If the file doesn't exist, isn't a valid Excel file, or pandas is not installed
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    
    if file_path.suffix.lower() not in ['.xls', '.xlsx']:
        raise ValueError(f"Not an Excel file: {file_path}")
    
    # Try to import pandas here to avoid making it a required dependency
    try:
        import pandas as pd
    except ImportError:
        raise ValueError("pandas is required to read Excel files. Install it with: pip install pandas openpyxl")
    
    try:
        df = pd.read_excel(file_path)
        
        if df.empty:
            raise ValueError("Excel file is empty")
        
        # Convert all rows to dictionaries
        result = []
        for _, row in df.iterrows():
            row_dict = {}
            for key, value in row.items():
                if pd.isna(value):
                    row_dict[key] = ""
                else:
                    row_dict[key] = value
            result.append(row_dict)
                
        return result
    except Exception as e:
        raise ValueError(f"Excel parsing error: {e}")

def parse_data_string(data_string: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Parse a data string in the format "{ 'key1': value1, 'key2': value2, ... }"
    or a list of such objects "[{ 'key1': value1, ... }, { 'key2': value2, ... }]"
    
    Args:
        data_string (str): The data string to parse
        
    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: The parsed data
        
    Raises:
        ValueError: If the string cannot be parsed
    """
    try:
        # Clean up the input string to make it valid JSON
        # Replace single quotes with double quotes
        data_string = data_string.replace("'", '"')
        
        # Handle Yes/No values (convert to true/false for JSON)
        data_string = data_string.replace(': Yes', ': true').replace(': No', ': false')
        
        # Add quotes around unquoted keys
        import re
        data_string = re.sub(r'(\{|\,)\s*([a-zA-Z0-9_]+)\s*:', r'\1 "\2":', data_string)
        
        # Parse the resulting JSON
        return json.loads(data_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid data string format: {e}")

def load_file_based_on_extension(file_path: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load data from a file based on its extension.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: The loaded data - either a single entry or a list of entries
        
    Raises:
        ValueError: If the file type is not supported
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    
    suffix = file_path.suffix.lower()
    
    if suffix == '.json':
        return load_json_file(file_path)
    elif suffix == '.csv':
        return load_csv_file(file_path)
    elif suffix in ['.xls', '.xlsx']:
        return load_excel_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported types are: .json, .csv, .xls, .xlsx")