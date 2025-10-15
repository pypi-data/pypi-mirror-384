from typing import List, Dict, Any

from port_experience.managers import BasePortManager
from port_experience.managers.blueprint_tree_manager import BlueprintTreeManager


class PortBlueprintManager(BasePortManager):
    """Manages Port.io blueprints creation and configuration."""

    def __init__(self, client_id: str, client_secret: str, port_host: str = "api.port.io",
                 use_tree_approach: bool = True):
        """Initialize the Port Blueprint Manager."""
        super().__init__(client_id, client_secret, port_host, "PortBlueprintManager")
        self.use_tree_approach = use_tree_approach
        if use_tree_approach:
            self.tree_manager = BlueprintTreeManager(client_id, client_secret, port_host)

    def discover_blueprints(self, blueprints_dir: str) -> List[Dict[str, Any]]:
        """
        Discover all blueprint JSON files in the specified directory.

        Args:
            blueprints_dir: Path to the blueprints directory

        Returns:
            List of blueprint configurations loaded from JSON files
        """
        blueprints = self.discover_json_files(blueprints_dir, "blueprints")

        valid_blueprints = []
        for blueprint_info in blueprints:
            filename = blueprint_info['filename']
            blueprint_data = blueprint_info['data']

            if self._validate_blueprint(blueprint_data):
                valid_blueprints.append(blueprint_info)
            else:
                self.logger.error(f"Invalid blueprint structure in {filename}")

        return valid_blueprints

    def _validate_blueprint(self, blueprint_data: Dict[str, Any]) -> bool:
        """
        Validate blueprint data structure.

        Args:
            blueprint_data: Blueprint configuration data

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['identifier', 'title', 'schema']

        for field in required_fields:
            if field not in blueprint_data:
                self.logger.error(f"Missing required field: {field}")
                return False

        schema = blueprint_data.get('schema', {})
        if not isinstance(schema, dict):
            self.logger.error("Schema must be a dictionary")
            return False

        return True

    def blueprint_exists(self, identifier: str) -> bool:
        """
        Check if a blueprint exists.

        Args:
            identifier: Blueprint identifier

        Returns:
            True if blueprint exists, False otherwise
        """
        response = self.make_api_request('GET', f'/v1/blueprints/{identifier}', silent_404=True)
        exists = response is not None

        if exists:
            self.logger.info(f"Blueprint '{identifier}' found in portal")
        else:
            self.logger.info(f"Blueprint '{identifier}' not found in portal - will create it")

        return exists

    def create_blueprint(self, blueprint_data: Dict[str, Any]) -> bool:
        """
        Create a blueprint in Port.io.

        Args:
            blueprint_data: Blueprint configuration data

        Returns:
            True if successful, False otherwise
        """
        identifier = blueprint_data.get('identifier')
        if not identifier:
            self.logger.error("Blueprint identifier is required")
            return False

        self.logger.info(f"Creating blueprint: {identifier}")
        response = self.make_api_request('POST', '/v1/blueprints', blueprint_data)

        if response:
            return True
        else:
            self.logger.error(f"Failed to create blueprint: {identifier}")
            return False

    def update_blueprint(self, blueprint_data: Dict[str, Any]) -> bool:
        """
        Update an existing blueprint in Port.io.

        Args:
            blueprint_data: Blueprint configuration data

        Returns:
            True if successful, False otherwise
        """
        identifier = blueprint_data.get('identifier')
        if not identifier:
            self.logger.error("Blueprint identifier is required")
            return False

        self.logger.info(f"Updating blueprint: {identifier}")
        response = self.make_api_request('PATCH', f'/v1/blueprints/{identifier}', blueprint_data)

        if response:
            return True
        else:
            self.logger.error(f"Failed to update blueprint: {identifier}")
            return False

    def merge_extra_blueprint_config(self, identifier: str, extra_data: Dict[str, Any]) -> bool:
        """
        Merge extra configuration into an existing blueprint.
        This method fetches the current blueprint and merges the extra data.

        Args:
            identifier: Blueprint identifier
            extra_data: Extra configuration data to merge

        Returns:
            True if successful, False otherwise
        """
        current_blueprint = self.make_api_request('GET', f'/v1/blueprints/{identifier}')
        if not current_blueprint:
            self.logger.error(f"Failed to fetch current blueprint: {identifier}")
            return False

        merged_blueprint = self._deep_merge(current_blueprint, extra_data)

        self.logger.info(f"Merging extra configuration into blueprint: {identifier}")
        response = self.make_api_request('PATCH', f'/v1/blueprints/{identifier}', merged_blueprint)

        if response:
            return True
        else:
            self.logger.error(f"Failed to merge extra configuration into blueprint: {identifier}")
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

    def delete_blueprint(self, identifier: str) -> bool:
        """
        Delete a blueprint from Port.io.

        Args:
            identifier: Blueprint identifier

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting blueprint: {identifier}")
        response = self.make_api_request('DELETE', f'/v1/blueprints/{identifier}')

        if response:
            return True
        else:
            self.logger.error(f"Failed to delete blueprint: {identifier}")
            return False

    def handle_blueprint_with_strategy(self, blueprint_data: Dict[str, Any], filename: str = "") -> bool:
        """
        Handle blueprint creation/update based on configured strategy.
        Special handling for .extra.json files - always merge regardless of strategy.

        Args:
            blueprint_data: Blueprint configuration data
            filename: Name of the file being processed (to detect .extra.json)

        Returns:
            True if successful, False otherwise
        """
        identifier = blueprint_data.get('identifier')
        if not identifier:
            self.logger.error("Blueprint identifier is required")
            return False

        if filename.endswith('.extra.json'):
            self.logger.info(f"Processing .extra.json file for blueprint: {identifier}")
            if self.blueprint_exists(identifier):
                return self.merge_extra_blueprint_config(identifier, blueprint_data)
            else:
                self.logger.error(f"Cannot merge .extra.json: Blueprint '{identifier}' does not exist")
                return False

        strategy = self.get_strategy('blueprints')
        exists = self.blueprint_exists(identifier)

        if strategy == 'merge':
            if exists:
                self.logger.info(f"Proceeding to update blueprint '{identifier}'...")
                return self.update_blueprint(blueprint_data)
            else:
                self.logger.info(f"Proceeding to create blueprint '{identifier}'...")
                return self.create_blueprint(blueprint_data)
        else:
            if exists:
                self.logger.info(f"Proceeding to update blueprint '{identifier}'...")
                return self.update_blueprint(blueprint_data)
            else:
                self.logger.info(f"Proceeding to create blueprint '{identifier}'...")
                return self.create_blueprint(blueprint_data)

    def setup_all_blueprints(self, blueprints_dir: str) -> Dict[str, bool]:
        """
        Setup all blueprints from the specified directory.
        Uses simplified tree approach if enabled, otherwise falls back to original method.

        Args:
            blueprints_dir: Path to the blueprints directory

        Returns:
            Dictionary mapping blueprint identifiers to success status
        """
        if self.use_tree_approach:
            self.logger.info("Using simplified priority tree approach for blueprint setup")
            return self.tree_manager.setup_all_blueprints(blueprints_dir)
        else:
            self.logger.info("Using traditional approach for blueprint setup")
            return self._setup_blueprints_traditional(blueprints_dir)

    def _setup_blueprints_traditional(self, blueprints_dir: str) -> Dict[str, bool]:
        """
        Traditional blueprint setup method (original implementation).

        Args:
            blueprints_dir: Path to the blueprints directory

        Returns:
            Dictionary mapping blueprint identifiers to success status
        """
        results = {}

        blueprints = self.discover_blueprints(blueprints_dir)

        if not blueprints:
            self.logger.warning("No valid blueprints found to setup")
            return results

        self.logger.info(f"Setting up {len(blueprints)} blueprints...")

        for blueprint_info in blueprints:
            blueprint_data = blueprint_info['data']
            identifier = blueprint_data['identifier']
            filename = blueprint_info['filename']

            success = self.handle_blueprint_with_strategy(blueprint_data, filename)
            results[identifier] = success

            if not success:
                self.logger.error(f"Failed to process blueprint: {identifier}")

                if not self.should_continue_on_error():
                    self.logger.error("Stopping due to error and continue_on_error is false")
                    break

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        return results

    def enable_tree_approach(self) -> None:
        """Enable the tree approach for blueprint management."""
        self.use_tree_approach = True
        if not hasattr(self, 'tree_manager'):
            self.tree_manager = BlueprintTreeManager(
                self.client_id,
                self.client_secret,
                self.port_host
            )
        self.logger.info("Tree approach enabled")

    def disable_tree_approach(self) -> None:
        """Disable the tree approach and use traditional method."""
        self.use_tree_approach = False
        self.logger.info("Tree approach disabled, using traditional method")
