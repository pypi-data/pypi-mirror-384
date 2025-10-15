from typing import List, Dict, Any, Optional
from port_experience.managers import BasePortManager


class PortMappingManager(BasePortManager):
    """Manages Port.io integration mappings and configurations."""

    def __init__(self, client_id: str, client_secret: str, port_host: str = "api.port.io"):
        """Initialize the Port Mapping Manager."""
        super().__init__(client_id, client_secret, port_host, "PortMappingManager")

    def fetch_integration(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Fetch integration details by identifier.

        Args:
            identifier: Integration identifier

        Returns:
            Integration data dictionary or None if failed
        """
        self.logger.info(f"Checking integration: {identifier}")
        response = self.make_api_request('GET', f'/v1/integration/{identifier}', silent_404=True)

        if response and response.get('ok') and 'integration' in response:
            self.logger.info(f"Integration '{identifier}' found in portal")
            return response['integration']
        else:
            self.logger.info(f"Integration '{identifier}' not found in portal")
            return None

    def integration_has_resources(self, identifier: str) -> bool:
        """
        Check if integration has existing resources.

        Args:
            identifier: Integration identifier

        Returns:
            True if integration has resources, False otherwise
        """
        integration = self.fetch_integration(identifier)
        if not integration:
            return False

        existing_config = integration.get('config', {})
        existing_resources = existing_config.get('resources', [])
        return len(existing_resources) > 0

    def update_integration_config(self, identifier: str, new_resources: List[Dict[str, Any]]) -> bool:
        """
        Update integration config by merging new resources with existing ones.

        Args:
            identifier: Integration identifier
            new_resources: List of new resources to add/merge

        Returns:
            True if successful, False otherwise
        """
        integration = self.fetch_integration(identifier)
        if not integration:
            self.logger.error(f"Failed to fetch integration {identifier} for config update")
            return False

        existing_config = integration.get('config', {})
        existing_resources = existing_config.get('resources', [])

        merged_resources = self._merge_resources(existing_resources, new_resources)

        updated_config = existing_config.copy()
        updated_config['resources'] = merged_resources

        self.logger.info(f"Updating integration config: {identifier}")
        payload = {"config": updated_config}
        response = self.make_api_request('PATCH', f'/v1/integration/{identifier}/config', payload)

        if response:
            self.logger.info(f"Successfully updated config for integration: {identifier}")
            return True
        else:
            self.logger.error(f"Failed to update config for integration: {identifier}")
            return False

    def replace_integration_config(self, identifier: str, new_resources: List[Dict[str, Any]]) -> bool:
        """
        Replace integration config resources completely.

        Args:
            identifier: Integration identifier
            new_resources: List of new resources to replace with

        Returns:
            True if successful, False otherwise
        """
        integration = self.fetch_integration(identifier)
        if not integration:
            self.logger.error(f"Failed to fetch integration {identifier} for config update")
            return False

        existing_config = integration.get('config', {})

        # Replace resources completely
        updated_config = existing_config.copy()
        updated_config['resources'] = new_resources

        self.logger.info(f"Replacing integration config: {identifier}")
        payload = {"config": updated_config}
        response = self.make_api_request('PATCH', f'/v1/integration/{identifier}/config', payload)

        if response:
            self.logger.info(f"Successfully replaced config for integration: {identifier}")
            return True
        else:
            self.logger.error(f"Failed to replace config for integration: {identifier}")
            return False

    def append_integration_config(self, identifier: str, new_resources: List[Dict[str, Any]]) -> bool:
        """
        Append new resources to existing integration config.

        Args:
            identifier: Integration identifier
            new_resources: List of new resources to append

        Returns:
            True if successful, False otherwise
        """
        integration = self.fetch_integration(identifier)
        if not integration:
            self.logger.error(f"Failed to fetch integration {identifier} for config update")
            return False

        existing_config = integration.get('config', {})
        existing_resources = existing_config.get('resources', [])

        # Simply append new resources
        appended_resources = existing_resources + new_resources

        updated_config = existing_config.copy()
        updated_config['resources'] = appended_resources

        self.logger.info(f"Appending to integration config: {identifier}")
        payload = {"config": updated_config}
        response = self.make_api_request('PATCH', f'/v1/integration/{identifier}/config', payload)

        if response:
            self.logger.info(f"Successfully appended config for integration: {identifier}")
            return True
        else:
            self.logger.error(f"Failed to append config for integration: {identifier}")
            return False

    def handle_mapping_with_strategy(self, identifier: str, new_resources: List[Dict[str, Any]]) -> bool:
        """
        Handle mapping application based on configured strategy.

        Args:
            identifier: Integration identifier
            new_resources: List of new resources to apply

        Returns:
            True if successful, False otherwise
        """
        strategy = self.get_strategy('mappings')
        has_resources = self.integration_has_resources(identifier)

        self.logger.info(
            f"Processing mapping for '{identifier}' with strategy '{strategy}' (has_resources: {has_resources})")

        if strategy == 'merge':
            return self.update_integration_config(identifier, new_resources)

        elif strategy == 'replace':
            return self.replace_integration_config(identifier, new_resources)

        elif strategy == 'error':
            if has_resources:
                self.logger.error(f"Integration '{identifier}' already has resources and strategy is 'error'")
                return False
            else:
                return self.update_integration_config(identifier, new_resources)

        elif strategy == 'append':
            return self.append_integration_config(identifier, new_resources)

        else:
            self.logger.error(f"Unknown strategy: {strategy}")
            return False

    def _merge_resources(self, existing_resources: List[Dict[str, Any]],
                         new_resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge new resources with existing ones, updating by kind.

        Args:
            existing_resources: List of existing resources
            new_resources: List of new resources to merge

        Returns:
            List of merged resources
        """
        existing_resources_map = {}
        for resource in existing_resources:
            kind = resource.get('kind')
            if kind:
                existing_resources_map[kind] = resource

        merged_resources = existing_resources.copy()
        for new_resource in new_resources:
            kind = new_resource.get('kind')
            if kind in existing_resources_map:
                self.logger.info(f"Updating existing resource kind: {kind}")
                for i, existing_resource in enumerate(merged_resources):
                    if existing_resource.get('kind') == kind:
                        merged_resources[i] = new_resource
                        break
            else:
                self.logger.info(f"Adding new resource kind: {kind}")
                merged_resources.append(new_resource)

        return merged_resources

    def discover_mappings(self, mappings_dir: str) -> List[Dict[str, Any]]:
        """
        Discover all mapping JSON files in the specified directory.

        Args:
            mappings_dir: Path to the mappings directory

        Returns:
            List of mapping configurations loaded from JSON files
        """
        mappings = self.discover_json_files(mappings_dir, "mappings")

        valid_mappings = []
        for mapping_info in mappings:
            if self._validate_mapping(mapping_info['data']):
                valid_mappings.append(mapping_info)
            else:
                self.logger.error(f"Invalid mapping structure in {mapping_info['filename']}")

        return valid_mappings

    def _validate_mapping(self, mapping_data: Dict[str, Any]) -> bool:
        """
        Validate mapping data structure.

        Args:
            mapping_data: Mapping configuration data

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['integration', 'resources']

        for field in required_fields:
            if field not in mapping_data:
                self.logger.error(f"Missing required field: {field}")
                return False

        resources = mapping_data.get('resources', [])
        if not isinstance(resources, list):
            self.logger.error("Resources must be a list")
            return False

        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                self.logger.error(f"Resource {i} must be a dictionary")
                return False

            required_resource_fields = ['kind', 'selector', 'port']
            for field in required_resource_fields:
                if field not in resource:
                    self.logger.error(f"Resource {i} missing required field: {field}")
                    return False

        return True

    def apply_mappings(self, mappings_dir: str) -> Dict[str, bool]:
        """
        Apply all mappings from the specified directory to their integrations.

        Args:
            mappings_dir: Path to the mappings directory

        Returns:
            Dictionary mapping integration identifiers to success status
        """
        results = {}

        mappings = self.discover_mappings(mappings_dir)

        if not mappings:
            self.logger.warning("No valid mappings found to apply")
            return results

        self.logger.info(f"Applying {len(mappings)} mappings...")

        for mapping_info in mappings:
            mapping_data = mapping_info['data']
            integration_identifier = mapping_data['integration']
            resources = mapping_data['resources']
            filename = mapping_info['filename']

            self.logger.info(f"Processing mapping: {filename} for integration: {integration_identifier}")

            success = self.handle_mapping_with_strategy(integration_identifier, resources)
            results[integration_identifier] = success

            if success:
                self.logger.info(f"Successfully applied mapping for integration: {integration_identifier}")
            else:
                self.logger.error(f"Failed to apply mapping for integration: {integration_identifier}")

                # Check if we should continue on error
                if not self.should_continue_on_error():
                    self.logger.error("Stopping due to error and continue_on_error is false")
                    break

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        self.logger.info(f"Mapping application complete: {successful}/{total} mappings applied successfully")

        return results
