import os
import sys
from pathlib import Path
from port_experience.managers.blueprint_manager import PortBlueprintManager
from port_experience.managers.action_manager import PortActionManager
from port_experience.managers.mapping_manager import PortMappingManager
from port_experience.managers.blueprint_tree_manager import BlueprintTreeManager
from port_experience.managers.widget_manager import PortWidgetManager


def load_env_file(env_file='.env'):
    """Load environment variables from .env file."""
    env_path = Path(env_file)
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


load_env_file()


def get_client_credentials() -> tuple[str, str]:
    """
    Get Port.io client ID and client secret from environment variables or .env file.

    Returns:
        Tuple of (client_id, client_secret)
    """
    client_id = os.getenv('PORT_CLIENT_ID')
    client_secret = os.getenv('PORT_CLIENT_SECRET')

    return client_id, client_secret


def check_existing_resources(client_id: str, client_secret: str, resource_type: str, resource_dir: str) -> dict:
    """
    Check existing resources in Port environment and compare with local resources.

    Args:
        client_id: Port client ID
        client_secret: Port client secret
        resource_type: Type of resource ('blueprints', 'actions', 'mappings', 'widgets')
        resource_dir: Path to local resources directory

    Returns:
        Dictionary with comparison results
    """
    print(f"\n🔍 Checking existing {resource_type} in your Port environment...")

    # Load local resources
    local_resources = {}
    if Path(resource_dir).exists():
        for filename in os.listdir(resource_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(resource_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        import json
                        resource_data = json.load(f)

                        # Extract identifier based on resource type
                        identifier = None
                        title = None

                        if resource_type == 'blueprints':
                            identifier = resource_data.get('identifier')
                            title = resource_data.get('title', identifier)
                        elif resource_type == 'actions':
                            identifier = resource_data.get('identifier')
                            title = resource_data.get('title', identifier)
                        elif resource_type == 'mappings':
                            identifier = resource_data.get('identifier')
                            title = resource_data.get('title', identifier)
                        elif resource_type == 'widgets':
                            identifier = resource_data.get('identifier')
                            title = resource_data.get('title', identifier)

                        if identifier:
                            local_resources[identifier] = {
                                'filename': filename,
                                'title': title or identifier,
                                'description': resource_data.get('description', 'No description'),
                                'data': resource_data
                            }
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")

    if not local_resources:
        print(f"❌ No local {resource_type} found!")
        return {'local': {}, 'existing': {}, 'to_create': [], 'to_update': []}

    # Check existing resources in Port
    if resource_type == 'blueprints':
        manager = PortBlueprintManager(client_id, client_secret)
        api_endpoint = '/v1/blueprints'
        exists_method = manager.blueprint_exists
    elif resource_type == 'actions':
        manager = PortActionManager(client_id, client_secret)
        api_endpoint = '/v1/actions'
        exists_method = manager.action_exists
    elif resource_type == 'mappings':
        manager = PortMappingManager(client_id, client_secret)
        api_endpoint = '/v1/integration'
        exists_method = manager.integration_exists
    elif resource_type == 'widgets':
        manager = PortWidgetManager(client_id, client_secret)
        api_endpoint = '/v1/pages'
        exists_method = manager.page_exists
    else:
        print(f"❌ Unknown resource type: {resource_type}")
        return {'local': {}, 'existing': {}, 'to_create': [], 'to_update': []}

    existing_resources = {}
    to_create = []
    to_update = []

    print(f"\n📋 Local {resource_type} found: {len(local_resources)}")
    for identifier, resource_info in local_resources.items():
        print(f"  • {identifier}: {resource_info['title']}")

        if exists_method(identifier):
            existing_resources[identifier] = resource_info
            to_update.append(identifier)
            print(f"    ✅ Already exists - will be UPDATED")
        else:
            to_create.append(identifier)
            print(f"    🆕 New {resource_type[:-1]} - will be CREATED")

    # Get all existing resources from Port (for reference)
    try:
        all_existing_response = manager.make_api_request('GET', api_endpoint)
        if all_existing_response:
            if resource_type == 'blueprints' and 'blueprints' in all_existing_response:
                all_existing = {bp['identifier']: bp.get('title', bp['identifier']) for bp in
                                all_existing_response['blueprints']}
            elif resource_type == 'actions' and 'actions' in all_existing_response:
                all_existing = {action['identifier']: action.get('title', action['identifier']) for action in
                                all_existing_response['actions']}
            elif resource_type == 'mappings' and isinstance(all_existing_response, list):
                all_existing = {integration['identifier']: integration.get('title', integration['identifier']) for
                                integration in all_existing_response}
            elif resource_type == 'widgets' and 'pages' in all_existing_response:
                all_existing = {page['identifier']: page.get('title', page['identifier']) for page in
                                all_existing_response['pages']}
            else:
                all_existing = {}

            other_existing = {k: v for k, v in all_existing.items() if k not in local_resources}
        else:
            other_existing = {}
    except Exception as e:
        print(f"⚠️  Could not fetch all existing {resource_type}: {e}")
        other_existing = {}

    return {
        'local': local_resources,
        'existing': existing_resources,
        'other_existing': other_existing,
        'to_create': to_create,
        'to_update': to_update
    }


def get_user_confirmation(comparison_results: dict, resource_type: str) -> bool:
    """
    Get user confirmation before proceeding with resource operations.

    Args:
        comparison_results: Results from resource comparison
        resource_type: Type of resource being processed

    Returns:
        True if user confirms, False otherwise
    """
    to_create = comparison_results['to_create']
    to_update = comparison_results['to_update']
    other_existing = comparison_results['other_existing']

    resource_name = resource_type.title()
    resource_name_singular = resource_type[:-1] if resource_type.endswith('s') else resource_type

    print("\n" + "=" * 60)
    print(f"📊 {resource_name} OPERATION SUMMARY")
    print("=" * 60)

    if to_create:
        print(f"\n🆕 {resource_name.upper()} TO BE CREATED ({len(to_create)}):")
        for identifier in to_create:
            resource_info = comparison_results['local'][identifier]
            print(f"  • {identifier}: {resource_info['title']}")

    if to_update:
        print(f"\n🔄 {resource_name.upper()} TO BE UPDATED/MERGED ({len(to_update)}):")
        for identifier in to_update:
            resource_info = comparison_results['local'][identifier]
            print(f"  • {identifier}: {resource_info['title']}")

    if not to_create and not to_update:
        print(f"\n✅ All {resource_type} are already up to date!")
        return True

    print("\n" + "=" * 60)
    print("⚠️  CONFIRMATION REQUIRED")
    print("=" * 60)

    print(f"\nThis operation will:")
    if to_create:
        print(f"  • CREATE {len(to_create)} new {resource_name_singular}(s)")
    if to_update:
        print(f"  • UPDATE/MERGE {len(to_update)} existing {resource_name_singular}(s)")

    print(f"\nThe operation will use the 'merge' strategy")
    print("This means existing resources will be updated with new properties,")
    print("and new properties will be added without removing existing ones.")

    while True:
        response = input("\nDo you want to proceed? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


# Main function is now handled by the CLI module
# This file contains the core functionality that can be imported and used programmatically

def main():
    """
    Legacy main function for backward compatibility.
    
    This function is deprecated. Use the CLI instead:
    port-experience apply
    """
    import warnings
    warnings.warn(
        "Direct execution of main.py is deprecated. Use 'port-experience apply' instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Import and call the CLI apply command for backward compatibility
    from port_experience.cli import apply
    import click
    
    # Set up environment variables for backward compatibility
    os.environ.setdefault('BLUEPRINTS_DIR', 'setup/blueprints')
    os.environ.setdefault('ACTIONS_DIR', 'setup/actions')
    os.environ.setdefault('MAPPINGS_DIR', 'setup/mappings')
    os.environ.setdefault('WIDGETS_DIR', 'setup/widgets')
    os.environ.setdefault('ACTION', 'all')
    os.environ.setdefault('EXPECTED_FOLDERS', 'blueprints,actions,mappings,widgets')
    
    # Call the apply command
    ctx = click.Context(apply)
    apply.invoke(ctx)


if __name__ == '__main__':
    main()
