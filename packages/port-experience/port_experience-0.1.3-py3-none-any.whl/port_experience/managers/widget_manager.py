from typing import List, Dict, Any, Optional

from port_experience.managers import BasePortManager


class PortWidgetManager(BasePortManager):
    """Manages Port.io widgets creation and configuration."""

    def __init__(self, client_id: str, client_secret: str, port_host: str = "api.port.io"):
        """Initialize the Port Widget Manager."""
        super().__init__(client_id, client_secret, port_host, "PortWidgetManager")

    def discover_widgets(self, widgets_dir: str) -> List[Dict[str, Any]]:
        """
        Discover all widget JSON files in the specified directory.

        Args:
            widgets_dir: Path to the widgets directory

        Returns:
            List of widget configurations loaded from JSON files
        """
        widgets = self.discover_json_files(widgets_dir, "widgets")

        valid_widgets = []
        for widget_info in widgets:
            filename = widget_info['filename']
            widget_data = widget_info['data']

            if self._validate_widget(widget_data):
                valid_widgets.append(widget_info)
            else:
                self.logger.error(f"Invalid widget structure in {filename}")

        return valid_widgets

    def _validate_widget(self, widget_data: Dict[str, Any]) -> bool:
        """
        Validate widget data structure.

        Args:
            widget_data: Widget configuration data

        Returns:
            True if valid, False otherwise
        """
        # Widget data can be in different formats:
        # 1. Page with widgets: {'identifier': '...', 'title': '...', 'type': '...', 'widgets': [...]}
        # 2. Page with single widget: {'page': '...', 'widget': {...}}
        # 3. Standalone widget: {'title': '...', 'type': '...', ...}

        if 'identifier' in widget_data and 'widgets' in widget_data:
            # Format 1: Page with widgets array
            required_fields = ['identifier', 'title', 'type', 'widgets']
            for field in required_fields:
                if field not in widget_data:
                    self.logger.error(f"Missing required field: {field}")
                    return False

            # Validate widgets array
            widgets = widget_data.get('widgets', [])
            if not isinstance(widgets, list):
                self.logger.error("Widgets must be a list")
                return False

            for widget in widgets:
                if not isinstance(widget, dict):
                    self.logger.error("Each widget must be a dictionary")
                    return False

                # For dashboard-widget, check for required fields including layout
                if widget.get('type') == 'dashboard-widget':
                    dashboard_required_fields = ['id', 'type', 'layout', 'widgets']
                    for field in dashboard_required_fields:
                        if field not in widget:
                            self.logger.error(f"Dashboard widget missing required field: {field}")
                            return False
                else:
                    # Regular widget validation
                    if 'title' not in widget or 'type' not in widget:
                        self.logger.error("Each widget must have 'title' and 'type' fields")
                        return False

        elif 'page' in widget_data and 'widget' in widget_data:
            # Format 2: Page with single widget
            if not isinstance(widget_data.get('widget'), dict):
                self.logger.error("Widget must be a dictionary")
                return False

            widget = widget_data['widget']
            if 'title' not in widget or 'type' not in widget:
                self.logger.error("Widget must have 'title' and 'type' fields")
                return False

        else:
            # Format 3: Standalone widget
            required_fields = ['title', 'type']
            for field in required_fields:
                if field not in widget_data:
                    self.logger.error(f"Missing required field: {field}")
                    return False

        return True

    def _clean_page_data(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean page data by removing API response metadata.

        Args:
            page_data: Raw page data from API

        Returns:
            Cleaned page data suitable for API requests
        """
        # Fields to remove that are API response metadata or not allowed in requests
        metadata_fields = ['ok', 'error', 'message', 'details', 'createdAt', 'updatedAt', 'createdBy', 'updatedBy',
                           'page', 'type', 'sidebar', 'section', 'showInSidebar', 'protected', 'requiredQueryParams']

        clean_data = {}
        for key, value in page_data.items():
            if key not in metadata_fields:
                clean_data[key] = value

        return clean_data

    def page_exists(self, page_identifier: str) -> bool:
        """
        Check if a page exists.

        Args:
            page_identifier: Page identifier

        Returns:
            True if page exists, False otherwise
        """
        response = self.make_api_request('GET', f'/v1/pages/{page_identifier}', silent_404=True)
        exists = response is not None

        if exists:
            self.logger.info(f"Page '{page_identifier}' found in portal")
        else:
            self.logger.info(f"Page '{page_identifier}' not found in portal - will create it")

        return exists

    def get_page(self, page_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get page details.

        Args:
            page_identifier: Page identifier

        Returns:
            Page data or None if not found
        """
        response = self.make_api_request('GET', f'/v1/pages/{page_identifier}')
        if response and 'page' in response:
            return response['page']
        return response

    def create_page(self, page_data: Dict[str, Any]) -> bool:
        """
        Create a page in Port.io.

        Args:
            page_data: Page configuration data

        Returns:
            True if successful, False otherwise
        """
        identifier = page_data.get('identifier')
        if not identifier:
            self.logger.error("Page identifier is required")
            return False

        self.logger.info(f"Creating page: {identifier}")
        response = self.make_api_request('POST', '/v1/pages', page_data)

        if response:
            self.logger.info(f"Successfully created page: {identifier}")
            self.logger.info(f"Create response: {response}")
            return True
        else:
            self.logger.error(f"Failed to create page: {identifier}")
            return False

    def update_page(self, page_identifier: str, page_data: Dict[str, Any]) -> bool:
        """
        Update an existing page in Port.io.

        Args:
            page_identifier: Page identifier
            page_data: Page configuration data

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating page: {page_identifier}")
        response = self.make_api_request('PATCH', f'/v1/pages/{page_identifier}', page_data)

        if response:
            self.logger.info(f"Successfully updated page: {page_identifier}")
            self.logger.info(f"Update response: {response}")
            return True
        else:
            self.logger.error(f"Failed to update page: {page_identifier}")
            return False

    def get_page_widgets(self, page_identifier: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all widgets for a specific page.

        Args:
            page_identifier: Page identifier

        Returns:
            List of widgets or None if failed
        """
        # Try different possible endpoints for getting widgets
        possible_endpoints = [
            f'/v1/pages/{page_identifier}/widgets',
            f'/v1/pages/{page_identifier}',
            f'/v1/widgets?page={page_identifier}'
        ]

        for endpoint in possible_endpoints:
            response = self.make_api_request('GET', endpoint)
            if response:
                # Try to extract widgets from different possible response structures
                if 'widgets' in response:
                    return response.get('widgets', [])
                elif isinstance(response, list):
                    return response
                elif 'data' in response and isinstance(response['data'], list):
                    return response['data']

        return None

    def create_widget(self, page_identifier: str, widget_data: Dict[str, Any],
                      parent_widget_id: Optional[str] = None) -> bool:
        """
        Create a widget on a specific page.

        Args:
            page_identifier: Page identifier
            widget_data: Widget configuration data
            parent_widget_id: Optional parent widget ID for nested widgets

        Returns:
            True if successful, False otherwise
        """
        widget_id = widget_data.get('id')
        if not widget_id:
            self.logger.error("Widget ID is required")
            return False

        self.logger.info(f"Creating widget {widget_id} on page {page_identifier}")

        # Add parent widget ID if provided, or use a default if required
        if parent_widget_id:
            widget_data['parentWidgetId'] = parent_widget_id
        else:
            # Try to find a suitable parent widget or use a default
            existing_widgets = self.get_page_widgets(page_identifier)
            if existing_widgets and len(existing_widgets) > 0:
                # Use the first widget as parent
                widget_data['parentWidgetId'] = existing_widgets[0].get('id')
            else:
                # Use the page itself as parent (common pattern)
                widget_data['parentWidgetId'] = page_identifier

        # Try different possible endpoints for creating widgets
        possible_endpoints = [
            f'/v1/pages/{page_identifier}/widgets',
            f'/v1/widgets',
            f'/v1/pages/{page_identifier}'
        ]

        # Try different request formats
        request_formats = [
            {'widget': widget_data},
            widget_data,
            {'pageId': page_identifier, 'widget': widget_data}
        ]

        for endpoint in possible_endpoints:
            for request_data in request_formats:
                response = self.make_api_request('POST', endpoint, request_data)
                if response:
                    return True

        self.logger.error(f"Failed to create widget {widget_id} on page {page_identifier}")
        return False

    def update_widget(self, page_identifier: str, widget_id: str, widget_data: Dict[str, Any]) -> bool:
        """
        Update an existing widget on a page.

        Args:
            page_identifier: Page identifier
            widget_id: Widget identifier
            widget_data: Widget configuration data

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating widget {widget_id} on page {page_identifier}")

        # Wrap widget data in 'widget' property as expected by API
        request_data = {'widget': widget_data}

        response = self.make_api_request('PATCH', f'/v1/pages/{page_identifier}/widgets/{widget_id}', request_data)

        if response:
            return True
        else:
            self.logger.error(f"Failed to update widget {widget_id} on page {page_identifier}")
            return False

    def delete_widget(self, page_identifier: str, widget_id: str) -> bool:
        """
        Delete a widget from a page.

        Args:
            page_identifier: Page identifier
            widget_id: Widget identifier

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting widget {widget_id} from page {page_identifier}")
        response = self.make_api_request('DELETE', f'/v1/pages/{page_identifier}/widgets/{widget_id}')

        if response:
            return True
        else:
            self.logger.error(f"Failed to delete widget {widget_id} from page {page_identifier}")
            return False

    def find_suitable_parent_widget(self, page_identifier: str) -> Optional[str]:
        """
        Find a suitable parent widget for creating nested widgets.

        Args:
            page_identifier: Page identifier

        Returns:
            Parent widget ID or None if not found
        """
        widgets = self.get_page_widgets(page_identifier)
        if not widgets:
            return None

        # Look for dashboard or container widgets that can serve as parents
        for widget in widgets:
            widget_type = widget.get('type', '')
            if widget_type in ['dashboard', 'container', 'grid']:
                return widget.get('id')

        # If no suitable parent found, return the first widget
        if widgets:
            return widgets[0].get('id')

        return None

    def create_dashboard_widget(self, page_identifier: str, dashboard_id: str,
                                widgets: List[Dict[str, Any]], layout: List[Dict[str, Any]]) -> bool:
        """
        Create a dashboard widget with multiple child widgets.

        Args:
            page_identifier: Page identifier
            dashboard_id: Dashboard widget identifier
            widgets: List of widget configurations
            layout: Dashboard layout configuration

        Returns:
            True if successful, False otherwise
        """
        dashboard_data = {
            'id': dashboard_id,
            'title': f'Dashboard {dashboard_id}',
            'type': 'dashboard-widget',  # Changed from 'dashboard' to 'dashboard-widget'
            'layout': layout,
            'widgets': widgets
        }

        return self.create_widget(page_identifier, dashboard_data)

    def setup_dashboard_widget(self, page_data: Dict[str, Any]) -> bool:
        """
        Setup dashboard widget - create page first if needed, then add widgets.

        This method implements the proper flow:
        1. Check if page exists
        2. If not, create empty page first
        3. If yes, get existing page data
        4. Merge or update with new dashboard widget
        5. Update page with complete data

        Args:
            page_data: Page data containing widgets array with dashboard-widget

        Returns:
            True if successful, False otherwise
        """
        page_identifier = page_data.get('identifier')
        if not page_identifier:
            self.logger.error("Page identifier is required")
            return False

        self.logger.info(f"Setting up dashboard widget for page: {page_identifier}")

        # Step 1: Check if page exists
        page_exists = self.page_exists(page_identifier)

        if page_exists:
            self.logger.info(f"Getting current page data for '{page_identifier}'...")
            # Step 2: Get existing page
            existing_page = self.get_page(page_identifier)
            if not existing_page:
                self.logger.error(f"Failed to get existing page data for {page_identifier}")
                return False

            self.logger.info(f"Current page has {len(existing_page.get('widgets', []))} widgets")

        else:
            self.logger.info(f"Creating empty page '{page_identifier}' first...")
            # Step 3: Create empty page first
            empty_page_data = {
                'identifier': page_identifier,
                'title': page_data.get('title'),
                'type': page_data.get('type', 'dashboard'),
                'icon': page_data.get('icon', 'Dashboard'),
                'showInSidebar': page_data.get('showInSidebar', True),
                'section': page_data.get('section', 'software_catalog'),
                'sidebar': page_data.get('sidebar', 'catalog'),
                'protected': page_data.get('protected', False),
                'widgets': []
            }

            if not self.create_page(empty_page_data):
                self.logger.error(f"Failed to create empty page: {page_identifier}")
                return False

            self.logger.info(f"Successfully created empty page: {page_identifier}")
            # Use empty page as starting point
            existing_page = {'widgets': []}

        # Step 4: Merge widgets intelligently
        new_widgets = page_data.get('widgets', [])
        existing_widgets = existing_page.get('widgets', [])

        # Smart merge: Replace matching widgets, add new ones
        merged_widgets = self._merge_widgets(existing_widgets, new_widgets)
        existing_page['widgets'] = merged_widgets

        self.logger.info(
            f"Merged {len(existing_widgets)} existing widgets with {len(new_widgets)} new widgets → {len(merged_widgets)} total")

        # Step 5: Update page with complete data
        self.logger.info(f"Updating page {page_identifier} with dashboard widget...")

        # Clean the page data to remove any API response metadata
        clean_page_data = self._clean_page_data(existing_page)

        success = self.update_page(page_identifier, clean_page_data)

        if success:
            self.logger.info(f"Successfully updated page {page_identifier} with dashboard widget")
        else:
            self.logger.error(f"Failed to update page {page_identifier}")

        return success

    def _merge_widgets(self, existing_widgets: List[Dict[str, Any]],
                       new_widgets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Smart merge of widgets: replace matching widgets, preserve others.

        Args:
            existing_widgets: Currently existing widgets
            new_widgets: New widgets to merge in

        Returns:
            Merged list of widgets
        """
        merged = []
        new_widget_ids = {widget.get('id') for widget in new_widgets if widget.get('id')}

        # Keep existing widgets that are not being replaced
        for widget in existing_widgets:
            widget_id = widget.get('id')
            if widget_id not in new_widget_ids:
                merged.append(widget)
                self.logger.info(f"Preserving existing widget: {widget_id}")
            else:
                self.logger.info(f"Will replace existing widget: {widget_id}")

        # Add all new widgets (replacements and additions)
        for widget in new_widgets:
            widget_id = widget.get('id', 'unknown')
            merged.append(widget)
            self.logger.info(f"Adding new widget: {widget_id}")

        return merged

    def handle_widget_with_strategy(self, widget_data: Dict[str, Any], filename: str = "") -> bool:
        """
        Handle widget creation/update based on configured strategy.

        Args:
            widget_data: Widget configuration data
            filename: Name of the file being processed

        Returns:
            True if successful, False otherwise
        """
        # Check the format of widget data
        if 'identifier' in widget_data and 'widgets' in widget_data:
            # Format 1: Page with widgets array (including dashboard-widget)
            return self.setup_dashboard_widget(widget_data)
        elif 'page' in widget_data and 'widget' in widget_data:
            # Format 2: Page with single widget
            return self._handle_page_with_single_widget(widget_data)
        else:
            # Format 3: Standalone widget - we need a page identifier
            self.logger.error("Standalone widgets require a page identifier. Use handle_widget_on_page instead.")
            return False

    def _handle_page_with_widgets(self, page_data: Dict[str, Any]) -> bool:
        """
        Handle page with widgets creation/update.

        Args:
            page_data: Page configuration data with widgets

        Returns:
            True if successful, False otherwise
        """
        page_identifier = page_data.get('identifier')
        if not page_identifier:
            self.logger.error("Page identifier is required")
            return False

        # Check if page exists
        page_exists = self.page_exists(page_identifier)

        if page_exists:
            # Update existing page
            self.logger.info(f"Updating existing page '{page_identifier}'...")
            success = self.update_page(page_identifier, page_data)
        else:
            # Create new page
            self.logger.info(f"Creating new page '{page_identifier}'...")
            success = self.create_page(page_data)

        return success

    def _handle_page_with_single_widget(self, widget_data: Dict[str, Any]) -> bool:
        """
        Handle page with single widget creation/update.

        Args:
            widget_data: Widget configuration data with 'page' and 'widget' fields

        Returns:
            True if successful, False otherwise
        """
        page_identifier = widget_data.get('page')
        widget_config = widget_data.get('widget')

        if not page_identifier or not widget_config:
            self.logger.error("Page identifier and widget configuration are required")
            return False

        # Check if page exists
        page_exists = self.page_exists(page_identifier)

        if not page_exists:
            # Create a page with the widget embedded in it
            page_data = {
                'identifier': page_identifier,
                'title': page_identifier.title(),
                'type': 'dashboard',
                'widgets': [widget_config],  # Embed the widget in the page
                'showInSidebar': True,
                'section': 'software_catalog',
                'sidebar': 'catalog',
                'protected': False
            }

            self.logger.info(f"Creating new page '{page_identifier}' with embedded widget...")
            return self.create_page(page_data)
        else:
            # Page exists, we need to update it with the widget
            # Get current page data
            current_page = self.get_page(page_identifier)
            if not current_page:
                self.logger.error(f"Failed to get current page data: {page_identifier}")
                return False

            # Always add the widget to the page's widgets array (never replace)
            widgets = current_page.get('widgets', [])
            widget_id = widget_config.get('id')

            # Always add new widget (skip ID check to prevent replacement)
            widgets.append(widget_config)
            self.logger.info(f"Adding new widget {widget_id} to page {page_identifier}")

            # Update the page with the modified widgets
            current_page['widgets'] = widgets

            # Clean the page data to remove any API response metadata
            clean_page_data = self._clean_page_data(current_page)

            self.logger.info(f"Updating page with widget: {page_identifier}")
            return self.update_page(page_identifier, clean_page_data)

    def handle_widget_on_page(self, page_identifier: str, widget_data: Dict[str, Any],
                              parent_widget_id: Optional[str] = None) -> bool:
        """
        Handle widget creation/update on a specific page.

        Args:
            page_identifier: Page identifier
            widget_data: Widget configuration data
            parent_widget_id: Optional parent widget ID

        Returns:
            True if successful, False otherwise
        """
        widget_id = widget_data.get('id')
        if not widget_id:
            self.logger.error("Widget ID is required")
            return False

        # Check if page exists
        if not self.page_exists(page_identifier):
            self.logger.error(f"Page {page_identifier} does not exist")
            return False

        # Check if widget exists
        existing_widgets = self.get_page_widgets(page_identifier)
        widget_exists = False

        if existing_widgets:
            for widget in existing_widgets:
                if widget.get('id') == widget_id:
                    widget_exists = True
                    break

        if widget_exists:
            # Update existing widget
            self.logger.info(f"Updating existing widget '{widget_id}'...")
            return self.update_widget(page_identifier, widget_id, widget_data)
        else:
            # Create new widget
            self.logger.info(f"Creating new widget '{widget_id}'...")
            return self.create_widget(page_identifier, widget_data, parent_widget_id)

    def setup_all_widgets(self, widgets_dir: str) -> Dict[str, bool]:
        """
        Setup all widgets from the specified directory.
        Groups widgets by page and processes them together to avoid replacement.

        Args:
            widgets_dir: Path to the widgets directory

        Returns:
            Dictionary mapping widget/page identifiers to success status
        """
        results = {}

        widgets = self.discover_widgets(widgets_dir)

        if not widgets:
            self.logger.warning("No valid widgets found to setup")
            return results

        self.logger.info(f"Setting up {len(widgets)} widget configurations...")

        # Group widgets by page
        widgets_by_page = {}
        for widget_info in widgets:
            widget_data = widget_info['data']
            filename = widget_info['filename']

            if 'page' in widget_data and 'widget' in widget_data:
                page_id = widget_data['page']
                if page_id not in widgets_by_page:
                    widgets_by_page[page_id] = []
                widgets_by_page[page_id].append(widget_info)
            else:
                # Handle other widget formats individually
                success = self.handle_widget_with_strategy(widget_data, filename)
                identifier = self._get_widget_identifier(widget_data, filename)
                results[identifier] = success

        # Process each page with all its widgets
        for page_id, page_widgets in widgets_by_page.items():
            success = self._setup_page_widgets(page_id, page_widgets)
            for widget_info in page_widgets:
                widget_data = widget_info['data']
                widget_id = widget_data['widget'].get('id', 'unknown')
                identifier = f"{page_id}:{widget_id}"
                results[identifier] = success

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        self.logger.info(f"Widget setup completed: {successful}/{total} successful")

        return results

    def _get_widget_identifier(self, widget_data: Dict[str, Any], filename: str) -> str:
        """Get identifier for widget tracking."""
        if 'identifier' in widget_data:
            return widget_data['identifier']
        elif 'page' in widget_data and 'widget' in widget_data:
            page_id = widget_data['page']
            widget_id = widget_data['widget'].get('id', 'unknown')
            return f"{page_id}:{widget_id}"
        elif 'id' in widget_data:
            return widget_data['id']
        else:
            return filename

    def _setup_page_widgets(self, page_id: str, widget_infos: List[Dict[str, Any]]) -> bool:
        """
        Setup all widgets for a specific page.

        Args:
            page_id: Page identifier
            widget_infos: List of widget info dictionaries

        Returns:
            True if successful, False otherwise
        """
        # Check if page exists
        page_exists = self.page_exists(page_id)

        # Collect all widgets
        all_widgets = []

        if page_exists:
            # Get existing widgets
            current_page = self.get_page(page_id)
            if current_page:
                all_widgets = current_page.get('widgets', [])

        # Find the dashboard widget and add new widgets to it
        dashboard_widget = None
        dashboard_widget_index = None

        for i, widget in enumerate(all_widgets):
            if widget.get('type') == 'dashboard-widget':
                dashboard_widget = widget
                dashboard_widget_index = i
                break

        if dashboard_widget and 'widgets' in dashboard_widget:
            dashboard_nested_widgets = dashboard_widget['widgets']

            # Add all new widgets to the dashboard widget (skip duplicates)
            for widget_info in widget_infos:
                widget_config = widget_info['data']['widget']
                widget_id = widget_config.get('id', 'unknown')

                # Check if widget already exists in dashboard
                widget_exists = any(
                    existing_widget.get('id') == widget_id for existing_widget in dashboard_nested_widgets)

                if not widget_exists:
                    dashboard_nested_widgets.append(widget_config)
                    self.logger.info(f"Adding widget {widget_id} to dashboard widget on page {page_id}")
                else:
                    self.logger.info(f"Widget {widget_id} already exists in dashboard on page {page_id}, skipping")

            # Update the dashboard widget with the new nested widgets
            all_widgets[dashboard_widget_index] = dashboard_widget
        else:
            self.logger.warning(f"No dashboard widget found on page {page_id}, adding widgets at page level")
            # Fallback: add widgets at page level
            for widget_info in widget_infos:
                widget_config = widget_info['data']['widget']
                widget_id = widget_config.get('id', 'unknown')

                # Check if widget already exists
                widget_exists = any(existing_widget.get('id') == widget_id for existing_widget in all_widgets)

                if not widget_exists:
                    all_widgets.append(widget_config)
                    self.logger.info(f"Adding widget {widget_id} to page {page_id} (fallback)")
                else:
                    self.logger.info(f"Widget {widget_id} already exists on page {page_id}, skipping")

        if not page_exists:
            # Create new page with all widgets
            page_data = {
                'identifier': page_id,
                'title': page_id.title(),
                'type': 'dashboard',
                'widgets': all_widgets,
                'showInSidebar': True,
                'section': 'software_catalog',
                'sidebar': 'catalog',
                'protected': False
            }

            self.logger.info(f"Creating page {page_id} with {len(all_widgets)} widgets")
            return self.create_page(page_data)
        else:
            # Update existing page with all widgets
            current_page = self.get_page(page_id)
            if not current_page:
                self.logger.error(f"Failed to get current page data: {page_id}")
                return False

            current_page['widgets'] = all_widgets
            clean_page_data = self._clean_page_data(current_page)

            self.logger.info(f"Updating page {page_id} with {len(all_widgets)} widgets")
            return self.update_page(page_id, clean_page_data)
