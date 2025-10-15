import sys
import click
import json
import os
from pathlib import Path
from das.common.config import (
    save_api_url, load_api_url, DEFAULT_BASE_URL,
    save_verify_ssl, load_verify_ssl, VERIFY_SSL,
    load_openai_api_key, save_openai_api_key, clear_openai_api_key,
    clear_token, _config_dir
)

from das.app import Das
from das.managers.download_manager import DownloadManager
from das.managers.entries_manager import EntryManager
from das.managers.search_manager import SearchManager
from das.managers.digital_objects_manager import DigitalObjectsManager
from das.common.file_utils import load_file_based_on_extension, parse_data_string
from das.ai.plugins.dasai import DasAI

# Simple table formatting function to avoid external dependencies
def format_table(data, headers):
    """Format data into a text-based table without external dependencies"""
    if not data:
        return "No data to display"
        
    # Calculate column widths
    col_widths = [max(len(str(h)), max([len(str(row[i])) for row in data] or [0])) for i, h in enumerate(headers)]
    
    # Create the separator line
    separator = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
    
    # Create the header row
    header_row = '|' + '|'.join(' ' + str(h).ljust(w) + ' ' for h, w in zip(headers, col_widths)) + '|'
    
    # Create the data rows
    data_rows = []
    for row in data:
        data_rows.append('|' + '|'.join(' ' + str(cell).ljust(w) + ' ' for cell, w in zip(row, col_widths)) + '|')
    
    # Assemble the table
    table = [separator, header_row, separator]
    table.extend(data_rows)
    table.append(separator)
    
    return '\n'.join(table)

class DasCLI:
    def __init__(self):
        self.client = None
        self.api_url = None
        self.entry_manager = None
        self.search_manager = None
        self.download_manager = None
        self.digital_objects_manager = None
        self.das_ai = None        

    def get_client(self):
        """Get DAS client instance, using saved API URL"""
        if not self.api_url:
            self.api_url = load_api_url() or DEFAULT_BASE_URL
            if not self.api_url:
                raise click.UsageError(
                    "No API URL configured. Please login first with 'das login --api-url <URL>'"
                )

        self.entry_manager = EntryManager()
        self.search_manager = SearchManager()
        self.download_manager = DownloadManager()
        self.digital_objects_manager = DigitalObjectsManager()
        # Set SSL verification based on saved config
        if not self.client:
            self.client = Das(self.api_url)
        
        return self.client

    def get_das_ai(self):
        """Get DAS AI instance"""
        if not self.das_ai:
            self.das_ai = DasAI()
        return self.das_ai

pass_das_context = click.make_pass_decorator(DasCLI, ensure=True)

@click.group()
@click.version_option(package_name="das-cli")
@click.pass_context
def cli(ctx):
    """DAS Python CLI - Data Archive System client tool"""
    ctx.obj = DasCLI()

@cli.command()
@click.option('--api-url', required=True, help='API base URL')
@click.option('--username', required=True, prompt=True, help='Username')
@click.option('--password', required=True, prompt=True, hide_input=True, help='Password')
@pass_das_context
def login(das_ctx, api_url, username, password):
    """Login and store authentication token"""
    # Save API URL for future use
    save_api_url(api_url)
    das_ctx.api_url = api_url
    
    # Authenticate
    client = das_ctx.get_client()
    token = client.authenticate(username, password)
    if not token:
        click.secho("❌ Authentication failed. Please check your credentials.", fg="red")
        return
    else:
        click.secho("✓ Authentication successful!", fg="green")

# Search commands group
@cli.group()
def search():
    """Commands for searching entries"""
    pass
    
@search.command("help")
def search_help():
    """Show help about search query syntax and formats"""
    click.secho("\nSearch Query Syntax Help", fg="green", bold=True)
    click.echo("=" * 50)
    
    click.secho("\nBasic Search:", fg="blue", bold=True)
    click.echo("  das search entries --attribute <AttributeName> --query '<SearchQuery>'")
    click.echo("  Example: das search entries --attribute Cores --query 'name(*64*)'")
    
    click.secho("\nOutput Formats:", fg="blue", bold=True)
    click.echo("  --format table     Format results in a nice table (default)")
    click.echo("  --format json      Return results as JSON")
    click.echo("  --format compact   Simple one-line-per-result format")
    click.echo("  --raw              Show raw API response")
    
    click.secho("\nQuery Syntax Examples:", fg="blue", bold=True)
    click.echo("  'name(*pattern*)'              Search for pattern in name")
    click.echo("  'name(*pattern*);code(*ABC*)'  Multiple conditions (AND)")
    click.echo("  'Create at(>2023-01-01)'       Date comparison")
    
    click.secho("\nGet Detailed Information:", fg="blue", bold=True)
    click.echo("  das search entry <ID>          Get detailed info for a single entry")
    click.echo("  Example: das search entry 6b0e68e6-00cd-43a7-9c51-d56c9c091123")
    
    click.secho("\nPagination:", fg="blue", bold=True)
    click.echo("  --page <num>       Show specific page of results")
    click.echo("  --max-results <n>  Number of results per page (default: 10)")
    
    click.secho("\nSorting:", fg="blue", bold=True)
    click.echo("  --sort-by <field>  Field to sort by (default: Name)")
    click.echo("  --sort-order <order> Sort order: 'asc' or 'desc' (default: asc)")
    click.echo("\n")

@search.command("entries")
@click.option('--attribute', required=True, help='Attribute name to search in')
@click.option('--query', required=True, help='Search query string')
@click.option('--max-results', default=10, help='Maximum number of results to return')
@click.option('--page', default=1, help='Page number for paginated results')
@click.option('--sort-by', default='Name', help='Field to sort by (default: Name)')
@click.option('--sort-order', default='asc', type=click.Choice(['asc', 'desc']), help='Sort order (asc or desc)')
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json', 'compact']), help='Output format (table, json, or compact)')
@click.option('--raw', is_flag=True, help='Show raw response from API')
@pass_das_context
def search_entries(das_ctx, attribute, query, max_results, page, sort_by, sort_order, output_format, raw):
    """Search entries based on attribute and query"""
    try:
        # Ensure client and search_manager are initialized
        das_ctx.get_client()
        
        results = das_ctx.search_manager.search_entries(
            attribute=attribute,
            query=query,
            max_results=max_results,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        if raw:
            click.echo(results)
            return
            
        total_count = results.get('totalCount', 0)
        items = results.get('items', [])
        
        # Display search summary
        click.secho(f"\nFound {total_count} results for query: '{query}' in attribute: '{attribute}'", fg="blue")
        click.secho(f"Showing results {(page-1)*max_results + 1}-{min(page*max_results, total_count)} of {total_count}\n", fg="blue")
        
        if not items:
            click.secho("No results found.", fg="yellow")
            return
            
        if output_format == 'json':
            click.echo(json.dumps(results, indent=2))
        elif output_format == 'compact':
            for i, item in enumerate(items, 1):
                entry = item.get('entry', {})
                code = entry.get('code', 'N/A')
                name = entry.get('displayname', 'Unnamed')
                description = entry.get('description', 'No description')
                click.echo(f"{i}. {name} (Code: {code}) - {description}")
        else:  # table format
            headers = ["#", "Code", "Name", "Description", "Owner"]
            table_data = []
            
            for i, item in enumerate(items, 1):
                entry = item.get('entry', {})
                table_data.append([
                    i,
                    entry.get('code', 'N/A'),
                    entry.get('displayname', 'Unnamed'),
                    entry.get('description', 'No description')[:50] + ('...' if entry.get('description', '') and len(entry.get('description', '')) > 50 else ''),
                    entry.get('owner', 'Unknown')
                ])
            
            click.echo(format_table(table_data, headers))
            
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

# Hangfire commands group
@search.command("entry")
@click.argument('entry_id', required=True)
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']), help='Output format (table or json)')
@pass_das_context
def get_entry(das_ctx, entry_id, output_format):
    """Get detailed information about a single entry by ID"""
    try:
        # Ensure client and entry_manager are initialized
        das_ctx.get_client()
        # Reusing the entry manager to get entry details by ID
        entry = das_ctx.entry_manager.get_entry(entry_id)
        
        if output_format == 'json':
            click.echo(json.dumps(entry, indent=2))
        else:
            click.secho(f"\nEntry Details (ID: {entry_id})", fg="blue", bold=True)
            click.echo("=" * 50)
            
            if not entry or not isinstance(entry, dict):
                click.secho("No entry found with the specified ID.", fg="yellow")
                return
                
            # Format display fields in a readable way
            formatted_data = []
            for key, value in sorted(entry.items()):
                # Skip empty or None values
                if value is None or value == '':
                    continue
                    
                # Format date fields
                if isinstance(value, str) and key.lower().endswith(('time', 'date')) and 'T' in value:
                    try:
                        date_part = value.split('T')[0]
                        time_part = value.split('T')[1].split('.')[0]
                        value = f"{date_part} {time_part}"
                    except:
                        pass  # Keep original if formatting fails
                        
                # Add to formatted data
                formatted_data.append((key, value))
            
            # Display as key-value pairs
            for key, value in formatted_data:
                click.echo(f"{key.ljust(25)}: {value}")
                
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@cli.group()
def hangfire():
    """Commands for working with Hangfire tasks"""
    pass

@hangfire.command("sync-doi")
@click.argument('id', required=True)
@pass_das_context
def sync_doi(das_ctx, id):
    """Trigger a DOI synchronization task by ID"""
    client = das_ctx.get_client()
    try:
        client.hangfire.sync_doi(id)
        click.secho(f"✓ DOI synchronization task triggered!", fg="green")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

# Entries commands group
@cli.group()
def entry():
    """Commands for working with entries"""
    pass

@entry.command("update")
@click.option('--attribute', required=True, help='Attribute name')
@click.option('--code', help='Entry code to update (only used when --data is provided)')
@click.argument('file_path', required=False)
@click.option('--data', help='Data string in format { "key1": "value1", "key2": "value2", ... } or a list of such objects')
@pass_das_context
def update_entry(das_ctx, attribute, code=None, file_path=None, data=None):
    """Update entries from file or data string
    
    Each entry to update must contain a Code field that identifies the entry.
    Files can contain multiple entries (rows in CSV/XLS or list of objects in JSON).
    
    Examples:
    
    \b
    # Update entries from JSON file
    das entry update --attribute core c:\\data\\entries.json
    
    \b
    # Update entries from CSV file
    das entry update --attribute core c:\\data\\entries.csv
    
    \b
    # Update entries from Excel file
    das entry update --attribute core c:\\data\\entries.xls
    
    \b
    # Update a single entry from data string
    das entry update --attribute core --code ENT001 --data { 'Grant Public Access': Yes, ... }
    
    \b
    # Update multiple entries from data string
    das entry update --attribute core --data [{ 'Code': 'ENT001', ... }, { 'Code': 'ENT002', ... }]
    """
    try:
        # Ensure client and entry_manager are initialized
        das_ctx.get_client()
        if not file_path and not data:
            raise click.UsageError("Please provide either a file path or data string")
            
        entry_data = None
        is_bulk_update = False
        
        if file_path:
            click.echo(f"Loading data from file: {file_path}")
            entry_data = load_file_based_on_extension(file_path)
            
            # Check if we got a list or a single object
            if isinstance(entry_data, list):
                is_bulk_update = True
                click.echo(f"Found {len(entry_data)} entries to update")
            else:
                # If we got a single object but no code was provided, check if it has a Code field
                if not code:
                    # Look for Code field (case-insensitive)
                    entry_code = next((entry_data.get(key) for key in entry_data if key.lower() == 'code'), None)
                    if not entry_code:
                        raise click.UsageError("No code provided and entry data doesn't contain a Code field")
                    code = entry_code
                    
        elif data:
            click.echo("Parsing data string")
            entry_data = parse_data_string(data)
            
            # Check if we got a list or a single object
            if isinstance(entry_data, list):
                is_bulk_update = True
                click.echo(f"Found {len(entry_data)} entries to update")
            elif not code:
                # If we got a single object but no code was provided, check if it has a Code field
                entry_code = next((entry_data.get(key) for key in entry_data if key.lower() == 'code'), None)
                if not entry_code:
                    raise click.UsageError("No code provided and data doesn't contain a Code field")
                code = entry_code
                
        if not entry_data:
            raise click.UsageError("No valid entry data found")

        # Update the entries
        if is_bulk_update:
            results = das_ctx.entry_manager.update(attribute=attribute, entries=entry_data)
            
            # Display results
            success_count = sum(1 for result in results if result.get('status') == 'success')
            error_count = len(results) - success_count
            
            if success_count > 0:
                click.secho(f"✓ Successfully updated {success_count} entries", fg="green")
                
            if error_count > 0:
                click.secho(f"✗ Failed to update {error_count} entries", fg="red")
                
                # Show details of the failures
                click.echo("\nFailed updates:")
                for result in results:
                    if result.get('status') == 'error':
                        click.echo(f"  Code: {result.get('code', 'Unknown')}, Error: {result.get('error', 'Unknown error')}")
        else:
            # Single entry update
            results = das_ctx.entry_manager.update(attribute=attribute, code=code, entry=entry_data)
            
            if results and results[0].get('status') == 'success':
                click.secho(f"✓ Entry '{code}' updated successfully!", fg="green")
                click.echo(f"Entry ID: {results[0].get('id')}")
            else:
                error_msg = results[0].get('error', 'No response from server') if results else 'No response from server'
                click.secho(f"Entry update failed: {error_msg}", fg="red")
            
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@entry.command("delete")
@click.argument('code', required=True)
@pass_das_context
def delete_entry(das_ctx, code):
    """Delete entry by its code"""
    client = das_ctx.get_client()
    try:
        client.entries.delete(code)
        click.secho(f"✓ Entry '{code}' deleted!", fg="green")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@entry.command("link-digital-objects")
@click.option('--entry-code', required=True, help='Entry code to link/unlink digital objects to')
@click.option('--digital-object-code', '-d', multiple=True, required=True, help='Digital object code. Use multiple times for multiple objects.')
@click.option('--unlink', is_flag=True, help='Unlink specified digital objects from the entry instead of linking')
@pass_das_context
def link_digital_objects(das_ctx, entry_code, digital_object_code, unlink):
    """Link or unlink existing digital objects to an entry by their codes.

    Examples:

    \b
    # Link two digital objects to an entry
    das entry link-digital-objects --entry-code ENT001 -d DO001 -d DO002

    \b
    # Unlink a digital object from an entry
    das entry link-digital-objects --entry-code ENT001 -d DO003 --unlink
    """
    try:
        das_ctx.get_client()
        codes = list(digital_object_code)
        if not codes:
            raise click.UsageError("Please provide at least one --digital-object-code")

        success = das_ctx.digital_objects_manager.link_existing_digital_objects(
            entry_code=entry_code,
            digital_object_code_list=codes,
            is_unlink=unlink,
        )

        if success:
            action = "unlinked" if unlink else "linked"
            click.secho(f"✓ Successfully {action} {len(codes)} digital object(s) for entry '{entry_code}'", fg="green")
        else:
            click.secho("Operation did not report success.", fg="yellow")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@entry.command("create")
@click.option('--attribute', required=True, help='Attribute name')
@click.argument('file_path', required=False)
@click.option('--data', help='Data string in format { "key1": "value1", "key2": "value2", ... } or a list of such objects')
@pass_das_context
def create_entry(das_ctx, attribute, file_path=None, data=None):
    """Create one or more entries from file or data string
    
    Files can contain multiple entries (rows in CSV/XLS or list of objects in JSON).
    
    Examples:
    
    \b
    # Create entries from JSON file
    das entry create --attribute core c:\\data\\entries.json
    
    \b
    # Create entries from CSV file
    das entry create --attribute core c:\\data\\entries.csv
    
    \b
    # Create entries from Excel file
    das entry create --attribute core c:\\data\\entries.xls
    
    \b
    # Create a single entry from data string
    das entry create --attribute core --data { 'Grant Public Access': Yes, ... }
    
    \b
    # Create multiple entries from data string
    das entry create --attribute core --data [{ 'Name': 'Entry 1', ... }, { 'Name': 'Entry 2', ... }]
    """
    try:
        # Ensure client and entry_manager are initialized
        das_ctx.get_client()
        if not file_path and not data:
            raise click.UsageError("Please provide either a file path or data string")
            
        entry_data = None
        is_bulk_create = False
        
        if file_path:
            click.echo(f"Loading data from file: {file_path}")
            entry_data = load_file_based_on_extension(file_path)
            
            # Check if we got a list or a single object
            if isinstance(entry_data, list):
                is_bulk_create = True
                click.echo(f"Found {len(entry_data)} entries to create")
                
        elif data:
            click.echo("Parsing data string")
            entry_data = parse_data_string(data)
            
            # Check if we got a list or a single object
            if isinstance(entry_data, list):
                is_bulk_create = True
                click.echo(f"Found {len(entry_data)} entries to create")
                
        if not entry_data:
            raise click.UsageError("No valid entry data found")

        # Create the entries
        if is_bulk_create:
            results = das_ctx.entry_manager.create(attribute=attribute, entries=entry_data)
            
            # Display results
            success_count = sum(1 for result in results if result.get('status') == 'success')
            error_count = len(results) - success_count
            
            if success_count > 0:
                click.secho(f"✓ Successfully created {success_count} entries", fg="green")
                
                # Show IDs of created entries
                click.echo("\nCreated entry IDs:")
                for result in results:
                    if result.get('status') == 'success':
                        click.echo(f"  {result.get('id')}")
                
            if error_count > 0:
                click.secho(f"✗ Failed to create {error_count} entries", fg="red")
                
                # Show details of the failures
                click.echo("\nFailed creations:")
                for i, result in enumerate(results):
                    if result.get('status') == 'error':
                        click.echo(f"  Entry #{i+1}: {result.get('error', 'Unknown error')}")
        else:
            # Single entry creation
            results = das_ctx.entry_manager.create(attribute=attribute, entry=entry_data)
            
            if results and results[0].get('status') == 'success':
                click.secho(f"✓ Entry created successfully!", fg="green")
                click.echo(f"Entry ID: {results[0].get('id')}")
            else:
                error_msg = results[0].get('error', 'No ID returned') if results else 'No ID returned'
                click.secho(f"Entry creation failed: {error_msg}", fg="red")
            
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@entry.command("upload-digital-object")
@click.option('--entry-code', required=True, help='Entry code to attach the digital object to')
@click.option('--type', 'digital_object_type', required=True, help='Digital object type name (e.g., Dataset, File, Image)')
@click.option('--description', 'file_description', default='', help='Description for the uploaded file')
@click.argument('file_path', required=True)
@pass_das_context
def upload_digital_object(das_ctx, entry_code, digital_object_type, file_description, file_path):
    """Upload a file as a digital object and link it to an entry.

    Examples:

    \b
    # Upload a dataset file and link to an entry
    das entry upload-digital-object --entry-code ENT001 --type Dataset --description "CTD raw" c:\\data\\ctd.zip
    """
    try:
        # Ensure services are initialized
        das_ctx.get_client()

        # Perform upload and link
        digital_object_id = das_ctx.digital_objects_manager.upload_digital_object(
            entry_code=entry_code,
            file_description=file_description,
            digital_object_type=digital_object_type,
            file_path=file_path,
        )

        if digital_object_id:
            click.secho("✓ Digital object uploaded and linked successfully!", fg="green")
            click.echo(f"Digital Object ID: {digital_object_id}")
        else:
            click.secho("Upload completed but no ID was returned.", fg="yellow")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@entry.command("get")
@click.option('--code', default=None, help='Entry code')
@click.option('--id', type=int, default=None, help='Entry ID')
@pass_das_context
def get_entry(das_ctx, code=None, id=None):
    """Get entry by either its code or ID"""

    if not code and not id:
        raise click.UsageError("Please provide either an entry code or ID")
    
    try:
        # Ensure client and entry_manager are initialized
        das_ctx.get_client()
        # Pass client as a named parameter to avoid conflicts with 'id' parameter
        entry = das_ctx.entry_manager.get(code=code, id=id)
        if entry:
            click.secho("Entry Details:", fg="green", bold=True)
            click.echo("─" * 40)
            for key, value in entry.items():
                if key == 'Digital Object(s)' and isinstance(value, list):
                    continue
                elif isinstance(value, list):                    
                    click.echo(f"{key}:")
                    for item in value:
                        click.echo(f"  - {item}")                    
                else:  
                    click.echo(f"{key}: {value or ''}")

            # if entry contains key: Digital Object(s) and its a list, print each object details
            # with indentation for better readability
            if 'Digital Object(s)' in entry and isinstance(entry['Digital Object(s)'], list):
                click.echo()
                click.echo("─" * 40)
                click.echo("Digital Object(s):")
                for obj in entry['Digital Object(s)']:
                    click.echo(f"  - ID: {obj.get('Id')}")
                    click.echo(f"    Name: {obj.get('Name')}")
                    click.echo(f"    Type: {obj.get('Type')}")
                    click.echo(f"    Links: {obj.get('Links')}")
                    click.echo()                    
            click.echo("─" * 40)
        else:
            click.secho("Entry not found.", fg="yellow")
            click.echo("Please check the entry code or ID.")

    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@entry.command("chown")
@click.option('--user', 'user_name', required=True, help='New owner username')
@click.option('--code', '-c', multiple=True, required=True, help='Entry code to transfer. Can be used multiple times.')
@pass_das_context
def chown_entries(das_ctx, user_name, code):
    """Change ownership of one or more entries by their codes.

    Example:

    \b
    das entry chown --user alice --code ENT001 --code ENT002
    """
    try:
        # Ensure services are initialized
        das_ctx.get_client()

        entry_codes = list(code)
        if not entry_codes:
            raise click.UsageError("Please provide at least one --code")

        result = das_ctx.entry_manager.chown(user_name=user_name, entry_code_list=entry_codes)

        # If API returns a plain success or list, just report success
        click.secho("✓ Ownership updated successfully!", fg="green")
        if isinstance(result, dict):
            # Show minimal feedback if available
            updated = result.get('updated') or result.get('result') or result
            if updated:
                click.echo(json.dumps(updated, indent=2))
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

# Attribute commands group
@cli.group()
def attribute():
    """Commands for working with attributes"""
    pass

# Cache commands group
@cli.group()
def cache():
    """Commands for working with cache"""
    pass

# Config commands group
@cli.group()
def config():
    """Commands for configuring the CLI"""
    pass

@cache.command("clear-all")
@pass_das_context
def clear_all_cache(das_ctx):
    """Clear all cache entries"""
    client = das_ctx.get_client()
    try:
        result = client.cache.clear_all()
        if result.get('success'):
            click.secho("✓ All cache cleared!", fg="green")
        else:
            click.secho("Failed to clear cache.", fg="red")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@cache.command("list")
@pass_das_context
def list_cache(das_ctx):
    """List all cache entries"""
    client = das_ctx.get_client()
    try:
        caches = client.cache.get_all()
        if caches:
            click.secho("Cache Entries:", fg="green", bold=True)
            click.echo("─" * 40)
            # Sort cache items by name before displaying
            sorted_caches = sorted(caches.get('items', []), key=lambda x: x.get('name', '').lower())
            for cache in sorted_caches:
                click.echo(f"Name: {cache.get('name')}")
            click.echo("─" * 40)
        else:
            click.secho("No cache entries found.", fg="yellow")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")   

@cache.command("clear")
@click.argument('name', required=True)
@pass_das_context
def clear_cache(das_ctx, name):
    """Clear a specific cache by name"""
    client = das_ctx.get_client()
    try:
        result = client.cache.clear_cache(name)
        if result.get('success'):
            click.secho(f"✓ Cache '{name}' cleared!", fg="green")
        else:
            click.secho(f"Failed to clear cache '{name}'.", fg="red")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@attribute.command("get")
@click.option('--id', type=int, default=None, help='Attribute ID')
@click.option('--name', default=None, help='Attribute name')
@click.option('--alias', default=None, help='Attribute alias')
@click.option('--table-name', default=None, help='Table name')
@pass_das_context
def get_attribute(das_ctx, id, name, alias, table_name):
    """Get attribute by ID, name, alias, or table name"""
    if not any([id, name, alias, table_name]):
        raise click.UsageError("Please provide at least one search parameter")
        
    client = das_ctx.get_client()
    try:
        result = client.attributes.get_attribute(id=id, name=name, alias=alias, table_name=table_name)
        if result.get('success') and result.get('result', {}).get('items'):
            attributes = result['result']['items']
            for attr in attributes:
                click.secho("\nAttribute Details:", fg="green", bold=True)
                click.echo("─" * 40)
                click.echo(f"ID:          {attr.get('id')}")
                click.echo(f"Name:        {attr.get('name')}")
                click.echo(f"Description: {attr.get('description')}")
                click.echo(f"Alias:       {attr.get('alias')}")
                click.echo(f"Table Name:  {attr.get('tableName')}")
                click.echo(f"Menu Name:   {attr.get('menuName')}")
                click.echo(f"Context:     {attr.get('contextName')}")
                click.echo(f"Indexable:   {attr.get('isIndexable')}")
                if attr.get('indexName'):
                    click.echo(f"Index Name:  {attr.get('indexName')}")
                click.echo("─" * 40)
        else:
            click.secho("No attributes found.", fg="yellow")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")


@attribute.command("get-name")
@click.argument('id', type=int, required=True)
@pass_das_context
def get_attribute_name(das_ctx, id):
    """Get attribute name by ID"""
    client = das_ctx.get_client()
    try:
        name = client.attributes.get_name(id)
        click.echo(name)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@attribute.command("get-id")
@click.argument('name', required=True)
@pass_das_context
def get_attribute_id(das_ctx, name):
    """Get attribute ID by name"""
    client = das_ctx.get_client()
    try:
        attr_id = client.attributes.get_id(name)
        click.echo(attr_id)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

# SSL verification commands
@config.command("ssl-verify")
@click.argument('enabled', type=click.Choice(['true', 'false']), required=True)
def set_ssl_verify(enabled):
    """Set SSL certificate verification (true/false)"""
    verify = enabled.lower() == 'true'
    save_verify_ssl(verify)
    status = "enabled" if verify else "disabled"
    click.echo(f"SSL certificate verification {status}")

@config.command("ssl-status")
def get_ssl_status():
    """Show current SSL certificate verification status"""
    status = "enabled" if VERIFY_SSL else "disabled"
    click.echo(f"SSL certificate verification is currently {status}")

@config.command("reset")
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def reset_config(force):
    """Clear all configuration files (token, URL, and authentication info)"""
    if not force:
        if not click.confirm("This will remove all saved credentials and configuration. Are you sure?"):
            click.echo("Operation cancelled.")
            return
    
    from das.common.config import clear_token, _config_dir
    import shutil

    # Clear token (handles both keyring and file-based storage)
    clear_token()
    
    # Get the config directory path
    config_dir = _config_dir()
    
    # Check if the directory exists
    if config_dir.exists():
        # Remove all files in the config directory
        for file_path in config_dir.glob("*"):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    click.echo(f"Removed: {file_path.name}")
                except Exception as e:
                    click.secho(f"Failed to remove {file_path.name}: {e}", fg="red")
    
    click.secho("✓ All configuration files and credentials have been removed.", fg="green")

# Download commands group
@cli.group()
def download():
    """Commands for working with downloads"""
    pass

@download.command("request")
@click.option('--name', help='Name for the download request (defaults to timestamp if not provided)')
@click.option('--entry', '-e', multiple=True, required=True, help='Entry code to download files from. Can be used multiple times.')
@click.option('--file', '-f', multiple=True, help='File codes to download. If not specified, all files will be downloaded.')
@click.option('--from-file', help='Load download request from a JSON file')
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']), help='Output format (table or json)')
@pass_das_context
def create_download_request(das_ctx, name, entry, file, from_file, output_format):
    """
    Create a new download request for specified entries and files
    
    Examples:
    
    \b
    # Download all files from an entry
    das download request --entry ENT001
    
    \b
    # Download specific files from an entry
    das download request --entry ENT001 --file FILE001 --file FILE002
    
    \b
    # Download from multiple entries
    das download request --entry ENT001 --entry ENT002 --name "My Download"
    
    \b
    # Download specific files from multiple entries
    das download request --entry ENT001 --file FILE001 --entry ENT002 --file FILE003
    
    \b
    # Download using a JSON file specification
    das download request --from-file request.json
    """
    try:
        request_data = {}
        
        # Handle name parameter
        if name:
            request_data['name'] = name
            
        # Handle from-file parameter
        if from_file:
            click.echo(f"Loading download request from file: {from_file}")
            try:
                with open(from_file, 'r') as f:
                    file_data = json.load(f)
                request_data.update(file_data)
            except Exception as e:
                raise click.UsageError(f"Failed to load file: {e}")
        # Handle entry and file parameters
        else:
            # Group files by entry
            current_entry = None
            entry_files = {}
            
            # If we have entries and files, we need to pair them correctly
            if entry and file:
                for arg in sys.argv:
                    if arg == '--entry' or arg == '-e':
                        # Next arg will be an entry code
                        current_entry = None
                    elif arg == '--file' or arg == '-f':
                        # Next arg will be a file code
                        pass
                    elif current_entry is None and arg in entry:
                        # This is an entry code
                        current_entry = arg
                        if current_entry not in entry_files:
                            entry_files[current_entry] = []
                    elif current_entry is not None and arg in file:
                        # This is a file code for the current entry
                        entry_files[current_entry].append(arg)
            else:
                # If we have entries but no files, download all files for each entry
                for e in entry:
                    entry_files[e] = []
                    
            # Update request_data with the entry files
            for e, files in entry_files.items():
                request_data[e] = files
                
        if not request_data or all(key == 'name' for key in request_data.keys()):
            raise click.UsageError("No download request data provided")
            
        # Execute the download request
        # Make sure client and download_manager are initialized
        das_ctx.get_client()
        result = das_ctx.download_manager.create_download_request(request_data)
        
        # Check if result contains errors
        if isinstance(result, dict) and 'errors' in result:
            click.secho("Download request failed with errors:", fg="red")
            for error in result['errors']:
                click.secho(f"- {error}", fg="red")
            return
            
        # Handle the result based on its type
        if output_format == 'json':
            # If result is a string (just the ID), wrap it in a dict for consistent JSON output
            if isinstance(result, str):
                click.echo(json.dumps({"id": result}, indent=2))
            else:
                click.echo(json.dumps(result, indent=2))
        else:
            click.secho("✓ Download request created successfully!", fg="green")
            
            # If result is a string, it's just the request ID
            if isinstance(result, str):
                request_id = result
                click.echo(f"Request ID: {request_id}")
                
                # Show download instructions
                click.echo("\nUse the following command to check the status of your download:")
                click.secho(f"  das download status {request_id}", fg="cyan")
            else:
                # Handle the case where result is a dictionary with more information
                request_id = result.get('id', 'Unknown')
                click.echo(f"Request ID: {request_id}")
                click.echo(f"Status: {result.get('status', 'Pending')}")
                
                # Display files in the request if available
                if result.get('items'):
                    click.secho("\nFiles in this download request:", fg="blue")
                    
                    headers = ["#", "File Name", "Entry", "Size", "Status"]
                    table_data = []
                    
                    for i, item in enumerate(result.get('items', []), 1):
                        file_info = item.get('fileInfo', {})
                        table_data.append([
                            i,
                            file_info.get('name', 'Unknown'),
                            file_info.get('entryCode', 'Unknown'),
                            file_info.get('size', 'Unknown'),
                            item.get('status', 'Pending')
                        ])
                    
                    click.echo(format_table(table_data, headers))
                
                # Show download instructions
                click.echo("\nUse the following command to check the status of your download:")
                click.secho(f"  das download status {request_id}", fg="cyan")
            
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@download.command("files")
@click.argument('request_id', required=True)
@click.option('--out', 'output_path', required=False, default='.', help='Output file path or directory (defaults to current directory)')
@click.option('--force', is_flag=True, help='Overwrite existing file if present')
@pass_das_context
def download_files(das_ctx, request_id, output_path, force):
    """
    Download the completed bundle for a download request and save it to disk.

    Examples:

    \b
    # Save into current directory with server-provided filename
    das download files 6b0e68e6-00cd-43a7-9c51-d56c9c091123

    \b
    # Save to a specific folder
    das download files 6b0e68e6-00cd-43a7-9c51-d56c9c091123 --out C:\\Downloads

    \b
    # Save to an explicit filename, overwriting if exists
    das download files 6b0e68e6-00cd-43a7-9c51-d56c9c091123 --out C:\\Downloads\\bundle.zip --force
    """
    try:
        das_ctx.get_client()
        saved_path = das_ctx.download_manager.save_download(request_id=request_id, output_path=output_path, overwrite=force)
        click.secho(f"✓ Download saved to: {saved_path}", fg="green")
    except FileExistsError as e:
        click.secho(str(e), fg="yellow")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

@download.command("delete-request")
@click.argument('request_id', required=True)
@pass_das_context
def delete_download_request(das_ctx, request_id):
    """
    Delete a download request by its ID
    
    Example:
    
    \b
    # Delete a download request
    das download delete-request 6b0e68e6-00cd-43a7-9c51-d56c9c091123
    """
    try:
        # Ensure client and download_manager are initialized
        das_ctx.get_client()
        
        # Call the delete_download_request method
        result = das_ctx.download_manager.delete_download_request(request_id)
        
        # Display success message
        click.secho(f"✓ Download request '{request_id}' deleted successfully!", fg="green")
            
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")


@download.command("my-requests")
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']), help='Output format (table or json)')
@pass_das_context
def list_my_download_requests(das_ctx, output_format):
    """List your download requests in a user-friendly format"""
    try:
        # Ensure services are initialized
        das_ctx.get_client()
        result = das_ctx.download_manager.get_my_requests()

        # Normalize result shape
        total_count = 0
        items = []
        if isinstance(result, dict):
            total_count = result.get('totalCount', 0)
            items = result.get('items', [])
        elif isinstance(result, list):
            items = result
            total_count = len(items)

        if output_format == 'json':
            payload = { 'totalCount': total_count, 'items': items }
            click.echo(json.dumps(payload, indent=2))
            return

        if not items:
            click.secho("No download requests found.", fg="yellow")
            return

        # Build a compact table
        headers = ["#", "ID", "Requester", "Created", "Status", "Files"]
        table_data = []

        from das.common.enums import DownloadRequestStatus

        def map_status(code):
            try:
                return DownloadRequestStatus(code).name.replace('_', ' ').title()
            except Exception:
                return str(code)

        def fmt_dt(dt_str):
            if not isinstance(dt_str, str) or 'T' not in dt_str:
                return dt_str or ''
            date_part = dt_str.split('T')[0]
            time_part = dt_str.split('T')[1].split('.')[0]
            return f"{date_part} {time_part}"

        for i, req in enumerate(items, 1):
            req_id = req.get('id', '')
            requester = req.get('requester', '')
            created = fmt_dt(req.get('createdOn'))
            status = map_status(req.get('status'))
            files = req.get('files') or []
            file_count = len(files)
            table_data.append([
                i,
                req_id[:8],
                requester.split(' - ')[0] if isinstance(requester, str) else requester,
                created,
                status,
                file_count
            ])

        click.secho(f"\nYour download requests ({total_count})", fg="blue")
        click.echo(format_table(table_data, headers))

        # Show a brief file breakdown below the table
        click.secho("\nDetails:", fg="blue")
        for i, req in enumerate(items, 1):
            files = req.get('files') or []
            if not files:
                continue
            click.echo(f"{i}. {req.get('id', '')}")
            for f in files[:5]:
                # Map item status if present
                status_code = f.get('status')
                status_label = None
                try:
                    from das.common.enums import DownloadRequestItemStatus
                    status_label = DownloadRequestItemStatus(status_code).name.replace('_', ' ').title()
                except Exception:
                    status_label = str(status_code)
                click.echo(f"   - {f.get('fileName', f.get('needle', ''))} [{status_label}] ({f.get('digitalObjectType', '')})")
            if len(files) > 5:
                click.echo(f"   ... and {len(files) - 5} more")

    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

# DAS AI commands group
@cli.group()
def ai():
    """Commands for working with DAS AI"""
    pass

@ai.command("enable")
@pass_das_context
def enable_das_ai(das_ctx):
    """Enable DAS AI interactive mode"""
    try:
        # Ensure OpenAI API key is configured
        api_key = os.getenv("OPENAI_API_KEY") or load_openai_api_key()
        if not api_key:
            click.secho("No OpenAI API key found.", fg="yellow")
            click.echo("You can set it via environment variable OPENAI_API_KEY, or save it now.")
            key = click.prompt("Enter your OpenAI API key", hide_input=True)
            if not key:
                raise click.UsageError("OpenAI API key is required to enable DAS AI.")
            save_openai_api_key(key)
            click.secho("✓ OpenAI API key saved securely.", fg="green")

        # Get DAS AI instance
        das_ai = das_ctx.get_das_ai()
        
        click.secho("🤖 DAS AI is now enabled!", fg="green", bold=True)
        click.echo("Starting interactive AI session...")
        click.echo("Type 'exit' to quit the AI session.")
        click.echo("=" * 50)
        
        # Run the AI main loop
        import asyncio
        asyncio.run(das_ai.main())
        
    except Exception as e:
        click.secho(f"Error enabling DAS AI: {e}", fg="red")
        click.echo("Make sure you have set your OPENAI_API_KEY environment variable.")

def _ai_clear_impl(force: bool):
    if not force:
        if not click.confirm("This will remove your saved OpenAI API key and authentication token. Continue?"):
            click.echo("Operation cancelled.")
            return
    try:
        clear_openai_api_key()
        clear_token()
        cfg_dir = _config_dir()
        removed_any = False
        for fname in ["openai_key.json", "token.json"]:
            p = cfg_dir / fname
            if p.exists() and p.is_file():
                try:
                    p.unlink()
                    removed_any = True
                except Exception:
                    pass
        click.secho("✓ DAS AI credentials cleared.", fg="green")
        if removed_any:
            click.echo("Local credential files removed.")
    except Exception as e:
        click.secho(f"Error clearing credentials: {e}", fg="red")

@ai.command("clear")
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def ai_clear(force):
    """Clear DAS AI credentials (OpenAI key) and auth token."""
    _ai_clear_impl(force)

@ai.command("logout")
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def ai_logout(force):
    """Alias for 'das ai clear'"""
    _ai_clear_impl(force)

if __name__ == "__main__":
	cli()
