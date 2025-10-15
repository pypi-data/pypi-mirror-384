# Port Experience

A Python CLI tool for managing [Port.io](https://www.getport.io/) resources including blueprints, actions, mappings, and widgets from local JSON files.

## Installation

```bash
pip install port-experience
```

## Quick Start

1. **Set up your Port.io credentials**:
   ```bash
   # Option 1: Environment variables
   export PORT_CLIENT_ID="your_client_id_here"
   export PORT_CLIENT_SECRET="your_client_secret_here"
   
   # Option 2: Using .env file (recommended)
   echo "PORT_CLIENT_ID=your_client_id_here" > .env
   echo "PORT_CLIENT_SECRET=your_client_secret_here" >> .env
   ```

2. **Create your resource files** in JSON format in a `setup/` directory:
   ```
   your-project/
   ├── setup/
   │   ├── blueprints/
   │   │   └── my_blueprint.json
   │   ├── actions/
   │   │   └── my_action.json
   │   ├── mappings/
   │   │   └── my_mapping.json
   │   └── widgets/
   │       └── my_widget.json
   └── .env
   ```

3. **Apply your configurations**:
   ```bash
   # Apply the changes directly
   experience apply --sample-experience
   
   # Apply the changes from the experience directory
   cd sample-experience
   experience apply
   ```

## Features

- 🎯 **Multi-Resource Management**: Handle blueprints, actions, mappings, and widgets
- 🔄 **Smart Sync**: Compare and merge local resources with existing Port.io resources
- ✅ **Interactive Confirmation**: Review changes before applying them
- 🛡️ **Safe Updates**: Preserve existing data while adding new configurations
- 📊 **Detailed Reporting**: Clear summary of all operations

## Usage

### CLI Commands

```bash
# Apply all configurations (looks for setup/ directory)
experience apply

# Use a custom project directory
experience apply --my-project  # looks for my-project/.env and my-project/setup/

# Get help
experience --help
```

### Setup Directory Structure

The CLI automatically looks for your configuration files in this structure:

```
your-project/
├── setup/                    # Default directory
│   ├── blueprints/
│   ├── actions/
│   ├── mappings/
│   └── widgets/
└── .env                      # Your credentials
```

Or with a custom project name:

```
your-project/
├── .env                     # Default credentials (fallback)
├── my-project/
│   ├── .env                 # Project-specific credentials (preferred)
│   └── setup/               # Setup folder inside the project
│       ├── blueprints/
│       ├── actions/
│       ├── mappings/
│       └── widgets/
```

**Note**: When using `--my-project`, the CLI will look for `my-project/.env` and `my-project/setup/` directory structure.

### Programmatic Usage

```python
from port_experience import PortBlueprintManager

manager = PortBlueprintManager(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Setup all blueprints from directory
results = manager.setup_all_blueprints("setup/blueprints")
```

## Resource JSON Examples

**Blueprint** (`setup/blueprints/service.json`):
```json
{
  "identifier": "service",
  "title": "Service",
  "icon": "Microservice",
  "schema": {
    "properties": {
      "name": {"type": "string", "title": "Name"},
      "version": {"type": "string", "title": "Version"}
    }
  }
}
```

**Action** (`setup/actions/deploy.json`):
```json
{
  "identifier": "deploy",
  "title": "Deploy Service",
  "icon": "Rocket",
  "blueprint": "service",
  "invocationMethod": {
    "type": "WEBHOOK"
  }
}
```

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT_CLIENT_ID` | Your Port.io API Client ID |
| `PORT_CLIENT_SECRET` | Your Port.io API Client Secret |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLUEPRINTS_DIR` | Path to blueprints directory | `setup/blueprints` |
| `ACTIONS_DIR` | Path to actions directory | `setup/actions` |
| `MAPPINGS_DIR` | Path to mappings directory | `setup/mappings` |
| `WIDGETS_DIR` | Path to widgets directory | `setup/widgets` |
| `LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

### Using .env Files

Create a `.env` file in your project root for easier credential management:

```bash
# .env (in your current working directory)
PORT_CLIENT_ID=your_client_id_here
PORT_CLIENT_SECRET=your_client_secret_here
BLUEPRINTS_DIR=my-custom/blueprints
LOG_LEVEL=DEBUG
```

**Environment File Priority**: 
1. **Project-specific**: When using `--my-project`, looks for `my-project/.env` first
2. **Current directory**: Falls back to `.env` in the current working directory  
3. **Environment variables**: Uses system environment variables as final fallback

**Directory Structure**: Each project should have its own folder containing both the `.env` file and a `setup/` subdirectory with the configuration files.

## Getting Port.io Credentials

1. Log in to your [Port.io](https://app.getport.io) account
2. Navigate to **Settings** → **Credentials**
3. Create a new API client or use existing credentials
4. Copy the Client ID and Client Secret

## License

MIT
