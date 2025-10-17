import json
from typing import Dict, List, Any, Optional, Union
import requests
from requests_toolbelt import MultipartEncoder
import sys
import re
from langchain.tools import BaseTool

from .mcp import MCPClientOptions, PicaMCPClient

from .models import (
    Connection, 
    ConnectionDefinition, 
    AvailableAction,
    ExecuteParams, 
    ActionsResponse,
    ActionKnowledgeResponse,
    ExecuteResponse,
    RequestConfig,
    PicaClientOptions
)
from .logger import get_logger, log_request_response
from .prompts import get_default_system_prompt, get_authkit_system_prompt, generate_full_system_prompt

logger = get_logger()


class PicaClient:
    """
    Client for interacting with the Pica API.
    """
    def __init__(self, secret: str, options: Optional[PicaClientOptions] = None):
        """
        Initialize the Pica client.
        
        Args:
            secret: The API secret for Pica.
            options: Optional configuration parameters.
                - server_url: Custom server URL to use instead of the default.
                - connectors: List of connector keys to filter by.
                - actions: List of action IDs to filter by. Default is all actions.
                - permissions: Permission level to filter actions by. 'read' allows GET only, 'write' allows POST/PUT/PATCH, 'admin' allows all methods.
                - identity: Filter connections by specific identity ID.
                - identity_type: Filter connections by identity type (user, team, organization, or project).
                - authkit: Whether to use the AuthKit integration which enables the promptToConnectPlatform tool.
        """
        if not secret:
            logger.error("Pica API secret is required")
            print("ERROR: Pica API secret is required")
            sys.exit(1)
            
        self.secret = secret
        self.connections: List[Connection] = []
        self.connection_definitions: List[ConnectionDefinition] = []
        
        # Use default options if none provided
        options = options or PicaClientOptions()
        
        self.base_url = options.server_url
        logger.info(f"Initializing Pica client with base URL: {self.base_url}")
        
        self.get_connection_url = f"{self.base_url}/v1/vault/connections"
        self.available_actions_url = f"{self.base_url}/v1/knowledge"
        self.get_available_connectors_url = f"{self.base_url}/v1/available-connectors"
        
        self._initialized = False
        self._connectors_filter = options.connectors
        if self._connectors_filter:
            logger.debug(f"Filtering connections by keys: {self._connectors_filter}")
            
        self._identity_filter = options.identity
        self._identity_type_filter = options.identity_type
        if self._identity_filter or self._identity_type_filter:
            logger.debug(f"Filtering connections by identity: {self._identity_filter}, type: {self._identity_type_filter}")
        
        self._use_authkit = options.authkit
        if self._use_authkit:
            logger.debug("Using AuthKit settings")
            self._system_prompt = get_authkit_system_prompt("Loading connections...")
        else:
            self._system_prompt = get_default_system_prompt("Loading connections...")
        
        self._actions_filter = options.actions
        if self._actions_filter:
            logger.debug(f"Filtering actions by IDs: {self._actions_filter}")
        
        self._permissions_filter = options.permissions
        if self._permissions_filter:
            logger.debug(f"Filtering actions by permissions: {self._permissions_filter}")

        self.mcp_client = None
        self.mcp_tools = []
        if options.mcp_options:
            logger.debug("Initializing MCP client with provided options")
            mcp_options = MCPClientOptions(servers=options.mcp_options)
            self.mcp_client = PicaMCPClient(options=mcp_options)        

    def initialize(self) -> None:
        """
        Synchronously initialize the client by fetching connections and available connectors.
        Does not initialize MCP client which requires async.
        """
        if self._initialized:
            logger.debug("Client already initialized, skipping initialization")
            return
        
        # Initialize connections and definitions
        self._initialize_connections_and_definitions()
        
        # Generate system prompt without MCP tools info
        self._generate_system_prompt()
        
        if self.mcp_client:
            logger.warning("MCP client initialization requires async context. Call async_initialize() after creating the client.")
        
        self._initialized = True
        logger.info("Pica client initialization complete (MCP client not initialized)")
    
    def _initialize_connections_and_definitions(self) -> None:
        """Initialize connections and connection definitions."""
        logger.info("Initializing Pica client connections and definitions")
        
        if self._connectors_filter and "*" in self._connectors_filter:
            logger.debug("Initializing all available connections")
            self._initialize_connections()
        elif self._connectors_filter:
            logger.debug(f"Initializing specific connections: {self._connectors_filter}")
            self._initialize_connections()
        else:
            logger.debug("No connections to initialize (empty connectors list)")
            self.connections = []
        
        self._initialize_connection_definitions()
        
        logger.debug("Connections and definitions initialized")        
    
    async def async_initialize(self) -> None:
        """
        Asynchronously initialize the client including MCP client.
        """
        # First do the synchronous initialization if not already done
        if not self._initialized:
            # Initialize everything except MCP and system prompt generation
            self._initialize_connections_and_definitions()
        
        # Initialize MCP client if available
        if self.mcp_client:
            logger.info("Initializing MCP client")
            try:
                self.mcp_tools = await self.mcp_client.initialize()
                logger.info(f"Loaded {len(self.mcp_tools)} tools from MCP servers")
            except Exception as e:
                logger.error(f"Error initializing MCP client: {e}")
        
        # Now generate the system prompt with MCP tools info
        self._generate_system_prompt()
        
        self._initialized = True
        logger.info("Pica client initialization complete")

    def _generate_system_prompt(self) -> None:
        """Generate the system prompt with all necessary information including MCP tools."""
        filtered_connections = [conn for conn in self.connections if conn.active]
        logger.debug(f"Found {len(filtered_connections)} active connections")
        
        connections_info = (
            "\t* " + "\n\t* ".join([
                f"{conn.platform} - Key: {conn.key}" 
                for conn in filtered_connections
            ])
            if filtered_connections 
            else "No connections available"
        )
         
        available_platforms_info = "\n\t* ".join([
            f"{def_.platform} ({def_.name})"
            for def_ in self.connection_definitions
        ])

        # Generate MCP tools info if available
        mcp_tools_info = ""
        if self.mcp_tools:
            mcp_tools_list = []
            for tool in self.mcp_tools:
                # Format each tool with its name, description, and parameters
                params_info = ""
                if hasattr(tool, 'parameter_schema'):
                    schema = getattr(tool, 'parameter_schema')
                    if schema:
                        required_params = schema.get('required', [])
                        properties = schema.get('properties', {})
                        
                        param_details = []
                        for param_name, param_info in properties.items():
                            is_required = param_name in required_params
                            param_type = param_info.get('type', 'unknown')
                            param_desc = param_info.get('description', '')
                            
                            if is_required:
                                param_details.append(f"{param_name} ({param_type}, REQUIRED): {param_desc}")
                            else:
                                param_details.append(f"{param_name} ({param_type}, optional): {param_desc}")
                        
                        if param_details:
                            params_info = "\n    Parameters:\n    - " + "\n    - ".join(param_details)
                
                mcp_tools_list.append(f"- {tool.name}: {tool.description}{params_info}")
            
            mcp_tools_info = "\n".join(mcp_tools_list)
        
        if self._use_authkit:
            self._system_prompt = get_authkit_system_prompt(
                connections_info, 
                available_platforms_info,
                mcp_tools_info
            )
        else:
            self._system_prompt = get_default_system_prompt(
                connections_info, 
                available_platforms_info,
                mcp_tools_info
            )

        logger.info(f"System prompt generated with MCP tools info")

    @classmethod
    async def create(cls, secret: str, options: Optional[PicaClientOptions] = None):
        """
        Factory method to create and initialize a PicaClient with async support.
        
        Args:
            secret: The API secret for Pica.
            options: Optional configuration parameters.
            
        Returns:
            An initialized PicaClient instance.
        """
        client = cls(secret, options)
        await client.async_initialize()
        return client
    
    def _initialize_connections(self) -> None:
        """Fetch connections from the API."""
        try:
            logger.debug("Fetching connections from API")
            
            params: Dict[str, Any] = {}
            
            if self._identity_filter:
                params["identity"] = self._identity_filter
                
            if self._identity_type_filter:
                params["identityType"] = self._identity_type_filter
            
            if self._connectors_filter and "*" not in self._connectors_filter:
                keys_param = ",".join(self._connectors_filter)
                params["key"] = keys_param
                logger.debug(f"Adding key filter parameter: {keys_param}")
            
            try:
                connections_data = self._paginate_results(
                    self.get_connection_url,
                    params=params
                )
                
                self.connections = [Connection(**conn) for conn in connections_data]
                logger.info(f"Successfully fetched {len(self.connections)} connections")
            except Exception as e:
                logger.error(f"Failed to paginate connections: {e}", exc_info=True)
                raise
                
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}", exc_info=True)
            print(f"Failed to initialize connections: {e}")
            self.connections = []
    
    def _initialize_connection_definitions(self) -> None:
        """Fetch available connectors from the API."""
        try:
            logger.debug("Fetching available connectors from API")
            
            params: Dict[str, Any] = {}
            
            # Add authkit parameter if enabled
            if self._use_authkit:
                params["authkit"] = "true"
                logger.debug("Adding authkit=true parameter to available connectors request")
            
            try:
                connectors_data = self._paginate_results(
                    self.get_available_connectors_url,
                    params=params
                )
                
                self.connection_definitions = [
                    ConnectionDefinition(**def_) 
                    for def_ in connectors_data
                ]
                logger.info(f"Successfully fetched {len(self.connection_definitions)} available connectors")
            except Exception as e:
                logger.error(f"Failed to paginate available connectors: {e}", exc_info=True)
                raise
                
        except Exception as e:
            logger.error(f"Failed to initialize available connectors: {e}", exc_info=True)
            print(f"Failed to initialize available connectors: {e}")
            self.connection_definitions = []
    
    def _generate_headers(self) -> Dict[str, str]:
        """Generate headers for API requests."""
        return {
            "Content-Type": "application/json",
            "x-pica-secret": self.secret,
        }        
    
    async def generate_system_prompt(self, user_system_prompt: Optional[str] = None) -> str:
        """
        Generate a system prompt for use with LLMs.
        
        Args:
            user_system_prompt: Optional custom system prompt to prepend.
            
        Returns:
            The complete system prompt including Pica connection information.
        """
        if not self._initialized:
            self.initialize()
        
        return generate_full_system_prompt(self._system_prompt, user_system_prompt)
    
    @property
    def system(self) -> str:
        """Get the current system prompt."""
        return self._system_prompt
    
    def _paginate_results(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Paginate through API results.
        
        Args:
            url: The API endpoint URL.
            params: Query parameters to include in the request.
            limit: The number of results to fetch per page.
            
        Returns:
            A list of all results.
        """
        params = params or {}
        skip = 0
        all_results = []
        total = 0
        
        try:
            while True:
                current_params = {
                    **params,
                    "skip": skip,
                    "limit": limit
                }

                response = requests.get(
                    url, 
                    params=current_params, 
                    headers=self._generate_headers()
                )
                response.raise_for_status()
                data = response.json()
                
                rows = data.get("rows", [])
                total = data.get("total", 0)
                all_results.extend(rows)
                
                skip += limit
                if len(all_results) >= total:
                    break
                
            return all_results
        except Exception as e:
            print(f"Error in pagination: {e}")
            raise

    def _transform_knowledge_api_to_action(self, data: Dict[str, Any]) -> AvailableAction:
        """
        Transform knowledge API response format to AvailableAction.

        Knowledge API format uses: _id, connectionPlatform, baseUrl, etc.

        Args:
            data: Raw action data from knowledge API.

        Returns:
            AvailableAction instance.
        """
        return AvailableAction(**data)

    def _transform_search_api_to_action(self, data: Dict[str, Any]) -> AvailableAction:
        """
        Transform search API response format to AvailableAction.

        Search API format uses: systemId (maps to _id), key, etc.

        Args:
            data: Raw action data from search API.

        Returns:
            AvailableAction instance.
        """
        # Map systemId to _id for compatibility with AvailableAction model
        transformed = {
            "_id": data.get("systemId"),
            "title": data.get("title"),
            "method": data.get("method"),
            "path": data.get("path"),
            "tags": data.get("tags", []),
            "key": data.get("key"),  # Extra field, allowed by model
        }

        # Add any other fields that might be present
        for key, value in data.items():
            if key not in ["systemId"] and key not in transformed:
                transformed[key] = value

        return AvailableAction(**transformed)

    def get_all_available_actions(self, platform: str) -> List[AvailableAction]:
        """
        Get all available actions for a platform.

        Args:
            platform: The platform to get actions for.

        Returns:
            A list of available actions.
        """
        try:
            params = {
                "supported": "true",
                "connectionPlatform": platform
            }

            actions_data = self._paginate_results(
                self.available_actions_url,
                params=params
            )

            return [self._transform_knowledge_api_to_action(action) for action in actions_data]
        except Exception as e:
            print(f"Error fetching all available actions: {e}")
            raise ValueError("Failed to fetch all available actions")

    def search_available_actions(self, platform: str, query: str, limit: int = 20) -> List[AvailableAction]:
        """
        Search for available actions on a platform using vector search.

        Args:
            platform: The platform to search actions for.
            query: Descriptive intent phrase (without platform name).
            limit: Maximum number of results to return (default: 20).

        Returns:
            A list of relevant available actions.
        """
        try:
            logger.info(f"Searching actions for platform: {platform} with query: {query}")

            search_url = f"{self.base_url}/v1/available-actions/search/{platform}"
            params = {
                "query": query,
                "limit": limit
            }

            log_request_response("GET", search_url, request_data=params)
            response = requests.get(
                search_url,
                params=params,
                headers=self._generate_headers()
            )
            response.raise_for_status()

            # Search API returns a direct array, not wrapped in an object
            actions_data = response.json()

            # Validate that we got an array
            if not isinstance(actions_data, list):
                logger.error(f"Unexpected response format from search API: {type(actions_data)}")
                raise ValueError("Search API returned unexpected format")

            log_request_response("GET", search_url,
                                request_data=params,
                                response_status=response.status_code,
                                response_data={"results_count": len(actions_data)})

            # Transform search API format to AvailableAction instances
            actions = [self._transform_search_api_to_action(action) for action in actions_data]

            logger.info(f"Found {len(actions)} actions for query: {query}")
            return actions
        except Exception as e:
            logger.error(f"Error searching available actions: {e}", exc_info=True)
            print(f"Error searching available actions: {e}")
            raise ValueError("Failed to search available actions")
    
    def normalize_action_id(self, action_id: str) -> str:
        """
        Normalize action ID by adding the conn_mod_def:: prefix if it's missing.
        
        Args:
            action_id: The action ID to normalize.
            
        Returns:
            The normalized action ID with proper prefix.
        """
        if not action_id:
            return action_id
            
        if not action_id.startswith("conn_mod_def::"):
            return f"conn_mod_def::{action_id}"
            
        return action_id

    def get_single_action(self, action_id: str) -> AvailableAction:
        """
        Get a single action by ID.
        
        Args:
            action_id: The ID of the action to get.
            
        Returns:
            The requested action.
        """
        try:
            # Normalize the action ID to ensure it has the proper prefix
            normalized_action_id = self.normalize_action_id(action_id)
            logger.debug(f"Fetching action with ID: {normalized_action_id} (original: {action_id})")
            
            params = {"_id": normalized_action_id}
            
            log_request_response("GET", self.available_actions_url, request_data=params)
            response = requests.get(
                self.available_actions_url,
                params=params,
                headers=self._generate_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            log_request_response("GET", self.available_actions_url, 
                                request_data=params,
                                response_status=response.status_code, 
                                response_data={"rows_count": len(data.get("rows", []))})
            
            if not data.get("rows") or len(data["rows"]) == 0:
                logger.warning(f"Action with ID {normalized_action_id} not found")
                raise ValueError(f"Action with ID {normalized_action_id} not found")
            
            action = AvailableAction(**data["rows"][0])
            logger.debug(f"Successfully fetched action: {action.title}")
            return action
        except Exception as e:
            logger.error(f"Error fetching single action: {e}", exc_info=True)
            print(f"Error fetching single action: {e}")
            raise ValueError("Failed to fetch action")
    
    def get_available_actions(self, platform: str, query: Optional[str] = None, limit: int = 20) -> ActionsResponse:
        """
        Get available actions for a platform.

        Args:
            platform: The platform to get actions for.
            query: Optional search query to filter actions using vector search.
            limit: Maximum number of results when using search (default: 20).

        Returns:
            A response containing the available actions.
        """
        try:
            logger.info(f"Fetching available actions for platform: {platform}")

            if query:
                logger.debug(f"Using search with query: {query}")
                all_actions = self.search_available_actions(platform, query, limit)
            else:
                logger.debug("Fetching all available actions")
                all_actions = self.get_all_available_actions(platform)
            
            # Filter actions by IDs if actions filter is provided
            if self._actions_filter:
                logger.debug(f"Filtering actions by IDs: {self._actions_filter}")
                actions_filter_set = set(self._actions_filter)
                filtered_actions = []
                
                for action in all_actions:
                    action_id = self._extract_action_id(action)
                    if action_id and action_id in actions_filter_set:
                        filtered_actions.append(action)
                
                all_actions = filtered_actions
                logger.info(f"After filtering by IDs, {len(all_actions)} actions remain")
            
            # Filter actions by permissions if permissions filter is provided
            if self._permissions_filter:
                logger.debug(f"Filtering actions by permissions: {self._permissions_filter}")
                filtered_by_permissions = []
                
                if self._permissions_filter == "read":
                    for action in all_actions:
                        method = action.method
                        if method and method.upper() == "GET":
                            filtered_by_permissions.append(action)
                elif self._permissions_filter == "write":
                    for action in all_actions:
                        method = action.method
                        if method and method.upper() in ["POST", "PUT", "PATCH"]:
                            filtered_by_permissions.append(action)
                # For "admin" or no permissions set, return all actions (no filtering)
                else:
                    filtered_by_permissions = all_actions
                
                all_actions = filtered_by_permissions
                logger.info(f"After filtering by permissions ({self._permissions_filter}), {len(all_actions)} actions remain")

            # Create simplified action representations
            simplified_actions = []
            for action in all_actions:
                try:
                    action_id = self._extract_action_id(action)
                    if not action_id:
                        logger.warning(f"Skipping action without valid ID: {action.title}")
                        continue
                        
                    simplified_actions.append({
                        "_id": action_id,
                        "title": action.title or "Untitled Action",
                        "tags": action.tags or []
                    })
                except Exception as e:
                    logger.warning(f"Error processing action {getattr(action, 'title', 'Unknown')}: {e}")
                    continue
            
            # Include relevant MCP tools based on a generic matching approach
            # This is a more dynamic approach that doesn't rely on hardcoded platform names
            if self.mcp_tools:
                platform_terms = platform.lower().split()
                platform_terms.append(platform.lower())  # Add the full platform name as well
                
                # Find any MCP tools that might match the platform name or related terms
                for tool in self.mcp_tools:
                    tool_name = tool.name.lower()
                    tool_desc = tool.description.lower() if hasattr(tool, 'description') else ""
                    
                    # Check if any platform term appears in the tool name or description
                    if any(term in tool_name or term in tool_desc for term in platform_terms):
                        simplified_actions.append({
                            "_id": f"mcp_{tool.name}",
                            "title": tool.name,
                            "tags": ["MCP", "Tool"]
                        })

            logger.info(f"Found {len(simplified_actions)} available actions for {platform}")
            return ActionsResponse(
                success=True,
                actions=simplified_actions,
                platform=platform,
                content=f"Found {len(simplified_actions)} available actions for {platform}"
            )
        except Exception as e:
            logger.error(f"Error fetching available actions for {platform}: {e}", exc_info=True)
            print(f"Error fetching available actions: {e}")
            return ActionsResponse(
                success=False,
                title="Failed to get available actions",
                message=str(e),
                raw=str(e)
            )
    
    def get_action_knowledge(self, platform: str, action_id: str) -> ActionKnowledgeResponse:
        """
        Get knowledge about a specific action.
        
        Args:
            platform: The platform the action belongs to.
            action_id: The ID of the action.
            
        Returns:
            A response containing the action knowledge.
        """
        try:
            action = self.get_single_action(action_id)
            
            return ActionKnowledgeResponse(
                success=True,
                action=action,
                platform=platform,
                content=f"Found knowledge for action: {action.title}"
            )
        except Exception as e:
            print(f"Error getting action knowledge: {e}")
            return ActionKnowledgeResponse(
                success=False,
                platform=platform,
                title="Failed to get action knowledge",
                message=str(e),
                raw=str(e)
            )

    def get_mcp_tools(self) -> List[BaseTool]:
        """
        Get tools from connected MCP servers.
        
        Returns:
            List of LangChain tools from MCP servers.
        """
        return self.mcp_tools    

    def _extract_action_id(self, action: AvailableAction) -> Optional[str]:
        """
        Extract the action ID from an AvailableAction object.
        
        Args:
            action: The AvailableAction object.
            
        Returns:
            The action ID or None if not found.
        """
        if hasattr(action, '_id') and action._id:
            return action._id
        
        try:
            action_dict = action.model_dump()
            return action_dict.get("_id")
        except Exception:
            return None

    def _replace_path_variables(
        self, 
        path: str, 
        variables: Dict[str, Union[str, int, bool]]
    ) -> str:
        """
        Replace variables in a path string.
        
        Args:
            path: The path template string.
            variables: A dictionary of variable values.
            
        Returns:
            The path with variables replaced.
        """
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name not in variables:
                raise ValueError(f"Missing value for path variable: {var_name}")
            return str(variables[var_name])
        
        return re.sub(r'\{\{([^}]+)\}\}', replace_var, path)
    
    def execute(self, params: ExecuteParams) -> ExecuteResponse:
        """
        Execute an action using the passthrough API.
        
        Args:
            params: The parameters for the action execution.
            
        Returns:
            The response from the API.
        """
        try:
            logger.info(f"Executing action for platform: {params.platform}, method: {params.method}")
            
            # Check if connection exists
            if not any(conn.key == params.connection_key for conn in self.connections):
                error_msg = f"Connection not found. Please add a {params.platform} connection first."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.debug(f"Getting full action details for ID: {params.action.id}")
            full_action = self.get_single_action(params.action.id)
            
            path = params.action.path
            template_vars = re.findall(r'\{\{([^}]+)\}\}', path)
            path_variables = params.path_variables or {}
            
            if template_vars:
                logger.debug(f"Found path variables in action path: {template_vars}")
                required_vars = template_vars
                
                # Combine data and path_variables
                if isinstance(params.data, dict):
                    combined_vars = {**params.data, **path_variables}
                else:
                    combined_vars = path_variables
                
                # Check for missing variables
                missing_vars = [v for v in required_vars if v not in combined_vars]
                if missing_vars:
                    error_msg = f"Missing required path variables: {', '.join(missing_vars)}. Please provide values for these variables."
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # Move variables from data to path_variables if needed
                if isinstance(params.data, dict):
                    for var in required_vars:
                        if var in params.data and var not in path_variables:
                            path_variables[var] = params.data[var]
                            # Create a copy to avoid modifying the original
                            data_copy = dict(params.data)
                            del data_copy[var]
                            params.data = data_copy
                
                # Replace variables in path
                path = self._replace_path_variables(path, path_variables)
                logger.debug(f"Path after variable replacement: {path}")
            
            headers = {
                **self._generate_headers(),
                'x-pica-connection-key': params.connection_key,
                'x-pica-action-id': params.action.id,
            }
            
            if params.is_form_data:
                headers['Content-Type'] = 'multipart/form-data'
                
            url = f"{self.base_url}/v1/passthrough{path if path.startswith('/') else '/' + path}"
            
            request_config = {
                "url": url,
                "method": params.method,
                "headers": headers,
                "params": params.query_params
            }
            
            if params.method.lower() != 'get':
                if params.is_form_data and params.data and isinstance(params.data, dict):
                    # Convert data for multipart form
                    form_fields = {}
                    for key, value in params.data.items():
                        if isinstance(value, dict):
                            form_fields[key] = (None, json.dumps(value), 'application/json')
                        else:
                            form_fields[key] = (None, str(value))
                    
                    multipart_data = MultipartEncoder(fields=form_fields)
                    headers['Content-Type'] = multipart_data.content_type
                    request_config["data"] = multipart_data.to_string()
                    logger.debug("Request data formatted as multipart/form-data")
                else:
                    request_config["data"] = json.dumps(params.data) if params.data else None

            logger.debug(f"Request Config: {request_config}")
            
            # Log the request (with sensitive data masked)
            safe_headers = {k: v if 'secret' not in k.lower() and 'key' not in k.lower() else '********' 
                           for k, v in headers.items()}
            safe_config = {**request_config, "headers": safe_headers}
            log_request_response(params.method, url, request_data=safe_config)
            
            response = requests.request(
                method=params.method,
                url=url,
                headers=headers,
                params=params.query_params,
                data=request_config.get("data")
            )
            response.raise_for_status()
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            log_request_response(
                params.method, 
                url, 
                request_data=safe_config,
                response_status=response.status_code, 
                response_data={"success": True}
            )
            
            logger.info(f"Successfully executed {full_action.title} via {params.platform}")
            return ExecuteResponse(
                success=True,
                data=response_data,
                connectionKey=params.connection_key,
                platform=params.platform,
                action=full_action.title,
                requestConfig=RequestConfig(**request_config),
                knowledge=full_action.knowledge,
                content=f"Executed {full_action.title} via {params.platform}"
            )
        except Exception as e:
            logger.error(f"Error executing action: {e}", exc_info=True)
            print(f"Error executing action: {e}")
            
            log_request_response(
                params.method if hasattr(params, 'method') else "UNKNOWN", 
                f"{self.base_url}/v1/passthrough/...", 
                error=e
            )
            
            return ExecuteResponse(
                success=False,
                title="Failed to execute action",
                message=str(e),
                raw=str(e)
            )