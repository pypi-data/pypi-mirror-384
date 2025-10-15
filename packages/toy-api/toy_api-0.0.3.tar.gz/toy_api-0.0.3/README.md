# Toy API

Easily configurable test API servers and dummy Database generation for development and testing.

--- 

- [Overview](#overview)
  - [Toy Api](#toy-api)
  - [Toy Database](#toy-database)
- [CLI](#cli)
  - [Commands](#commands)
  - [Examples](#examples)
- [Configuration and Syntax](#configuration-and-syntax)
  - [API Configuration and Syntax](#api-configuration-and-syntax)
  - [Database Configuration and Syntax](#database-configuration-and-syntax)
- [Using Toy API in Your Own Projects](#using-toy-api-in-your-own-projects)
  - [Basic Integration](#basic-integration)
  - [Framework Examples](#framework-examples)
- [Install/Requirements](#installrequirements)
- [License](#license)

---

**FEATURES**

- **Configurable Test APIs**: Launch Flask-based test APIs with YAML configuration
- **Dummy Data Generation**: Generate realistic test data for users, posts, permissions, and more
- **Multiple Output Formats**: Export data as Parquet, CSV, JSON, or line-delimited JSON
- **Background Server Management**: Start/stop multiple servers with process tracking
- **Version Support**: Handle multiple API versions in subdirectories
- **Port Auto-Selection**: Automatic port selection when configured port is unavailable
- **Flexible Responses**: Built-in response types with dynamic data generation

---

## Overview

### Toy APIs

To generate dummy-data there are a number of built-in response-type generators:

- `api_info`: API metadata
- `user_list`: List of users
- `user_detail`: Single user details
- `user_profile`: User profile
- `user_permissions`: User permissions
- `post_list`: List of posts
- `post_detail`: Single post
- `health_check`: Health status

Given these generators, we can then define a toy-api in a config file:

```yaml
# toy_api_config/apis/example.yaml
name: my-api
description: Simple test API
port: 1234

routes:
  - route: "/"
    methods: ["GET"]
    response: "core.api_info"

  - route: "/users"
    methods: ["GET"]
    response: "core.user_list"

  - route: "/users/{{user_id}}"
    methods: ["GET"]
    response: "core.user"
```

Running `toy-api start example` will launch a Flask API filled with dummy data at `http://127.0.0.1:1234`:

- `/`: API metadata
- `/users`: List of users
- `/users/1001`: User details

See [API Configuration and Syntax](#api-configuration-and-syntax) for more details.

### Toy Database

Similarly, an entire database can be created with a simple config file:

```yaml
# toy_api_config/databases/example_db.yaml
config:
  NB_USERS: 10

shared:
  user_id[[NB_USERS]]: UNIQUE[int]
  region_name: CHOOSE[[Atlanta, San Francisco, New York]][1]

tables:
  users[[NB_USERS]]:
    user_id: [[user_id]]
    age: CHOOSE[[21-89]]
    name: NAME
    job: JOB
    nice: bool
    region_name: [[region_name]]

  permissions:
    user_id: [[user_id]]
    permissions: PERMISSIONS[n]

  regions:
    region_name: [[region_name]]
    area: CHOOSE[[1000-9000]]
```

Running `toy_api database example_db` will generate Parquet files in the `databases/example_db/` directory with realistic dummy data. See [Database Configuration and Syntax](#database-configuration-and-syntax) for more details.

---

## Usage

### CLI

#### Commands

Toy API provides a modern Click-based CLI:

- **toy_api** (default): List all available configurations
- **toy_api init**: Initialize `toy_api_config/` directory with example configs
- **toy_api start [config]**: Start API server (foreground or background with --all)
- **toy_api stop [config]**: Stop running server(s)
- **toy_api ps**: List running servers
- **toy_api list**: List all available configurations
- **toy_api database <config>**: Generate tables from database configuration

#### Examples

```bash
# Initialize local configuration directory
toy_api init

# List available configurations
toy_api list

# Start API server (foreground)
toy_api start example
toy_api start example --port 5000
toy_api start example --host 0.0.0.0 --debug

# Start all servers in background
toy_api start --all
toy_api start --all versioned_remote
toy_api start --all versioned_remote --out versioned_remote/0.1

# Check running servers
toy_api ps

# Stop servers
toy_api stop example
toy_api stop --all
toy_api stop --all versioned_remote

# Generate database tables
toy_api database example_db
toy_api database example_db --type csv
toy_api database example_db --tables users,permissions
toy_api database example_db --dest output/ --force

# Generate all databases
toy_api database --all
toy_api database --all versioned_db
```

**For more details**, see the [CLI Reference Wiki](https://github.com/yourusername/toy_api/wiki/CLI-Reference).

---

## Configuration and Syntax

Assume our file structure is:

```bash
toy_api_config
├── apis
│   ├── example.yaml
│   ├── api_v1.yaml
│   ├── api_v2.yaml
│   └── versioned_remote
│       ├── 0.1.yaml
│       ├── 0.2.yaml
│       └── 1.2.yaml
├── databases
│   ├── example_db.yaml
│   └── test_db.yaml
└── objects
    └── custom.yaml
```

---

### API Configuration and Syntax

API configurations are stored in the `toy_api_config/apis/` directory. Each config defines:
- **name**: API identifier
- **description**: API description
- **port**: Port to bind to (or omit for auto-selection)
- **routes**: List of endpoint definitions

#### Basic Example

```yaml
# toy_api_config/apis/example.yaml
name: my-api
description: Simple test API
port: 1234

routes:
  - route: "/"
    methods: ["GET"]
    response: "core.api_info"

  - route: "/users"
    methods: ["GET"]
    response: "core.user_list"

  - route: "/users/{{user_id}}"
    methods: ["GET"]
    response: "core.user"
```

#### Variable Placeholders

Routes use double curly braces `{{}}` for variable placeholders (converted to Flask notation internally):

- `/users`: Matches exactly "/users"
- `/users/{{user_id}}`: Matches "/users/123", "/users/abc", etc.
- `/users/{{user_id}}/posts`: Matches "/users/123/posts"

**Note**: Use `{{variable}}` notation in config files. The system converts this to Flask's `<variable>` notation internally.

#### Response Types

All responses use object-based generation with explicit namespace prefixes:

**Built-in core objects** (use `core.*` prefix):

- `core.api_info`: API metadata
- `core.user_list`: Paginated list of users
- `core.user`: Single user details
- `core.user_profile`: Extended user profile
- `core.user_permissions`: User permissions and role
- `core.user_settings`: User settings/preferences
- `core.post_list`: Paginated list of posts
- `core.post`: Single post details
- `core.health_check`: Health status

See [Object-Based Data Generation](#object-based-data-generation-new) for custom objects.


#### Port Management

```yaml
port: 8000              # Fixed port
# OR omit for auto-selection (8000-9000 range)
```

If a configured port is unavailable, Toy API automatically selects the next available port.

#### Multiple Methods

```yaml
- route: "/users/{{user_id}}"
  methods: ["GET", "POST", "PUT"]
  response: "core.user"
```

#### Configuration Discovery

Toy API searches for configs in priority order:

1. **Local configs** - `toy_api_config/apis/*.yaml`
2. **Package configs** - Built-in configurations (in `config/apis/`)

**For more details**, see the [API Configuration Wiki](https://github.com/yourusername/toy_api/wiki/API-Configuration).

---

### Database Configuration and Syntax

Database configurations are stored in `toy_api_config/databases/` directory. Each database defines:
- **config**: Reusable configuration variables
- **shared**: Shared data across tables
- **tables**: Table definitions with column specifications

Database configs use special syntax for data generation:

#### Double Square Brackets `[[]]`

Reference config variables or shared data:

```yaml
config:
  NB_USERS: 10

shared:
  user_id[[NB_USERS]]: UNIQUE[int]

tables:
  users[[NB_USERS]]:
    user_id: [[user_id]]
```

#### Data Types

Basic data types:

- `str`: Random string
- `int`: Random integer (0-1000)
- `float`: Random float (0-1000)
- `bool`: Random boolean

#### UNIQUE - Generate Unique Values

```yaml
id: UNIQUE[int]      # 1000, 1001, 1002, ...
code: UNIQUE[str]    # unique_0000, unique_0001, ...
```

#### CHOOSE - Select from List or Range

```yaml
city: CHOOSE[[NYC, LA, SF]]              # Random city
age: CHOOSE[[21-89]]                     # Random age 21-89
tags: CHOOSE[[a, b, c, d]][2]           # Exactly 2 tags
items: CHOOSE[[1-100]][5]               # 5 random numbers
random: CHOOSE[[x, y, z]][n]            # 1-3 items
```

#### Constants

**Singular** (single value):
- `FIRST_NAME`, `LAST_NAME`, `LOCATION`, `PERMISSION`
- `THEME`, `LANGUAGE`, `POST_TAG`, `JOB`

**Plural** (list of values):
- `FIRST_NAMES`, `LAST_NAMES`, `LOCATIONS`, `PERMISSIONS`
- `THEMES`, `LANGUAGES`, `POST_TAGS`, `JOBS`

**With count**:

```yaml
tags: POST_TAGS[3]          # Exactly 3 tags
perms: PERMISSIONS[n]       # 1 to all permissions
```

**Special**:

```yaml
name: NAME                  # Full name (first + last)
names: NAMES                # List of full names
```

#### Shared Data

Share columns across tables:

```yaml
shared:
  user_id[10]: UNIQUE[int]          # Create 10 unique IDs
  regions: CHOOSE[[A, B, C]][1]     # Create region list

tables:
  users[10]:
    user_id: [[user_id]]            # Reference shared IDs
    region: [[regions]]             # Reference regions
```

#### Config Variables

Define reusable values:

```yaml
config:
  NB_USERS: 20
  NB_POSTS: 100

shared:
  user_id[[NB_USERS]]: UNIQUE[int]

tables:
  users[[NB_USERS]]:
    user_id: [[user_id]]

  posts[[NB_POSTS]]:
    user_id: [[user_id]]
```

#### Object-Based Data Generation (NEW!)

Define reusable object templates for cleaner configs:

**Define objects** in `config/objects/` or `toy_api_config/objects/`:

```yaml
# config/objects/my_objects.yaml
user:
  user_id: UNIQUE[int]
  name: NAME
  email: str
  active: bool

post:
  post_id: UNIQUE[int]
  title: POST_TITLE
  content: str
  tags: POST_TAGS[3]
```

**Use objects** in table definitions:

```yaml
tables:
  # Reference object
  users[[10]]:
    object: "my_objects.user"

  # Reference object with overrides
  users_with_region[[10]]:
    object: "my_objects.user"
    user_id: [[shared_user_id]]  # Override field
    region: LOCATION              # Add new field
```

**Reference objects within objects**:

When referencing objects or using `[[...]]` syntax in object definitions, **quote the value** to prevent YAML from parsing it as a list:

```yaml
# In config/objects/my_objects.yaml
user_list:
  users: "[[object.my_objects.user]][5]"  # CORRECT - quoted
  total: 5

# user_list:
#   users: [[object.my_objects.user]][5]  # WRONG - parsed as nested list
```

**Built-in objects** in `config/objects/core.yaml`:
- `core.user` - Basic user
- `core.user_profile` - Extended user profile
- `core.user_permissions` - User permissions
- `core.post` - Blog post
- `core.health_check` - Health check response
- And more...

**Use in API responses**:

```yaml
routes:
  - route: "/users/{{user_id}}"
    methods: ["GET"]
    response: "core.user"  # Object-based response!
```

**Benefits**:
- Reusable definitions across tables and APIs
- Consistent data structure
- Override/extend as needed
- **Fully backward compatible** - old syntax still works!

#### Complete Example

```yaml
name: example_db
description: Example database with user data
authors:
  - API Team

config:
  NB_USERS: 10

shared:
  user_id[[NB_USERS]]: UNIQUE[int]
  region_name: CHOOSE[[Atlanta, San Francisco, New York]][1]

tables:
  users[[NB_USERS]]:
    user_id: [[user_id]]
    age: CHOOSE[[21-89]]
    name: NAME
    job: JOB
    active: bool
    region_name: [[region_name]]

  permissions:
    user_id: [[user_id]]
    permission_name: PERMISSIONS[n]
    granted_date: str

  regions:
    region_name: [[region_name]]
    area: CHOOSE[[1000-9000]]
    population: int
```

**For more details**, see the [Table Generation Syntax Wiki](https://github.com/yourusername/toy_api/wiki/Table-Generation-Syntax).

---

## Using Toy API in Your Own Projects

The core functionality is available as standalone modules that can be integrated into any Python project.

### Basic Integration

#### Creating an API

```python
from toy_api.app import create_app

# Create Flask app from config
app = create_app("toy_api_config/apis/example.yaml")

# Run the app
app.run(host="127.0.0.1", port=5000)
```

#### Generating Tables

```python
from toy_api.table_generator import create_table

# Generate tables from database config
create_table(
    table_config="toy_api_config/databases/example_db.yaml",
    dest="output",
    file_type="parquet"
)
```

### Framework Examples

#### Django Integration

```python
# In your Django app
from toy_api.app import _load_config, create_app

# Load config for use in Django views
config = _load_config("path/to/config.yaml")

# Or mount Toy API as a sub-application
toy_app = create_app("path/to/config.yaml")
```

#### FastAPI Integration

```python
from fastapi import FastAPI
from toy_api.app import create_app

app = FastAPI()

# Mount Toy API as sub-app
toy_app = create_app("toy_api_config/apis/example.yaml")
app.mount("/toy", toy_app)
```

#### Pytest Integration

```python
import pytest
from toy_api.app import create_app

@pytest.fixture
def toy_api_client():
    app = create_app("tests/fixtures/test_api.yaml")
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_users_endpoint(toy_api_client):
    response = toy_api_client.get('/users')
    assert response.status_code == 200
    assert isinstance(response.json, list)
```

---

## Install/Requirements

Requirements are managed through a [Pixi](https://pixi.sh/latest) "project" (similar to a conda environment). After pixi is installed use `pixi run <cmd>` to ensure the correct project is being used. For example,

```bash
# launch jupyter
pixi run jupyter lab .

# run a script
pixi run python scripts/example.py

# run toy_api commands
pixi run toy_api start example
```

The first time `pixi run` is executed the project will be installed (note this means the first run will be a bit slower). Any changes to the project will be updated on the subsequent `pixi run`. It is unnecessary, but you can run `pixi install` after changes - this will update your local environment, so that it does not need to be updated on the next `pixi run`.

Note, the repo's `pyproject.toml`, and `pixi.lock` files ensure `pixi run` will just work. No need to recreate an environment. Additionally, the `pyproject.toml` file includes `toy_api = { path = ".", editable = true }`. This line is equivalent to `pip install -e .`, so there is no need to pip install this module.

The project was initially created using a `package_names.txt` and the following steps. Note that this should **NOT** be re-run as it will create a new project (potentially changing package versions).

```bash
#
# IMPORTANT: Do NOT run this unless you explicitly want to create a new pixi project
#
# 1. initialize pixi project (in this case the pyproject.toml file had already existed)
pixi init . --format pyproject
# 2. add specified python version
pixi add python=3.11
# 3. add packages (note this will use pixi magic to determine/fix package version ranges)
pixi add $(cat package_names.txt)
# 4. add pypi-packages, if any (note this will use pixi magic to determine/fix package version ranges)
pixi add --pypi $(cat pypi_package_names.txt)
```

---

## License

BSD 3-Clause
