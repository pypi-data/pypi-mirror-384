from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os

from port_experience.managers import BasePortManager


class PriorityLevel(Enum):
    """Priority levels for blueprint properties."""
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


@dataclass
class BlueprintNode:
    """Simple blueprint node with properties and dependencies."""
    identifier: str
    properties: Dict[str, Any]
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class BlueprintTreeManager(BasePortManager):
    """Simplified blueprint manager with priority-based creation."""

    PROPERTY_PRIORITY_MAP = {
        'identifier': PriorityLevel.LEVEL_1,
        'description': PriorityLevel.LEVEL_1,
        'title': PriorityLevel.LEVEL_1,
        'icon': PriorityLevel.LEVEL_1,
        'schema': PriorityLevel.LEVEL_1,

        'mirrorProperties': PriorityLevel.LEVEL_2,
        'relations': PriorityLevel.LEVEL_2,

        'calculationProperties': PriorityLevel.LEVEL_3,
        'aggregationProperties': PriorityLevel.LEVEL_3,
        'ownership': PriorityLevel.LEVEL_3,
    }

    def __init__(self, client_id: str, client_secret: str, port_host: str = "api.port.io"):
        """Initialize the Blueprint Tree Manager."""
        super().__init__(client_id, client_secret, port_host, "BlueprintTreeManager")
        self.blueprint_nodes: Dict[str, BlueprintNode] = {}
        self.created_blueprints: set = set()
        self.creating_stack: set = set()  # Track blueprints currently being created to detect cycles

    def setup_all_blueprints(self, blueprints_dir: str) -> Dict[str, bool]:
        """
        Setup all blueprints using phased priority-based approach.
        Phase 1: Create all blueprints with Level 1 properties
        Phase 2: Add Level 2 properties to all blueprints
        Phase 3: Add Level 3 properties to all blueprints

        Args:
            blueprints_dir: Path to the blueprints directory

        Returns:
            Dictionary mapping blueprint identifiers to success status
        """
        results = {}

        self._load_blueprints(blueprints_dir)

        if not self.blueprint_nodes:
            self.logger.warning("No blueprints found to setup")
            return results

        self.logger.info(f"Setting up {len(self.blueprint_nodes)} blueprints in phases...")

        # Phase 1: Create all blueprints with Level 1 properties only
        self.logger.info("Phase 1: Creating all blueprints with core properties...")
        for identifier in self.blueprint_nodes:
            if identifier not in self.created_blueprints:
                success = self._create_blueprint_core_only(identifier)
                results[identifier] = success

                if not success:
                    self.logger.error(f"Failed to create blueprint core: {identifier}")
                    if not self.should_continue_on_error():
                        return results

        # Phase 2: Add Level 2 properties (relations) to all blueprints
        self.logger.info("Phase 2: Adding Level 2 properties (relations) to all blueprints...")
        for identifier in self.blueprint_nodes:
            success = self._add_level_2_properties(identifier)
            if not success:
                self.logger.error(f"Failed to add Level 2 properties to: {identifier}")
                results[identifier] = False
                if not self.should_continue_on_error():
                    return results

        # Phase 3a: Add calculation properties to all blueprints first
        self.logger.info("Phase 3a: Adding calculation properties to all blueprints...")
        for identifier in self.blueprint_nodes:
            success = self._add_calculation_properties(identifier)
            if not success:
                self.logger.error(f"Failed to add calculation properties to: {identifier}")
                results[identifier] = False
                if not self.should_continue_on_error():
                    return results

        # Phase 3b: Add aggregation properties to all blueprints
        self.logger.info("Phase 3b: Adding aggregation properties to all blueprints...")
        for identifier in self.blueprint_nodes:
            success = self._add_aggregation_properties(identifier)
            if not success:
                self.logger.error(f"Failed to add aggregation properties to: {identifier}")
                results[identifier] = False
                if not self.should_continue_on_error():
                    return results

        # Phase 3c: Add ownership properties to all blueprints
        self.logger.info("Phase 3c: Adding ownership properties to all blueprints...")
        for identifier in self.blueprint_nodes:
            success = self._add_ownership_properties(identifier)
            if not success:
                self.logger.error(f"Failed to add ownership properties to: {identifier}")
                results[identifier] = False
                if not self.should_continue_on_error():
                    return results

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        self.logger.info(f"Blueprint setup completed: {successful}/{total} successful")

        return results

    def _load_blueprints(self, blueprints_dir: str) -> None:
        """Load all blueprint files and analyze dependencies."""
        self.logger.info("Loading blueprints...")

        if not os.path.exists(blueprints_dir):
            self.logger.error(f"Blueprints directory does not exist: {blueprints_dir}")
            return

        for filename in os.listdir(blueprints_dir):
            # Load .json files but skip .extra.json files
            if filename.endswith('.json') and not filename.endswith('.extra.json'):
                filepath = os.path.join(blueprints_dir, filename)
                blueprint_data = self._load_blueprint_file(filepath)

                if blueprint_data:
                    identifier = blueprint_data['identifier']

                    self.blueprint_nodes[identifier] = BlueprintNode(
                        identifier=identifier,
                        properties=blueprint_data,
                        dependencies=[]
                    )

                    self.logger.info(f"Loaded blueprint: {identifier}")

        self.logger.info(f"Loaded {len(self.blueprint_nodes)} blueprints: {list(self.blueprint_nodes.keys())}")
        # Second pass: Extract dependencies now that all blueprints are loaded
        for identifier, node in self.blueprint_nodes.items():
            dependencies = self._extract_dependencies(node.properties)
            node.dependencies = dependencies
            self.logger.info(f"Blueprint {identifier} dependencies: {dependencies}")

    def _load_blueprint_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load and validate a blueprint file."""
        try:
            with open(filepath, 'r') as f:
                blueprint_data = json.load(f)

            if 'identifier' not in blueprint_data:
                self.logger.error(f"Missing identifier in {filepath}")
                return None

            return blueprint_data

        except Exception as e:
            self.logger.error(f"Error loading blueprint file {filepath}: {str(e)}")
            return None

    def _extract_dependencies(self, blueprint_data: Dict[str, Any]) -> List[str]:
        """
        Extract hard dependencies from blueprint data.
        Only relations are considered hard dependencies.
        Aggregation properties are soft dependencies handled later.
        """
        dependencies = set()
        identifier = blueprint_data['identifier']

        # Only relations are hard dependencies that must exist before creation
        relations = blueprint_data.get('relations', {})
        for relation_config in relations.values():
            target = relation_config.get('target')
            # Skip self-references and non-existent blueprints
            if target and target != identifier and target in self.blueprint_nodes:
                dependencies.add(target)

        # Aggregation properties are NOT included as dependencies
        # They can be added after both blueprints exist

        return list(dependencies)

    def _create_blueprint_recursive(self, identifier: str) -> bool:
        """
        Create a blueprint, creating its dependencies first if needed.
        Detects and handles circular dependencies.

        Args:
            identifier: Blueprint identifier to create

        Returns:
            True if successful, False otherwise
        """
        # Already created
        if identifier in self.created_blueprints:
            self.logger.info(f"Blueprint {identifier} already created, skipping")
            return True

        # Circular dependency detected
        if identifier in self.creating_stack:
            self.logger.warning(f"Circular dependency detected for {identifier}, will handle with priority levels")
            return True  # Return True to continue, will be created later

        if identifier not in self.blueprint_nodes:
            self.logger.error(f"Blueprint {identifier} not found")
            return False

        # Add to stack to detect cycles
        self.creating_stack.add(identifier)

        try:
            blueprint_node = self.blueprint_nodes[identifier]

            # Create dependencies first
            for dependency in blueprint_node.dependencies:
                if dependency not in self.created_blueprints:
                    self.logger.info(f"Creating dependency {dependency} for {identifier}")
                    if not self._create_blueprint_recursive(dependency):
                        self.logger.error(f"Failed to create dependency {dependency} for {identifier}")
                        return False

            # Create the blueprint itself
            success = self._create_blueprint_with_priority(identifier)
            return success

        finally:
            # Remove from stack when done
            self.creating_stack.discard(identifier)

    def _create_blueprint_with_priority(self, identifier: str) -> bool:
        """
        Create a blueprint using priority levels.

        Args:
            identifier: Blueprint identifier

        Returns:
            True if successful, False otherwise
        """
        blueprint_node = self.blueprint_nodes[identifier]
        blueprint_data = blueprint_node.properties

        # Check if blueprint already exists
        if self.blueprint_exists(identifier):
            self.logger.info(f"Updating existing blueprint '{identifier}' with all properties...")
            return self._update_blueprint_with_priority(identifier, blueprint_data)
        else:
            self.logger.info(f"Creating new blueprint '{identifier}' with priority levels...")
            return self._create_new_blueprint_with_priority(identifier, blueprint_data)

    def _create_new_blueprint_with_priority(self, identifier: str, blueprint_data: Dict[str, Any]) -> bool:
        """Create a new blueprint with priority levels."""
        # Level 1: Core properties
        level_1_props = self._get_properties_by_level(blueprint_data, PriorityLevel.LEVEL_1)

        # Create blueprint with Level 1 properties
        success = self._create_blueprint_core(level_1_props)
        if not success:
            return False

        # Level 2: Relations
        level_2_props = self._get_properties_by_level(blueprint_data, PriorityLevel.LEVEL_2)
        if level_2_props:
            self.logger.info(f"Adding Level 2 properties to {identifier}")
            success = self._update_blueprint_properties(identifier, level_2_props)
            if not success:
                return False

        # Level 3: Computed properties
        level_3_props = self._get_properties_by_level(blueprint_data, PriorityLevel.LEVEL_3)
        if level_3_props:
            self.logger.info(f"Adding Level 3 properties to {identifier}")
            success = self._update_blueprint_properties(identifier, level_3_props)
            if not success:
                return False

        self.created_blueprints.add(identifier)
        self.logger.info(f"Successfully created blueprint {identifier}")
        return True

    def _update_blueprint_with_priority(self, identifier: str, blueprint_data: Dict[str, Any]) -> bool:
        """Update existing blueprint with all properties."""
        # Get current blueprint
        current_blueprint = self.make_api_request('GET', f'/v1/blueprints/{identifier}')
        if not current_blueprint:
            self.logger.error(f"Failed to fetch current blueprint: {identifier}")
            return False

        # Merge all properties
        merged_blueprint = self._deep_merge(current_blueprint, blueprint_data)

        # Update blueprint
        response = self.make_api_request('PATCH', f'/v1/blueprints/{identifier}', merged_blueprint)

        if response:
            self.created_blueprints.add(identifier)
            self.logger.info(f"Successfully updated blueprint {identifier}")
            return True
        else:
            self.logger.error(f"Failed to update blueprint {identifier}")
            return False

    def _get_properties_by_level(self, blueprint_data: Dict[str, Any], level: PriorityLevel) -> Dict[str, Any]:
        """Get properties for a specific priority level."""
        properties = {}

        for prop_name, prop_value in blueprint_data.items():
            if self.PROPERTY_PRIORITY_MAP.get(prop_name) == level:
                properties[prop_name] = prop_value

        return properties

    def _create_blueprint_core(self, blueprint_data: Dict[str, Any]) -> bool:
        """Create the core blueprint."""
        identifier = blueprint_data.get('identifier')
        if not identifier:
            self.logger.error("Blueprint identifier is required")
            return False

        self.logger.info(f"Creating blueprint core: {identifier}")
        response = self.make_api_request('POST', '/v1/blueprints', blueprint_data)

        if response:
            return True
        else:
            self.logger.error(f"Failed to create blueprint core: {identifier}")
            return False

    def _update_blueprint_properties(self, identifier: str, properties: Dict[str, Any]) -> bool:
        """Update blueprint with additional properties."""
        self.logger.info(f"Updating blueprint properties: {identifier}")
        response = self.make_api_request('PATCH', f'/v1/blueprints/{identifier}', properties)

        if response:
            return True
        else:
            self.logger.error(f"Failed to update blueprint properties: {identifier}")
            return False

    def blueprint_exists(self, identifier: str) -> bool:
        """Check if a blueprint exists."""
        response = self.make_api_request('GET', f'/v1/blueprints/{identifier}', silent_404=True)
        exists = response is not None

        if exists:
            self.logger.info(f"Blueprint '{identifier}' found in portal")
        else:
            self.logger.info(f"Blueprint '{identifier}' not found in portal - will create it")

        return exists

    def _deep_merge(self, base_dict: Dict[str, Any], extra_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base_dict.copy()

        for key, value in extra_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _create_blueprint_core_only(self, identifier: str) -> bool:
        """
        Create a blueprint with Level 1 properties only.

        Args:
            identifier: Blueprint identifier

        Returns:
            True if successful, False otherwise
        """
        if identifier not in self.blueprint_nodes:
            self.logger.error(f"Blueprint {identifier} not found")
            return False

        blueprint_node = self.blueprint_nodes[identifier]
        blueprint_data = blueprint_node.properties

        # Check if blueprint already exists
        if self.blueprint_exists(identifier):
            self.logger.info(f"Blueprint '{identifier}' already exists, will be updated in later phases")
            self.created_blueprints.add(identifier)
            return True

        # Get Level 1 properties only
        level_1_props = self._get_properties_by_level(blueprint_data, PriorityLevel.LEVEL_1)

        # Create blueprint with Level 1 properties
        self.logger.info(f"Creating blueprint core: {identifier}")
        success = self._create_blueprint_core(level_1_props)

        if success:
            self.created_blueprints.add(identifier)
            self.logger.info(f"Successfully created blueprint core: {identifier}")

        return success

    def _add_level_2_properties(self, identifier: str) -> bool:
        """
        Add Level 2 properties (relations, mirror properties) to a blueprint.

        Args:
            identifier: Blueprint identifier

        Returns:
            True if successful, False otherwise
        """
        if identifier not in self.blueprint_nodes:
            self.logger.error(f"Blueprint {identifier} not found")
            return False

        blueprint_node = self.blueprint_nodes[identifier]
        blueprint_data = blueprint_node.properties

        # Get Level 2 properties
        level_2_props = self._get_properties_by_level(blueprint_data, PriorityLevel.LEVEL_2)

        if not level_2_props:
            self.logger.info(f"No Level 2 properties for {identifier}, skipping")
            return True

        self.logger.info(f"Adding Level 2 properties to {identifier}")
        return self._update_blueprint_properties(identifier, level_2_props)

    def _add_calculation_properties(self, identifier: str) -> bool:
        """
        Add calculation properties to a blueprint.

        Args:
            identifier: Blueprint identifier

        Returns:
            True if successful, False otherwise
        """
        if identifier not in self.blueprint_nodes:
            self.logger.error(f"Blueprint {identifier} not found")
            return False

        blueprint_node = self.blueprint_nodes[identifier]
        blueprint_data = blueprint_node.properties

        # Get only calculation properties
        calc_props = {}
        if 'calculationProperties' in blueprint_data:
            calc_props['calculationProperties'] = blueprint_data['calculationProperties']

        if not calc_props or not calc_props.get('calculationProperties'):
            self.logger.info(f"No calculation properties for {identifier}, skipping")
            return True

        self.logger.info(f"Adding calculation properties to {identifier}")
        return self._update_blueprint_properties(identifier, calc_props)

    def _add_aggregation_properties(self, identifier: str) -> bool:
        """
        Add aggregation properties to a blueprint.

        Args:
            identifier: Blueprint identifier

        Returns:
            True if successful, False otherwise
        """
        if identifier not in self.blueprint_nodes:
            self.logger.error(f"Blueprint {identifier} not found")
            return False

        blueprint_node = self.blueprint_nodes[identifier]
        blueprint_data = blueprint_node.properties

        # Get only aggregation properties
        agg_props = {}
        if 'aggregationProperties' in blueprint_data:
            agg_props['aggregationProperties'] = blueprint_data['aggregationProperties']

        if not agg_props or not agg_props.get('aggregationProperties'):
            self.logger.info(f"No aggregation properties for {identifier}, skipping")
            return True

        self.logger.info(f"Adding aggregation properties to {identifier}")
        return self._update_blueprint_properties(identifier, agg_props)

    def _add_ownership_properties(self, identifier: str) -> bool:
        """
        Add ownership properties to a blueprint.

        Args:
            identifier: Blueprint identifier

        Returns:
            True if successful, False otherwise
        """
        if identifier not in self.blueprint_nodes:
            self.logger.error(f"Blueprint {identifier} not found")
            return False

        blueprint_node = self.blueprint_nodes[identifier]
        blueprint_data = blueprint_node.properties

        # Get only ownership properties
        ownership_props = {}
        if 'ownership' in blueprint_data:
            ownership_props['ownership'] = blueprint_data['ownership']

        if not ownership_props or not ownership_props.get('ownership'):
            self.logger.info(f"No ownership properties for {identifier}, skipping")
            return True

        self.logger.info(f"Adding ownership properties to {identifier}")
        return self._update_blueprint_properties(identifier, ownership_props)