"""
Port Experience CLI
==================

Command-line interface for the Port Experience middleware service.
Provides structured commands for managing Port.io resources.
"""

import os
import sys
from pathlib import Path
import click
from port_experience.main import (
    load_env_file,
    get_client_credentials,
    check_existing_resources,
    get_user_confirmation,
    PortBlueprintManager,
    PortActionManager,
    PortMappingManager,
    PortWidgetManager,
)


@click.group()
@click.version_option(version="0.1.0", prog_name="experience")
def cli():
    """
    Experience - Apply Port.io configurations from local files.
    
    A simple CLI to create, update, and synchronize Port.io configurations
    including blueprints, actions, mappings, and widgets.
    """
    # Load environment variables from default location
    load_env_file()


def _determine_setup_directory(project_name):
    """
    Determine the setup directory based on dynamic project option.

    Args:
        project_name: The project name from the dynamic option (e.g., 'roi-dashboard')

    Returns:
        str: Path to the setup directory
    """
    if project_name:
        setup_dir = f'{project_name}/setup'
        if not Path(setup_dir).exists():
            click.echo(f"❌ Error: Setup directory '{setup_dir}' not found", err=True)
            click.echo(f"   Expected structure: {project_name}/setup/{{blueprints,actions,mappings,widgets}}", err=True)
            sys.exit(1)
        return setup_dir

    default_setup_dir = 'setup'
    if not Path(default_setup_dir).exists():
        click.echo(f"❌ Error: Default setup directory '{default_setup_dir}' not found", err=True)
        click.echo("   Use a dynamic project option like --roi-dashboard to specify the correct path", err=True)
        click.echo("   Example: experience apply --roi-dashboard", err=True)
        sys.exit(1)

    return default_setup_dir


def _load_project_env_file(project_name):
    """
    Load .env file from project directory if it exists.

    Args:
        project_name: The project name (e.g., 'roi-dashboard')
    """
    if project_name:
        project_env_path = f'{project_name}/.env'
        if Path(project_env_path).exists():
            click.echo(f"📁 Loading environment variables from: {project_env_path}")
            load_env_file(project_env_path)
        else:
            click.echo(f"ℹ️  No .env file found in {project_name}/ directory, using current directory .env or environment variables")


def _check_dynamic_project_option(ctx):
    """
    Check if any dynamic project option was used (e.g., --roi-dashboard, --github-dashboard).

    Args:
        ctx: Click context object

    Returns:
        str or None: The project name if a dynamic option was found, None otherwise
    """
    # Check the extra args that Click captured
    extra_args = ctx.args

    for arg in extra_args:
        if arg.startswith('--'):
            # Found a dynamic project option
            project_name = arg[2:]  # Remove '--' prefix

            # Check if this looks like a valid project name (no spaces, reasonable characters)
            if project_name.replace('-', '').replace('_', '').isalnum():
                click.echo(f"🎯 Using dynamic project option: {project_name}")
                return project_name

    return None


@cli.command(context_settings={'allow_extra_args': True, 'ignore_unknown_options': True})
@click.pass_context
def apply(ctx):
    """
    Apply Port.io configurations from local JSON files.
    
    Creates or updates blueprints, actions, mappings, and widgets in your 
    Port.io environment based on local configuration files.

    USAGE:
    --PROJECT-NAME           Use PROJECT-NAME/setup as the setup directory

    Examples:
      experience apply --roi-dashboard
      experience apply --github-dashboard
      experience apply --my-project
    """
    click.echo("🚀 Port Experience - Applying Configurations")
    
    # Check for dynamic project options (e.g., --roi-dashboard, --github-dashboard, etc.)
    dynamic_project_path = _check_dynamic_project_option(ctx)

    # Load project-specific .env file if using a custom project
    _load_project_env_file(dynamic_project_path)

    client_id, client_secret = get_client_credentials()
    
    if not client_id or not client_secret:
        click.echo("❌ Error: PORT_CLIENT_ID and PORT_CLIENT_SECRET must be set", err=True)
        click.echo("   Set them as environment variables or in a .env file", err=True)
        sys.exit(1)
    
    # Determine base setup directory based on dynamic project option
    base_setup_dir = _determine_setup_directory(dynamic_project_path)

    # Use environment variables with defaults, but override with determined base directory
    blueprints_dir = os.getenv('BLUEPRINTS_DIR', f'{base_setup_dir}/blueprints')
    actions_dir = os.getenv('ACTIONS_DIR', f'{base_setup_dir}/actions')
    mappings_dir = os.getenv('MAPPINGS_DIR', f'{base_setup_dir}/mappings')
    widgets_dir = os.getenv('WIDGETS_DIR', f'{base_setup_dir}/widgets')
    action = os.getenv('ACTION', 'all').lower()
    
    # Get expected/required folders from environment variable
    expected_folders_str = os.getenv('EXPECTED_FOLDERS', 'blueprints,actions,mappings,widgets')
    expected_folders_list = [folder.strip().lower() for folder in expected_folders_str.split(',')]
    
    click.echo(f"\n🔧 Configuration:")
    click.echo(f"  • Processing: {action}")
    click.echo(f"  • Base setup directory: {base_setup_dir}")
    click.echo(f"  • Required folders: {', '.join(expected_folders_list)}")
    click.echo(f"  • Blueprints directory: {blueprints_dir}")
    click.echo(f"  • Actions directory: {actions_dir}")
    click.echo(f"  • Mappings directory: {mappings_dir}")
    click.echo(f"  • Widgets directory: {widgets_dir}")
    
    success = True
    
    # Process blueprints
    success = _process_blueprints(client_id, client_secret, blueprints_dir,
                                expected_folders_list, False) and success
    
    # Process actions
    success = _process_actions(client_id, client_secret, actions_dir,
                             expected_folders_list, False) and success
    
    # Process mappings
    success = _process_mappings(client_id, client_secret, mappings_dir,
                              expected_folders_list, False) and success
    
    # Process widgets
    success = _process_widgets(client_id, client_secret, widgets_dir,
                             expected_folders_list, False) and success
    
    # Final status
    click.echo("\n" + "=" * 60)
    if success:
        click.echo("🎉 All operations completed successfully!")
        sys.exit(0)
    else:
        click.echo("❌ Some operations failed!")
        click.echo("\n🔍 Debug Information:")
        click.echo(f"  • Required folders: {', '.join(expected_folders_list)}")
        click.echo(f"  • Action filter: {action}")
        click.echo("\n💡 To see detailed error logs, check the console output above for specific failure reasons.")
        sys.exit(1)


def _process_blueprints(client_id, client_secret, blueprints_dir, expected_folders, skip_confirmation):
    """Process blueprints with error handling."""
    click.echo(f"\n📋 Setting up blueprints from: {blueprints_dir}")
    
    if not Path(blueprints_dir).exists():
        if 'blueprints' in expected_folders:
            click.echo(f"❌ Error: Required blueprints directory '{blueprints_dir}' not found", err=True)
            return False
        else:
            click.echo(f"⏭️  Blueprints directory '{blueprints_dir}' not found (not required, skipping)")
            return True
    
    comparison_results = check_existing_resources(client_id, client_secret, 'blueprints', blueprints_dir)
    
    if not comparison_results['local']:
        click.echo("❌ No local blueprints found to process")
        click.echo(f"   Directory contents: {list(Path(blueprints_dir).glob('*.json')) if Path(blueprints_dir).exists() else 'Directory does not exist'}")
        click.echo("   ⏭️  Skipping blueprint operations")
        return True
    
    # Get user confirmation unless skipped
    if not skip_confirmation and not get_user_confirmation(comparison_results, 'blueprints'):
        click.echo("\n❌ Operation cancelled by user")
        return False
    
    click.echo("\n🚀 Proceeding with blueprint operations...")
    
    blueprint_manager = PortBlueprintManager(client_id, client_secret)
    blueprint_results = blueprint_manager.setup_all_blueprints(blueprints_dir)
    
    success_count = 0
    failed_blueprints = []
    for identifier, blueprint_success in blueprint_results.items():
        status = "SUCCESS" if blueprint_success else "FAILED"
        click.echo(f"{identifier}: {status}")
        if blueprint_success:
            success_count += 1
        else:
            failed_blueprints.append(identifier)
    
    click.echo(f"Blueprint Summary: {success_count}/{len(blueprint_results)} blueprints created successfully")
    if failed_blueprints:
        click.echo(f"❌ Failed blueprints: {', '.join(failed_blueprints)}")
    
    return success_count == len(blueprint_results)


def _process_actions(client_id, client_secret, actions_dir, expected_folders, skip_confirmation):
    """Process actions with error handling."""
    click.echo(f"\n⚡ Setting up actions from: {actions_dir}")
    
    if not Path(actions_dir).exists():
        if 'actions' in expected_folders:
            click.echo(f"❌ Error: Required actions directory '{actions_dir}' not found", err=True)
            return False
        else:
            click.echo(f"⏭️  Actions directory '{actions_dir}' not found (not required, skipping)")
            return True
    
    comparison_results = check_existing_resources(client_id, client_secret, 'actions', actions_dir)
    
    if not comparison_results['local']:
        click.echo("❌ No local actions found to process")
        click.echo(f"   Directory contents: {list(Path(actions_dir).glob('*.json')) if Path(actions_dir).exists() else 'Directory does not exist'}")
        click.echo("   ⏭️  Skipping action operations")
        return True
    
    # Get user confirmation unless skipped
    if not skip_confirmation and not get_user_confirmation(comparison_results, 'actions'):
        click.echo("\n❌ Operation cancelled by user")
        return False
    
    click.echo("\n🚀 Proceeding with action operations...")
    
    action_manager = PortActionManager(client_id, client_secret)
    action_results = action_manager.setup_all_actions(actions_dir)
    
    success_count = 0
    failed_actions = []
    for identifier, action_success in action_results.items():
        status = "SUCCESS" if action_success else "FAILED"
        click.echo(f"{identifier}: {status}")
        if action_success:
            success_count += 1
        else:
            failed_actions.append(identifier)
    
    click.echo(f"Action Summary: {success_count}/{len(action_results)} actions created successfully")
    if failed_actions:
        click.echo(f"❌ Failed actions: {', '.join(failed_actions)}")
    
    return success_count == len(action_results)


def _process_mappings(client_id, client_secret, mappings_dir, expected_folders, skip_confirmation):
    """Process mappings with error handling."""
    click.echo(f"\n🔗 Applying mappings from: {mappings_dir}")
    
    if not Path(mappings_dir).exists():
        if 'mappings' in expected_folders:
            click.echo(f"❌ Error: Required mappings directory '{mappings_dir}' not found", err=True)
            return False
        else:
            click.echo(f"⏭️  Mappings directory '{mappings_dir}' not found (not required, skipping)")
            return True
    
    comparison_results = check_existing_resources(client_id, client_secret, 'mappings', mappings_dir)
    
    if not comparison_results['local']:
        click.echo("❌ No local mappings found to process")
        click.echo(f"   Directory contents: {list(Path(mappings_dir).glob('*.json')) if Path(mappings_dir).exists() else 'Directory does not exist'}")
        click.echo("   ⏭️  Skipping mapping operations")
        return True
    
    # Get user confirmation unless skipped
    if not skip_confirmation and not get_user_confirmation(comparison_results, 'mappings'):
        click.echo("\n❌ Operation cancelled by user")
        return False
    
    click.echo("\n🚀 Proceeding with mapping operations...")
    
    mapping_manager = PortMappingManager(client_id, client_secret)
    mapping_results = mapping_manager.apply_mappings(mappings_dir)
    
    success_count = 0
    failed_mappings = []
    for identifier, mapping_success in mapping_results.items():
        status = "SUCCESS" if mapping_success else "FAILED"
        click.echo(f"{identifier}: {status}")
        if mapping_success:
            success_count += 1
        else:
            failed_mappings.append(identifier)
    
    click.echo(f"Mapping Summary: {success_count}/{len(mapping_results)} mappings applied successfully")
    if failed_mappings:
        click.echo(f"❌ Failed mappings: {', '.join(failed_mappings)}")
    
    return success_count == len(mapping_results)


def _process_widgets(client_id, client_secret, widgets_dir, expected_folders, skip_confirmation):
    """Process widgets with error handling."""
    click.echo(f"\n📊 Setting up widgets from: {widgets_dir}")
    
    if not Path(widgets_dir).exists():
        if 'widgets' in expected_folders:
            click.echo(f"❌ Error: Required widgets directory '{widgets_dir}' not found", err=True)
            return False
        else:
            click.echo(f"⏭️  Widgets directory '{widgets_dir}' not found (not required, skipping)")
            return True
    
    comparison_results = check_existing_resources(client_id, client_secret, 'widgets', widgets_dir)
    
    if not comparison_results['local']:
        click.echo("❌ No local widgets found to process")
        click.echo(f"   Directory contents: {list(Path(widgets_dir).glob('*.json')) if Path(widgets_dir).exists() else 'Directory does not exist'}")
        click.echo("   ⏭️  Skipping widget operations")
        return True
    
    # Get user confirmation unless skipped
    if not skip_confirmation and not get_user_confirmation(comparison_results, 'widgets'):
        click.echo("\n❌ Operation cancelled by user")
        return False
    
    click.echo("\n🚀 Proceeding with widget operations...")
    
    widget_manager = PortWidgetManager(client_id, client_secret)
    widget_results = widget_manager.setup_all_widgets(widgets_dir)
    
    success_count = 0
    failed_widgets = []
    for identifier, widget_success in widget_results.items():
        status = "SUCCESS" if widget_success else "FAILED"
        click.echo(f"{identifier}: {status}")
        if widget_success:
            success_count += 1
        else:
            failed_widgets.append(identifier)
    
    click.echo(f"Widget Summary: {success_count}/{len(widget_results)} widgets created successfully")
    if failed_widgets:
        click.echo(f"❌ Failed widgets: {', '.join(failed_widgets)}")
    
    return success_count == len(widget_results)

if __name__ == '__main__':
    cli()
