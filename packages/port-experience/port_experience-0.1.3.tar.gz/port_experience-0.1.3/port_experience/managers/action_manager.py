import os
import re
from typing import List, Dict, Any

from port_experience.managers import BasePortManager


class PortActionManager(BasePortManager):
    """Manages Port.io actions creation and configuration."""

    def __init__(self, client_id: str, client_secret: str, port_host: str = "api.port.io"):
        """Initialize the Port Action Manager."""
        super().__init__(client_id, client_secret, port_host, "PortActionManager")

    def _substitute_variables(self, data: Any) -> Any:
        """
        Recursively substitute var__ prefixed keys with values from environment variables.

        Args:
            data: The data structure to process (dict, list, or primitive)

        Returns:
            Data with variables substituted
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key.startswith('var__'):
                    # The value should be the environment variable name
                    if isinstance(value, str):
                        env_var = value
                        env_value = os.getenv(env_var)

                        if env_value is not None:
                            # Use the environment variable value, key without 'var__' prefix
                            new_key = key[5:]  # Remove 'var__' prefix
                            result[new_key] = env_value
                            self.logger.info(
                                f"Substituted {key} -> {new_key} with value '{env_value}' from environment variable {env_var}")
                        else:
                            # Environment variable not found, keep original key but warn
                            result[key] = value
                            self.logger.warning(
                                f"Environment variable {env_var} not found for {key}, keeping original value")
                    else:
                        # Value is not a string, keep as is
                        result[key] = value
                        self.logger.warning(f"var__ key {key} has non-string value, cannot substitute")
                else:
                    # Recursively process nested structures
                    result[key] = self._substitute_variables(value)
            return result
        elif isinstance(data, list):
            return [self._substitute_variables(item) for item in data]
        else:
            # Primitive types (string, number, boolean, etc.) - return as is
            return data

    def discover_actions(self, actions_dir: str) -> List[Dict[str, Any]]:
        """
        Discover all action JSON files in the specified directory.

        Args:
            actions_dir: Path to the actions directory

        Returns:
            List of action configurations loaded from JSON files
        """
        actions = self.discover_json_files(actions_dir, "actions")

        valid_actions = []
        for action_info in actions:
            filename = action_info['filename']
            action_data = action_info['data']

            if self._validate_action(action_data):
                valid_actions.append(action_info)
            else:
                self.logger.error(f"Invalid action structure in {filename}")

        return valid_actions

    def _validate_action(self, action_data: Dict[str, Any]) -> bool:
        """
        Validate action data structure.

        Args:
            action_data: Action configuration data

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['identifier', 'title', 'trigger']

        for field in required_fields:
            if field not in action_data:
                self.logger.error(f"Missing required field: {field}")
                return False

        trigger = action_data.get('trigger', {})
        if not isinstance(trigger, dict):
            self.logger.error("Trigger must be a dictionary")
            return False

        if 'operation' not in trigger:
            self.logger.error("Trigger must have 'operation' field")
            return False

        if 'type' not in trigger:
            self.logger.error("Trigger must have 'type' field")
            return False

        if 'blueprintIdentifier' not in trigger:
            self.logger.error("Trigger must have 'blueprintIdentifier' field")
            return False

        return True

    def action_exists(self, identifier: str) -> bool:
        """
        Check if an action exists.

        Args:
            identifier: Action identifier

        Returns:
            True if action exists, False otherwise
        """
        response = self.make_api_request('GET', f'/v1/actions/{identifier}', silent_404=True)
        exists = response is not None

        if exists:
            self.logger.info(f"Action '{identifier}' found in portal")
        else:
            self.logger.info(f"Action '{identifier}' not found in portal - will create it")

        return exists

    def create_action(self, action_data: Dict[str, Any]) -> bool:
        """
        Create an action in Port.io.

        Args:
            action_data: Action configuration data

        Returns:
            True if successful, False otherwise
        """
        identifier = action_data.get('identifier')
        if not identifier:
            self.logger.error("Action identifier is required")
            return False

        # Apply variable substitution before creating the action
        self.logger.info(f"Applying variable substitution for action: {identifier}")
        substituted_data = self._substitute_variables(action_data)

        self.logger.info(f"Creating action: {identifier}")
        response = self.make_api_request('POST', '/v1/actions', substituted_data)

        if response:
            return True
        else:
            self.logger.error(f"Failed to create action: {identifier}")
            return False

    def update_action(self, action_data: Dict[str, Any]) -> bool:
        """
        Update an existing action in Port.io.

        Args:
            action_data: Action configuration data

        Returns:
            True if successful, False otherwise
        """
        identifier = action_data.get('identifier')
        if not identifier:
            self.logger.error("Action identifier is required")
            return False

        # Apply variable substitution before updating the action
        self.logger.info(f"Applying variable substitution for action: {identifier}")
        substituted_data = self._substitute_variables(action_data)

        self.logger.info(f"Updating action: {identifier}")
        response = self.make_api_request('PUT', f'/v1/actions/{identifier}', substituted_data)

        if response:
            return True
        else:
            self.logger.error(f"Failed to update action: {identifier}")
            return False

    def merge_extra_action_config(self, identifier: str, extra_data: Dict[str, Any]) -> bool:
        """
        Merge extra configuration into an existing action.
        This method fetches the current action and merges the extra data.

        Args:
            identifier: Action identifier
            extra_data: Extra configuration data to merge

        Returns:
            True if successful, False otherwise
        """
        current_action = self.make_api_request('GET', f'/v1/actions/{identifier}')
        if not current_action:
            self.logger.error(f"Failed to fetch current action: {identifier}")
            return False

        merged_action = self._deep_merge(current_action, extra_data)

        self.logger.info(f"Merging extra configuration into action: {identifier}")
        response = self.make_api_request('PATCH', f'/v1/actions/{identifier}', merged_action)

        if response:
            return True
        else:
            self.logger.error(f"Failed to merge extra configuration into action: {identifier}")
            return False

    def _deep_merge(self, base_dict: Dict[str, Any], extra_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with extra_dict values taking precedence.

        Args:
            base_dict: Base dictionary
            extra_dict: Dictionary to merge in

        Returns:
            Merged dictionary
        """
        result = base_dict.copy()

        for key, value in extra_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def delete_action(self, identifier: str) -> bool:
        """
        Delete an action from Port.io.

        Args:
            identifier: Action identifier

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting action: {identifier}")
        response = self.make_api_request('DELETE', f'/v1/actions/{identifier}')

        if response:
            return True
        else:
            self.logger.error(f"Failed to delete action: {identifier}")
            return False

    def handle_action_with_strategy(self, action_data: Dict[str, Any], filename: str = "") -> bool:
        """
        Handle action creation/update based on configured strategy.
        Special handling for .extra.json files - always merge regardless of strategy.

        Args:
            action_data: Action configuration data
            filename: Name of the file being processed (to detect .extra.json)

        Returns:
            True if successful, False otherwise
        """
        identifier = action_data.get('identifier')
        if not identifier:
            self.logger.error("Action identifier is required")
            return False

        if filename.endswith('.extra.json'):
            self.logger.info(f"Processing .extra.json file for action: {identifier}")
            if self.action_exists(identifier):
                return self.merge_extra_action_config(identifier, action_data)
            else:
                self.logger.error(f"Cannot merge .extra.json: Action '{identifier}' does not exist")
                return False

        strategy = self.get_strategy('actions')
        exists = self.action_exists(identifier)

        if strategy == 'merge':
            if exists:
                self.logger.info(f"Proceeding to update action '{identifier}'...")
                return self.update_action(action_data)
            else:
                self.logger.info(f"Proceeding to create action '{identifier}'...")
                return self.create_action(action_data)
        else:
            if exists:
                self.logger.info(f"Proceeding to update action '{identifier}'...")
                return self.update_action(action_data)
            else:
                self.logger.info(f"Proceeding to create action '{identifier}'...")
                return self.create_action(action_data)

    def setup_all_actions(self, actions_dir: str) -> Dict[str, bool]:
        """
        Setup all actions from the specified directory.

        Args:
            actions_dir: Path to the actions directory

        Returns:
            Dictionary mapping action identifiers to success status
        """
        results = {}

        actions = self.discover_actions(actions_dir)

        if not actions:
            self.logger.warning("No valid actions found to setup")
            return results

        self.logger.info(f"Setting up {len(actions)} actions...")

        for action_info in actions:
            action_data = action_info['data']
            identifier = action_data['identifier']
            filename = action_info['filename']

            success = self.handle_action_with_strategy(action_data, filename)
            results[identifier] = success

            if not success:
                self.logger.error(f"Failed to process action: {identifier}")

                # Check if we should continue on error
                if not self.should_continue_on_error():
                    self.logger.error("Stopping due to error and continue_on_error is false")
                    break

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        return results
