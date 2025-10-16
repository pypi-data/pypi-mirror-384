"""

Dummy Data Generator Module for Toy API

Unified data generation system for both database tables and API responses.
Supports object definitions, config variables, shared data, and various data
types and verbs (UNIQUE, CHOOSE) with constants from toy_api.constants.

License: BSD 3-Clause

"""

#
# IMPORTS
#
import csv
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import yaml

from toy_api.constants import (
    ADMIN_ACTIVITIES,
    FIRST_NAMES,
    JOBS,
    LANGUAGES,
    LAST_NAMES,
    LOCATIONS,
    PERMISSIONS,
    POST_TAGS,
    POST_TITLES,
    THEMES
)


#
# CONSTANTS
#
# Object cache for loaded object definitions
_OBJECTS_CACHE: Dict[str, Dict[str, Any]] = {}

CONSTANT_MAP: Dict[str, List[str]] = {
    "FIRST_NAMES": FIRST_NAMES,
    "LAST_NAMES": LAST_NAMES,
    "POST_TITLES": POST_TITLES,
    "LOCATIONS": LOCATIONS,
    "PERMISSIONS": PERMISSIONS,
    "THEMES": THEMES,
    "LANGUAGES": LANGUAGES,
    "POST_TAGS": POST_TAGS,
    "ADMIN_ACTIVITIES": ADMIN_ACTIVITIES,
    "JOBS": JOBS,
    # Singular versions
    "FIRST_NAME": FIRST_NAMES,
    "LAST_NAME": LAST_NAMES,
    "POST_TITLE": POST_TITLES,
    "LOCATION": LOCATIONS,
    "PERMISSION": PERMISSIONS,
    "THEME": THEMES,
    "LANGUAGE": LANGUAGES,
    "POST_TAG": POST_TAGS,
    "ADMIN_ACTIVITY": ADMIN_ACTIVITIES,
    "JOB": JOBS,
}


#
# PUBLIC
#
def create_table(
        table_config: Union[str, Dict[str, Any]],
        dest: Optional[str] = None,
        file_type: Literal['parquet', 'csv', 'json', 'ld-json'] = 'parquet',
        partition_cols: Optional[List[str]] = None,
        to_dataframe: bool = False,
        tables_filter: Optional[List[str]] = None,
        force: bool = False) -> Union[List[Dict[str, Any]], Any]:
    """Create table data from configuration.

    Args:
        table_config: Path to YAML config file or config dictionary.
        dest: Optional destination path to write file.
        file_type: Output file format (parquet, csv, json, ld-json).
        partition_cols: Columns to partition by (parquet only).
        to_dataframe: Return DataFrame instead of list of dicts (if pandas available).
        tables_filter: Optional list of table names to generate (default: all).
        force: Overwrite existing files (default: False).

    Returns:
        List of dictionaries (one per row) or DataFrame if to_dataframe=True.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config format is invalid.
    """
    # Load configuration
    if isinstance(table_config, str):
        config = _load_config(table_config)
    else:
        config = table_config

    # Parse configuration
    config_values = config.get("config", {})
    shared_def = config.get("shared", {})
    tables_def = config.get("tables", {})

    # Filter tables if requested
    if tables_filter:
        filtered_tables_def = {}
        for table_name, columns in tables_def.items():
            # Parse table name (remove row count spec)
            parsed_name, _ = _parse_column_spec(table_name, config_values)
            if parsed_name in tables_filter:
                filtered_tables_def[table_name] = columns
        tables_def = filtered_tables_def

    # Generate shared data
    shared_data = _generate_shared(shared_def, config_values)

    # Generate all tables
    all_tables = {}
    for table_spec, columns in tables_def.items():
        # Parse table name to remove [[config]] syntax
        table_name, _ = _parse_column_spec(table_spec, config_values)
        table_data = _generate_table(table_spec, columns, shared_data, config_values)
        all_tables[table_name] = table_data

    # Write to file if dest provided
    if dest:
        _write_tables(all_tables, dest, file_type, partition_cols, force)

    # Return results
    if len(all_tables) == 1:
        # Single table - return just the table data
        result = list(all_tables.values())[0]
    else:
        # Multiple tables - return dict of table_name -> data
        result = all_tables

    # Convert to dataframe if requested
    if to_dataframe:
        try:
            import pandas as pd
            if isinstance(result, list):
                return pd.DataFrame(result)
            else:
                return {name: pd.DataFrame(data) for name, data in result.items()}
        except ImportError:
            # Pandas not available, return list of dicts
            pass

    return result


def generate_object(
        object_name: str,
        params: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        row_idx: int = 0) -> Dict[str, Any]:
    """Generate a single object instance.

    This is useful for generating API response data from object definitions.

    Args:
        object_name: Name of object to generate (e.g., 'core.user').
        params: Optional parameters for customization (e.g., {'user_id': '123'}).
        overrides: Optional field overrides to merge with object definition.
        row_idx: Row index for consistent random generation (default: 0).

    Returns:
        Dictionary containing generated object data.

    Raises:
        ValueError: If object not found.

    Examples:
        >>> generate_object('core.user')
        {'user_id': 1000, 'name': 'Alice Anderson', 'email': 'alice@example.com', ...}

        >>> generate_object('core.user', params={'user_id': '123'})
        {'user_id': '123', 'name': 'Bob Brown', ...}
    """
    objects = _load_objects()

    if object_name not in objects:
        raise ValueError(f"Object '{object_name}' not found in object definitions")

    # Get object definition
    obj_def = objects[object_name].copy()

    # Merge with overrides if provided
    if overrides:
        obj_def.update(overrides)

    # Generate object data
    obj_data = {}
    config_values = {}
    shared_data = {}

    for field_name, field_spec in obj_def.items():
        value = _generate_cell_value(field_spec, row_idx, config_values, shared_data)
        obj_data[field_name] = value

    # Apply parameter overrides (e.g., from URL params)
    if params:
        obj_data.update(params)

    return obj_data


#
# INTERNAL
#
def _load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file.

    Args:
        config_path: Path to YAML configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    with open(config_path, 'r') as file:
        return yaml.safe_load(file) or {}


def _generate_shared(shared_def: Dict[str, Any], config_values: Dict[str, Any]) -> Dict[str, List[Any]]:
    """Generate shared data columns.

    Args:
        shared_def: Shared column definitions.
        config_values: Config values for substitution.

    Returns:
        Dictionary mapping column names to lists of values.
    """
    shared_data = {}

    for col_spec, value_spec in shared_def.items():
        # Parse column name and optional row count
        col_name, row_count = _parse_column_spec(col_spec, config_values)

        # Generate column data
        column_values = _generate_column(value_spec, row_count, config_values, shared_data)

        shared_data[col_name] = column_values

    return shared_data


def _generate_table(
        table_spec: str,
        columns: Dict[str, Any],
        shared_data: Dict[str, List[Any]],
        config_values: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a single table.

    Args:
        table_spec: Table name with optional row count (e.g., "users[10]").
        columns: Column definitions (may include 'object' reference).
        shared_data: Shared data columns.
        config_values: Config values for substitution.

    Returns:
        List of row dictionaries.
    """
    # Resolve object reference if present
    columns = _resolve_object(columns)

    # Parse table name and row count
    table_name, row_count = _parse_column_spec(table_spec, config_values)

    # Determine actual row count from columns or shared data
    if row_count is None:
        # Find row count from shared data references
        for col_spec in columns.values():
            if isinstance(col_spec, str) and col_spec.startswith("[[") and col_spec.endswith("]]"):
                shared_col_name = col_spec[2:-2]
                if shared_col_name in shared_data:
                    row_count = len(shared_data[shared_col_name])
                    break

        # If still no row count, use random
        if row_count is None:
            row_count = random.randint(10, 50)

    # Generate table data
    table_data = []
    for row_idx in range(row_count):
        row = {}
        for col_name, value_spec in columns.items():
            value = _generate_cell_value(value_spec, row_idx, config_values, shared_data)
            row[col_name] = value
        table_data.append(row)

    return table_data


def _generate_column(
        value_spec: str,
        row_count: Optional[int],
        config_values: Dict[str, Any],
        shared_data: Dict[str, List[Any]]) -> List[Any]:
    """Generate values for an entire column.

    Args:
        value_spec: Value specification string.
        row_count: Number of rows to generate.
        config_values: Config values for substitution.
        shared_data: Shared data columns.

    Returns:
        List of column values.
    """
    if row_count is None:
        row_count = random.randint(10, 50)

    column_values = []
    for row_idx in range(row_count):
        value = _generate_cell_value(value_spec, row_idx, config_values, shared_data)
        column_values.append(value)

    return column_values


def _generate_cell_value(
        value_spec: Any,
        row_idx: int,
        config_values: Dict[str, Any],
        shared_data: Dict[str, List[Any]]) -> Any:
    """Generate a single cell value.

    Args:
        value_spec: Value specification (string, list, dict, or other type).
        row_idx: Row index for shared data lookup.
        config_values: Config values for substitution.
        shared_data: Shared data columns.

    Returns:
        Generated value.
    """
    # Handle YAML parsing of [[name]] as nested list
    # YAML interprets [[name]] as a list containing a list with one element
    if isinstance(value_spec, list):
        # Handle [[item]][[count]] syntax (e.g., [[object.core.user]][[n]])
        if len(value_spec) == 2:
            if isinstance(value_spec[0], list) and len(value_spec[0]) == 1:
                if isinstance(value_spec[1], list) and len(value_spec[1]) == 1:
                    item_spec = value_spec[0][0]
                    count_spec = value_spec[1][0]

                    # Handle [[object.NAMESPACE.NAME]][[count]]
                    if isinstance(item_spec, str) and item_spec.startswith('object.'):
                        object_name = item_spec[7:]  # Remove 'object.' prefix

                        # Determine count
                        if count_spec == 'n':
                            count = random.randint(1, 5)
                        else:
                            count = int(count_spec)

                        # Generate list of objects
                        return [
                            generate_object(object_name, row_idx=row_idx + i)
                            for i in range(count)
                        ]

        # Handle single [[item]] syntax
        if len(value_spec) == 1:
            if isinstance(value_spec[0], list) and len(value_spec[0]) == 1:
                item = value_spec[0][0]

                # Handle [[object.NAMESPACE.NAME]] - single object instance
                if isinstance(item, str) and item.startswith('object.'):
                    object_name = item[7:]  # Remove 'object.' prefix
                    return generate_object(object_name, row_idx=row_idx)

                # Handle [[300-500]] - range syntax
                if isinstance(item, str) and '-' in item and item.replace('-', '').isdigit():
                    parts = item.split('-')
                    start = int(parts[0])
                    end = int(parts[1])
                    return random.randint(start, end)

                # Handle [[shared_col_name]] - shared column reference
                shared_col_name = item
                if shared_col_name in shared_data:
                    shared_col = shared_data[shared_col_name]
                    if row_idx < len(shared_col):
                        return shared_col[row_idx]
                    else:
                        # Row index exceeds shared data length, choose random
                        return random.choice(shared_col)
                else:
                    raise ValueError(f"Shared column '{shared_col_name}' not found in shared data")

    # If value_spec is not a string, return it as-is
    if not isinstance(value_spec, str):
        return value_spec

    # Handle [[...]][count] string format (e.g., [[object.core.user]][5])
    match = re.match(r'\[\[([^\]]+)\]\]\[([^\]]+)\]', value_spec)
    if match:
        item_spec = match.group(1)
        count_spec = match.group(2)

        # Handle [[object.NAMESPACE.NAME]][count]
        if item_spec.startswith('object.'):
            object_name = item_spec[7:]  # Remove 'object.' prefix

            # Determine count
            if count_spec == 'n':
                count = random.randint(1, 5)
            else:
                count = int(count_spec)

            # Generate list of objects
            return [
                generate_object(object_name, row_idx=row_idx + i)
                for i in range(count)
            ]

        # Handle [[start-end]][count] - list of random numbers from range
        if '-' in item_spec and item_spec.replace('-', '').isdigit():
            parts = item_spec.split('-')
            start = int(parts[0])
            end = int(parts[1])

            if count_spec == 'n':
                count = random.randint(1, 5)
            else:
                count = int(count_spec)

            return [random.randint(start, end) for _ in range(count)]

    # Handle [[...]] string format
    if value_spec.startswith("[[") and value_spec.endswith("]]"):
        inner = value_spec[2:-2]

        # Handle [[object.NAMESPACE.NAME]] - single object instance
        if inner.startswith('object.'):
            object_name = inner[7:]  # Remove 'object.' prefix
            return generate_object(object_name, row_idx=row_idx)

        # Handle [[300-500]] - range syntax
        if '-' in inner and inner.replace('-', '').isdigit():
            parts = inner.split('-')
            start = int(parts[0])
            end = int(parts[1])
            return random.randint(start, end)

        # Handle [[shared_col_name]] - shared data reference
        if inner in shared_data:
            shared_col = shared_data[inner]
            if row_idx < len(shared_col):
                return shared_col[row_idx]
            else:
                # Row index exceeds shared data length, choose random
                return random.choice(shared_col)
        else:
            raise ValueError(f"Shared column '{inner}' not found")

    # Handle special NAME constant
    if value_spec == "NAME":
        return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

    if value_spec == "NAMES":
        count = random.randint(1, 5)
        return [f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" for _ in range(count)]

    # Handle UNIQUE verb
    if value_spec.startswith("UNIQUE["):
        return _generate_unique_value(value_spec, row_idx)

    # Handle CHOOSE verb
    if value_spec.startswith("CHOOSE["):
        return _generate_choose_value(value_spec, shared_data)

    # Handle DATE verb
    if value_spec.startswith("DATE"):
        return _generate_date_value(value_spec)

    # Handle constants
    if value_spec in CONSTANT_MAP:
        # Check if it's plural form (return list) or singular (return single)
        if value_spec.endswith("S"):
            count = random.randint(1, len(CONSTANT_MAP[value_spec]))
            return random.sample(CONSTANT_MAP[value_spec], count)
        else:
            return random.choice(CONSTANT_MAP[value_spec])

    # Handle constants with selection [n] or [int]
    match = re.match(r'([A-Z_]+)\[([n0-9]+)\]', value_spec)
    if match:
        const_name = match.group(1)
        count_spec = match.group(2)

        if const_name in CONSTANT_MAP:
            const_list = CONSTANT_MAP[const_name]
            if count_spec == 'n':
                count = random.randint(1, len(const_list))
            else:
                count = int(count_spec)
            count = min(count, len(const_list))
            return random.sample(const_list, count)

    # Handle basic types
    if value_spec == "str":
        return _generate_random_string()
    elif value_spec == "int":
        return random.randint(0, 1000)
    elif value_spec == "float":
        return round(random.uniform(0, 1000), 2)
    elif value_spec == "bool":
        return random.choice([True, False])

    # Default: return as-is
    return value_spec


def _generate_unique_value(value_spec: str, row_idx: int) -> Any:
    """Generate unique value based on specification.

    Args:
        value_spec: UNIQUE specification (e.g., "UNIQUE[int]").
        row_idx: Row index to use for unique value.

    Returns:
        Unique value.
    """
    # Extract type from UNIQUE[type]
    match = re.match(r'UNIQUE\[([^\]]+)\]', value_spec)
    if not match:
        return row_idx

    value_type = match.group(1)

    if value_type == "int":
        return row_idx + 1000  # Offset to avoid small numbers
    elif value_type == "str":
        return f"unique_{row_idx:04d}"
    else:
        return f"{value_type}_{row_idx}"


def _generate_choose_value(value_spec: str, shared_data: Dict[str, List[Any]]) -> Any:
    """Generate value using CHOOSE verb.

    Args:
        value_spec: CHOOSE specification (e.g., "CHOOSE[[a,b,c]][2]" or "CHOOSE[[user_id]]").
        shared_data: Shared data columns for column references.

    Returns:
        Chosen value(s).
    """
    # Parse CHOOSE[[items]][count] or CHOOSE[[items]]
    # Handle range syntax: CHOOSE[[21-89]]
    # Handle shared column reference: CHOOSE[[column_name]]
    # Single bracket for count parameter, double bracket for items
    pattern = r'CHOOSE\[\[([^\]]+)\]\](?:\[([^\]]+)\])?'
    match = re.match(pattern, value_spec)

    if not match:
        return None

    items_spec = match.group(1)
    count_spec = match.group(2)

    # Check if items_spec is a shared column reference
    if items_spec in shared_data:
        items = shared_data[items_spec]
    # Parse items
    elif '-' in items_spec and items_spec.replace('-', '').replace(' ', '').isdigit():
        # Range syntax: 21-89
        parts = items_spec.split('-')
        start = int(parts[0].strip())
        end = int(parts[1].strip())
        items = list(range(start, end + 1))
    else:
        # List syntax: a, b, c
        items = [item.strip() for item in items_spec.split(',')]

    # Determine count
    if count_spec is None:
        # No count specified - return single item
        return random.choice(items)
    elif count_spec == 'n':
        # Random count
        count = random.randint(1, len(items))
    elif count_spec == '1':
        # Exactly 1
        return random.choice(items)
    else:
        # Specific count
        count = int(count_spec)

    count = min(count, len(items))
    return random.sample(items, count)


def _generate_date_value(value_spec: str) -> str:
    """Generate random date string with optional formatting.

    Args:
        value_spec: DATE specification using Python strftime format.
                   Examples: "DATE" (default: %Y-%m-%d), "DATE[%Y%m%d:%H%M%S]"

    Returns:
        Formatted date string.
    """
    # Generate random datetime between 2020 and 2024
    from datetime import datetime, timedelta
    start_date = datetime(2020, 1, 1, 0, 0, 0)
    end_date = datetime(2024, 12, 31, 23, 59, 59)
    time_between = end_date - start_date
    seconds_between = int(time_between.total_seconds())
    random_seconds = random.randint(0, seconds_between)
    random_datetime = start_date + timedelta(seconds=random_seconds)

    # Extract format if provided
    if value_spec == "DATE":
        # Default format: YYYY-MM-DD
        return random_datetime.strftime("%Y-%m-%d")

    # Parse DATE[format]
    match = re.match(r'DATE\[([^\]]+)\]', value_spec)
    if match:
        format_spec = match.group(1)
        # Use format_spec directly as Python strftime format
        return random_datetime.strftime(format_spec)

    # Default fallback
    return random_datetime.strftime("%Y-%m-%d")


def _parse_column_spec(col_spec: str, config_values: Dict[str, Any]) -> tuple:
    """Parse column specification to extract name and optional row count.

    Args:
        col_spec: Column specification (e.g., "user_id[10]" or "user_id[[NB_USERS]]").
        config_values: Config values for substitution.

    Returns:
        Tuple of (column_name, row_count or None).
    """
    # Handle [[CONFIG_VAR]] syntax
    match = re.match(r'([^\[]+)\[\[([^\]]+)\]\]', col_spec)
    if match:
        col_name = match.group(1)
        config_var = match.group(2)
        row_count = config_values.get(config_var)
        return col_name, row_count

    # Handle [int] syntax
    match = re.match(r'([^\[]+)\[(\d+)\]', col_spec)
    if match:
        col_name = match.group(1)
        row_count = int(match.group(2))
        return col_name, row_count

    # No row count specified
    return col_spec, None


def _generate_random_string(length: int = 10) -> str:
    """Generate random string.

    Args:
        length: Length of string.

    Returns:
        Random string.
    """
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def _write_tables(
        tables: Dict[str, List[Dict[str, Any]]],
        dest: str,
        file_type: str,
        partition_cols: Optional[List[str]] = None,
        force: bool = False) -> None:
    """Write tables to files.

    Args:
        tables: Dictionary of table_name -> data.
        dest: Destination path.
        file_type: File format.
        partition_cols: Partition columns (parquet only).
        force: Overwrite existing files.
    """
    dest_path = Path(dest)

    # Always create directory structure (even for single table)
    dest_path.mkdir(parents=True, exist_ok=True)
    for table_name, table_data in tables.items():
        table_file = dest_path / f"{table_name}.{file_type}"
        _write_single_table(table_data, table_file, file_type, partition_cols, force)


def _write_single_table(
        data: List[Dict[str, Any]],
        file_path: Path,
        file_type: str,
        partition_cols: Optional[List[str]] = None,
        force: bool = False) -> None:
    """Write single table to file.

    Args:
        data: Table data as list of dicts.
        file_path: Output file path.
        file_type: File format.
        partition_cols: Partition columns (parquet only).
        force: Overwrite existing files.
    """
    # Check if file exists and force is False
    if file_path.exists() and not force:
        raise FileExistsError(f"File {file_path} already exists. Use force=True to overwrite.")

    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_type == 'parquet':
        _write_parquet(data, file_path, partition_cols)
    elif file_type == 'csv':
        _write_csv(data, file_path)
    elif file_type == 'json':
        _write_json(data, file_path)
    elif file_type == 'ld-json':
        _write_ld_json(data, file_path)


def _write_parquet(
        data: List[Dict[str, Any]],
        file_path: Path,
        partition_cols: Optional[List[str]] = None) -> None:
    """Write data to Parquet file.

    Args:
        data: Table data.
        file_path: Output file path.
        partition_cols: Partition columns.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        # Convert to PyArrow table
        table = pa.Table.from_pylist(data)

        # Write with or without partitioning
        if partition_cols:
            pq.write_to_dataset(table, root_path=str(file_path.parent),
                                partition_cols=partition_cols)
        else:
            pq.write_table(table, str(file_path))
    except ImportError:
        raise ImportError("PyArrow required for Parquet support. Install with: pip install pyarrow")


def _write_csv(data: List[Dict[str, Any]], file_path: Path) -> None:
    """Write data to CSV file.

    Args:
        data: Table data.
        file_path: Output file path.
    """
    if not data:
        return

    with open(file_path, 'w', newline='') as csvfile:
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def _write_json(data: List[Dict[str, Any]], file_path: Path) -> None:
    """Write data to JSON file.

    Args:
        data: Table data.
        file_path: Output file path.
    """
    with open(file_path, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=2)


def _write_ld_json(data: List[Dict[str, Any]], file_path: Path) -> None:
    """Write data to line-delimited JSON file.

    Args:
        data: Table data.
        file_path: Output file path.
    """
    with open(file_path, 'w') as jsonfile:
        for row in data:
            jsonfile.write(json.dumps(row) + '\n')


def _load_objects(search_paths: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """Load object definitions from YAML files.

    Args:
        search_paths: Optional list of paths to search for objects.
                     Defaults to local 'toy_api_config/objects' and package 'config/objects'.

    Returns:
        Dictionary mapping object names (file.key) to object definitions.
    """
    global _OBJECTS_CACHE

    if _OBJECTS_CACHE:
        return _OBJECTS_CACHE

    if search_paths is None:
        search_paths = []

        # Add local project objects directory
        local_objects = Path('toy_api_config') / 'objects'
        if local_objects.exists():
            search_paths.append(str(local_objects))

        # Add package objects directory (relative to this file)
        package_root = Path(__file__).parent.parent
        package_objects = package_root / 'config' / 'objects'
        if package_objects.exists():
            search_paths.append(str(package_objects))

    objects = {}

    for search_path in search_paths:
        obj_path = Path(search_path)
        if not obj_path.exists():
            continue

        # Load all .yaml files in the objects directory
        for yaml_file in obj_path.glob('*.yaml'):
            file_name = yaml_file.stem  # e.g., 'core' from 'core.yaml'

            try:
                with open(yaml_file, 'r') as f:
                    file_objects = yaml.safe_load(f) or {}

                # Each top-level key in the file is an object definition
                for obj_name, obj_def in file_objects.items():
                    full_name = f"{file_name}.{obj_name}"  # e.g., 'core.user'
                    objects[full_name] = obj_def

            except Exception as e:
                # Skip files that can't be loaded
                import sys
                print(f"Warning: Failed to load {yaml_file}: {e}", file=sys.stderr)
                continue

    _OBJECTS_CACHE = objects

    # Debug: print loaded objects on first load
    import sys
    print(f"DEBUG: Loaded {len(objects)} objects from paths: {search_paths}", file=sys.stderr)
    if 'core.user_list' in objects:
        print("DEBUG: ✓ core.user_list found", file=sys.stderr)
    else:
        print("DEBUG: ✗ core.user_list NOT found", file=sys.stderr)
        print(f"DEBUG: Available core objects: {[k for k in objects.keys() if k.startswith('core.')][:10]}", file=sys.stderr)

    return objects


def _resolve_object(columns: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve object reference in column definitions.

    If columns contains an 'object' key, load that object definition and
    merge it with any column overrides/additions.

    Args:
        columns: Column definitions dict, may contain 'object' key.

    Returns:
        Resolved column definitions with object expanded.
    """
    if 'object' not in columns:
        return columns

    object_ref = columns['object']
    objects = _load_objects()

    if object_ref not in objects:
        raise ValueError(f"Object '{object_ref}' not found in object definitions")

    # Start with object definition
    resolved = objects[object_ref].copy()

    # Override/extend with explicit column definitions
    for col_name, col_spec in columns.items():
        if col_name != 'object':
            resolved[col_name] = col_spec

    return resolved