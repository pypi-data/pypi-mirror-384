import unittest
from unittest.mock import patch, MagicMock

from pica_langchain.client import PicaClient
from pica_langchain.models import Connection, ExecuteParams, ActionToExecute, PicaClientOptions, ConnectionDefinition

class TestPicaClient(unittest.TestCase):
    @patch('requests.get')
    def test_initialize_connections(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rows": [
                {
                    "id": "a77e130c-ce37-4a58-831c-62f2313da46d",
                    "platformVersion": "1.0.0",
                    "name": None,
                    "type": "api",
                    "key": "test::exa::default::2a5b13860bd1405d922f1014ae227f92",
                    "environment": "test", 
                    "platform": "exa",
                    "identity": "2a5b13860bd1405d922f1014ae227f92",
                    "identityType": None,
                    "description": "Exa is a semantic search engine built to help users find high-quality, insightful content from across the web. It focuses on meaning-based search rather than just keyword matching.",
                    "version": "1.0.0",
                    "state": "operational",
                    "active": True
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        client = PicaClient("fake-secret")
        
        # Reset the mock to clear previous calls
        mock_get.reset_mock()
        
        client._initialize_connections()
        
        mock_get.assert_called_once()
        self.assertEqual(len(client.connections), 1)
        self.assertEqual(client.connections[0].key, "test::exa::default::2a5b13860bd1405d922f1014ae227f92")
        self.assertEqual(client.connections[0].platform, "exa")
    
    @patch('requests.get')
    def test_get_available_actions(self, mock_get):
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            "rows": [
                {
                    "_id": "action1",
                    "title": "Test Action",
                    "connectionPlatform": "gmail",
                    "knowledge": "This is a test action",
                    "path": "/test/path",
                    "baseUrl": "https://api.example.com",
                    "tags": ["test"]
                }
            ],
            "total": 1,
            "skip": 0,
            "limit": 100
        }
        mock_response1.raise_for_status = MagicMock()
        
        mock_get.return_value = mock_response1
        
        client = PicaClient("fake-secret")
        
        result = client.get_available_actions("gmail")
        
        self.assertTrue(result.success)
        self.assertEqual(result.platform, "gmail")
        self.assertIsNotNone(result.actions)
        self.assertEqual(len(result.actions), 1)  # type: ignore
        self.assertIsNotNone(result.actions[0])  # type: ignore
        self.assertEqual(result.actions[0]["_id"], "action1")  # type: ignore
    
    @patch('requests.get')
    def test_get_action_knowledge(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rows": [
                {
                    "_id": "action1",
                    "title": "Test Action",
                    "connectionPlatform": "gmail",
                    "knowledge": "This is a test action",
                    "path": "/test/path",
                    "baseUrl": "https://api.example.com",
                    "tags": ["test"]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_get.return_value = mock_response
        
        client = PicaClient("fake-secret")
        
        result = client.get_action_knowledge("gmail", "action1")
        
        self.assertTrue(result.success)
        self.assertEqual(result.platform, "gmail")
        self.assertIsNotNone(result.action)

    @patch('requests.request')
    @patch('requests.get')
    def test_execute(self, mock_get, mock_request):
        mock_action_response = MagicMock()
        mock_action_response.json.return_value = {
            "rows": [
                {
                    "_id": "action1",
                    "title": "Test Action",
                    "connectionPlatform": "gmail",
                    "knowledge": "This is a test action",
                    "path": "/test/path",
                    "baseUrl": "https://api.example.com",
                    "tags": ["test"]
                }
            ]
        }
        mock_action_response.raise_for_status = MagicMock()
        
        mock_execute_response = MagicMock()
        mock_execute_response.json.return_value = {"success": True, "data": "test data"}
        mock_execute_response.raise_for_status = MagicMock()
        
        mock_get.return_value = mock_action_response
        mock_request.return_value = mock_execute_response
        
        client = PicaClient("fake-secret")
        client.connections = [
            Connection(
                _id="conn1",
                platformVersion="1.0",
                connectionDefinitionId="def1",
                name="Test Connection",
                key="test-conn-1",
                environment="prod",
                platform="gmail",
                secretsServiceId="sec1",
                settings={
                    "parseWebhookBody": True,
                    "showSecret": True,
                    "allowCustomEvents": True,
                    "oauth": True
                },
                throughput={"key": "x", "limit": 100},
                updated=True,
                version="1",
                deleted=False,
                tags=["test"],
                active=True,
                deprecated=False
            )
        ]
        
        params = ExecuteParams(
            platform="gmail",
            action=ActionToExecute(_id="action1", path="/test/path"),
            method="GET",
            connection_key="test-conn-1"
        )
        
        result = client.execute(params)
        
        self.assertTrue(result.success)
        self.assertEqual(result.platform, "gmail")
        self.assertEqual(result.data, {"success": True, "data": "test data"})

    @patch('requests.get')
    def test_initialize_connection_definitions_with_authkit(self, mock_get):
        """Test that the authkit parameter is added to the URL when enabled."""
        # Prepare a mock response with connection definition data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rows": [
                {
                    "_id": "def1",
                    "name": "Gmail Connector",
                    "key": "gmail-connector",
                    "platform": "gmail",
                    "platformVersion": "1.0",
                    "description": "Connect to Gmail",
                    "category": "email",
                    "image": "https://example.com/gmail.png",
                    "tags": ["email", "google"],
                    "oauth": True,
                    "updated": True,
                    "version": "1",
                    "deleted": False,
                    "active": True,
                    "deprecated": False
                }
            ],
            "total": 1,
            "skip": 0,
            "limit": 100
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Create client with authkit enabled
        options = PicaClientOptions(authkit=True)
        client = PicaClient("fake-secret", options=options)
        
        # Reset mock to clear initialization calls
        mock_get.reset_mock()
        
        # Call method directly to test
        client._initialize_connection_definitions()
        
        # Check that the request was made
        mock_get.assert_called()
        
        # Get the params from the call
        args, kwargs = mock_get.call_args
        params = kwargs.get('params', {})
        
        # Assert the params contain the authkit parameter
        self.assertIn('authkit', params)
        self.assertEqual(params['authkit'], 'true')
        
        # Verify the connection definition was processed correctly
        self.assertEqual(len(client.connection_definitions), 1)
        self.assertEqual(client.connection_definitions[0].key, "gmail-connector")
        self.assertEqual(client.connection_definitions[0].platform, "gmail")
        self.assertTrue(client.connection_definitions[0].oauth)
        
    @patch('requests.get')
    def test_initialize_connection_definitions_without_authkit(self, mock_get):
        """Test that the authkit parameter is not added to the URL when disabled."""
        # Prepare a mock response with connection definition data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rows": [
                {
                    "_id": "def1",
                    "name": "Gmail Connector",
                    "key": "gmail-connector",
                    "platform": "gmail",
                    "platformVersion": "1.0",
                    "description": "Connect to Gmail",
                    "category": "email",
                    "image": "https://example.com/gmail.png",
                    "tags": ["email", "google"],
                    "oauth": True,
                    "updated": True,
                    "version": "1",
                    "deleted": False,
                    "active": True,
                    "deprecated": False
                }
            ],
            "total": 1,
            "skip": 0,
            "limit": 100
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Create client with authkit disabled (default)
        options = PicaClientOptions(authkit=False)
        client = PicaClient("fake-secret", options=options)
        
        # Reset mock to clear initialization calls
        mock_get.reset_mock()
        
        # Call method directly to test
        client._initialize_connection_definitions()
        
        # Check that the request was made
        mock_get.assert_called()
        
        # Get the params from the call
        args, kwargs = mock_get.call_args
        params = kwargs.get('params', {})
        
        # Assert the params do not contain the authkit parameter
        self.assertNotIn('authkit', params,
                        f"Found unexpected 'authkit' in params: {params}")
        
        # Verify the connection definition was processed correctly
        self.assertEqual(len(client.connection_definitions), 1)
        self.assertEqual(client.connection_definitions[0].key, "gmail-connector")
        self.assertEqual(client.connection_definitions[0].platform, "gmail")
        self.assertTrue(client.connection_definitions[0].oauth)

    def test_normalize_action_id(self):
        client = PicaClient("fake-secret")
        
        test_cases = [
            ("conn_mod_def::F_JeJ_A_TKg::cc2kvVQQTiiIiLEDauy6zQ", "conn_mod_def::F_JeJ_A_TKg::cc2kvVQQTiiIiLEDauy6zQ"),
            ("GCQEQGUVPz4::duqxCkRtSQKWGWb5eFgyLg", "conn_mod_def::GCQEQGUVPz4::duqxCkRtSQKWGWb5eFgyLg"),
            ("mcp_test_tool", "conn_mod_def::mcp_test_tool"),
            ("simple_action_id", "conn_mod_def::simple_action_id"),
            ("action:test", "conn_mod_def::action:test"),
        ]
        
        for input_id, expected_output in test_cases:
            with self.subTest(input_id=input_id):
                result = client.normalize_action_id(input_id)
                self.assertEqual(result, expected_output, 
                               f"Failed for input '{input_id}': expected '{expected_output}', got '{result}'")

if __name__ == '__main__':
    unittest.main()
