"""
Tests for the Agent class (v1.2 - AgentContext API)
"""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from agent_sdk import Agent, AgentConfig, AgentContext
from agent_sdk.utils import get_agent_config_from_pyproject, read_pyproject_config


class TestAgent:
    """Test cases for the Agent class"""

    @pytest.fixture
    def mock_run_function(self):
        """Mock execution function for testing (v1.2 - takes AgentContext, returns None)"""

        def mock_func(agent: AgentContext) -> None:
            agent.log("Test execution")

        return mock_func

    @pytest.fixture
    def mock_stop_function(self):
        """Mock stop function for testing (v1.2 - takes AgentContext, returns None)"""

        def mock_func(agent: AgentContext) -> None:
            agent.log("Test stop")

        return mock_func

    @pytest.fixture
    def sample_current_positions(self):
        """Sample current positions for testing"""
        return [
            {
                "network": "ethereum:1",
                "assetAddress": "0x1234567890abcdef",
                "tokenId": None,
                "avgUnitCost": "100.00",
                "currentQty": "1.5",
            }
        ]

    def test_agent_initialization(self, mock_run_function, mock_stop_function):
        """Test basic agent initialization"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        assert agent.run_function == mock_run_function
        assert agent.stop_function == mock_stop_function
        assert agent.health_check_function is not None
        assert agent.config is not None
        assert agent.logger is not None

    def test_agent_initialization_with_config(
        self, mock_run_function, mock_stop_function
    ):
        """Test agent initialization with custom config"""
        config = AgentConfig(
            title="Test Agent",
            description="A test agent",
            version="2.0.0",
        )

        agent = Agent(
            run_function=mock_run_function,
            stop_function=mock_stop_function,
            config=config,
        )

        assert agent.config.title == "Test Agent"
        assert agent.config.description == "A test agent"
        assert agent.config.version == "2.0.0"

    def test_agent_initialization_missing_run_function(self):
        """Test that agent raises error when execution function is missing"""
        with pytest.raises(TypeError):
            Agent()

    def test_process_request_success(
        self, mock_run_function, mock_stop_function, sample_current_positions
    ):
        """Test successful request processing"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        result = agent.process_request(
            session_id=123,
            session_wallet_address="0x1234567890abcdef",
            current_positions=sample_current_positions,
            command="execute",
        )

        assert result["success"] is True

    def test_process_request_with_error(
        self, mock_stop_function, sample_current_positions
    ):
        """Test request processing with error"""

        def error_function(agent: AgentContext) -> None:
            raise Exception("Test error")

        agent = Agent(run_function=error_function, stop_function=mock_stop_function)

        result = agent.process_request(
            session_id=123,
            session_wallet_address="0x1234567890abcdef",
            current_positions=sample_current_positions,
            command="execute",
        )

        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]

    def test_default_health_function(self, mock_stop_function, mock_run_function):
        """Test the default health function"""
        agent = Agent(
            run_function=mock_run_function,
            stop_function=mock_stop_function,
        )

        result = agent.health_check_function()

        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "healthy"

    def test_get_handler(self, mock_run_function, mock_stop_function):
        """Test that handler is returned"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        handler = agent.get_handler()

        assert callable(handler)

    def test_get_worker_export(self, mock_run_function, mock_stop_function):
        """Test that worker export is returned"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        worker_export = agent.get_worker_export()

        # worker_export is a FastAPI app or handler
        assert worker_export is not None

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", False)
    def test_agent_without_fastapi(self, mock_run_function, mock_stop_function):
        """Test agent initialization when FastAPI is not available"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        # Should not raise an error
        assert agent.app is None

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", True)
    def test_agent_with_fastapi(self, mock_run_function, mock_stop_function):
        """Test agent initialization when FastAPI is available"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        # Should create FastAPI app
        assert agent.app is not None

    def test_agent_dict_style_initialization(
        self, mock_run_function, mock_stop_function
    ):
        """Test agent initialization with dict-style parameters"""
        params = {
            "run_function": mock_run_function,
            "stop_function": mock_stop_function,
            "title": "Test Agent",
            "description": "A test agent",
        }

        agent = Agent(**params)

        assert agent.run_function == mock_run_function
        assert agent.stop_function == mock_stop_function
        assert agent.config.title == "Test Agent"
        assert agent.config.description == "A test agent"


class TestAgentIntegration:
    """Integration tests for the Agent class"""

    def test_full_agent_workflow(self):
        """Test a complete agent workflow (v1.2)"""

        def execution_func(agent: AgentContext) -> None:
            agent.log(f"Processed session {agent.sessionId}")

        def stop_func(agent: AgentContext) -> None:
            agent.log("Cleaned up successfully")

        agent = Agent(run_function=execution_func, stop_function=stop_func)

        # Test execution
        exec_result = agent.process_request(
            session_id=123,
            session_wallet_address="0x1234567890abcdef",
            current_positions=[],
            command="execute",
        )

        assert exec_result["success"] is True


class TestAgentLambdaHandler:
    """Test cases for Lambda handler functionality"""

    @pytest.fixture
    def mock_run_function(self):
        """Mock execution function for testing"""

        def mock_func(agent: AgentContext) -> None:
            agent.log("Test execution")

        return mock_func

    @pytest.fixture
    def mock_stop_function(self):
        """Mock stop function for testing"""

        def mock_func(agent: AgentContext) -> None:
            agent.log("Test stop")

        return mock_func

    def test_handler_http_event(self, mock_run_function, mock_stop_function):
        """Test handler with HTTP event (should use Mangum)"""
        with patch("agent_sdk.agent.FASTAPI_AVAILABLE", True):
            agent = Agent(
                run_function=mock_run_function,
                stop_function=mock_stop_function,
            )

            # Mock the Mangum handler
            mock_mangum_response = {"statusCode": 200, "body": '{"success": true}'}
            agent._handler = MagicMock(return_value=mock_mangum_response)

            http_event = {
                "httpMethod": "POST",
                "path": "/run",
                "body": '{"sessionId": 123, "sessionWalletAddress": "0x123", "currentPositions": []}',
                "headers": {"Content-Type": "application/json"},
            }

            handler_func = agent.get_handler()
            result = handler_func(http_event, {})

            assert result == mock_mangum_response

    def test_handler_direct_invocation_run(self, mock_run_function, mock_stop_function):
        """Test handler with direct invocation for run command"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        event = {
            "body": json.dumps(
                {
                    "sessionId": 123,
                    "sessionWalletAddress": "0x1234567890abcdef",
                    "currentPositions": [],
                }
            ),
            "rawPath": "/run",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200
        response_body = json.loads(result["body"])
        assert response_body["success"] is True

    def test_handler_direct_invocation_execute(
        self, mock_run_function, mock_stop_function
    ):
        """Test handler with direct invocation for execute command (backward compatibility)"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        event = {
            "body": json.dumps(
                {
                    "sessionId": 123,
                    "sessionWalletAddress": "0x1234567890abcdef",
                    "currentPositions": [],
                }
            ),
            "rawPath": "/execute",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200
        response_body = json.loads(result["body"])
        assert response_body["success"] is True

    def test_handler_direct_invocation_health(
        self, mock_run_function, mock_stop_function
    ):
        """Test handler with health command"""
        agent = Agent(
            run_function=mock_run_function,
            stop_function=mock_stop_function,
        )

        event = {"body": "{}", "rawPath": "/health"}

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200
        response_body = json.loads(result["body"])
        assert response_body["status"] == "healthy"

    def test_handler_missing_parameters(self, mock_run_function, mock_stop_function):
        """Test handler with missing required parameters"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        event = {
            "body": json.dumps({}),  # Missing sessionId and sessionWalletAddress
            "rawPath": "/run",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 400
        assert "sessionId" in result["body"]

    def test_handler_base64_encoded_body(self, mock_run_function, mock_stop_function):
        """Test handler with base64 encoded body"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        body_data = {
            "sessionId": 123,
            "sessionWalletAddress": "0x123",
            "currentPositions": [],
        }
        encoded_body = base64.b64encode(json.dumps(body_data).encode()).decode()

        event = {"body": encoded_body, "isBase64Encoded": True, "rawPath": "/run"}

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200

    def test_handler_error_handling(self, mock_stop_function):
        """Test handler error handling"""

        def error_function(agent: AgentContext) -> None:
            raise Exception("Test error")

        agent = Agent(run_function=error_function, stop_function=mock_stop_function)

        event = {
            "body": json.dumps(
                {
                    "sessionId": 123,
                    "sessionWalletAddress": "0x123",
                    "currentPositions": [],
                }
            ),
            "rawPath": "/run",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Test error" in body["error"]

    def test_handler_delete_stop_method(self, mock_run_function, mock_stop_function):
        """Test handler with DELETE method for stop command"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        event = {
            "httpMethod": "DELETE",
            "body": json.dumps(
                {
                    "sessionId": 123,
                    "sessionWalletAddress": "0x123",
                    "currentPositions": [],
                }
            ),
            "rawPath": "/stop",
        }

        handler_func = agent.get_handler()
        result = handler_func(event, {})

        assert result["statusCode"] == 200

    def test_is_http_event(self, mock_run_function, mock_stop_function):
        """Test _is_http_event helper method"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        # Test with httpMethod and required fields
        assert (
            agent._is_http_event({"httpMethod": "POST", "headers": {}, "path": "/test"})
            is True
        )

        # Test with httpMethod but missing required fields
        assert agent._is_http_event({"httpMethod": "POST"}) is False

        # Test with requestContext (API Gateway v1.2 format)
        assert agent._is_http_event({"requestContext": {"http": {}}}) is True

        # Test with requestContext but missing http
        assert agent._is_http_event({"requestContext": {}}) is False

        # Test without either
        assert agent._is_http_event({"body": "{}"}) is False

    def test_parse_event_body_json_string(self, mock_run_function, mock_stop_function):
        """Test _parse_event_body with JSON string"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        event = {"body": '{"key": "value"}'}
        result = agent._parse_event_body(event)
        assert result == {"key": "value"}

    def test_parse_event_body_invalid_json(self, mock_run_function, mock_stop_function):
        """Test _parse_event_body with invalid JSON"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        event = {"body": "invalid json"}
        result = agent._parse_event_body(event)
        assert result == {}

    def test_parse_event_body_dict(self, mock_run_function, mock_stop_function):
        """Test _parse_event_body with dict body"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        event = {"body": {"key": "value"}}
        result = agent._parse_event_body(event)
        assert result == {"key": "value"}

    def test_parse_event_body_base64_error(self, mock_run_function, mock_stop_function):
        """Test _parse_event_body with base64 decode error"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        event = {"body": "invalid_base64", "isBase64Encoded": True}
        result = agent._parse_event_body(event)
        assert result == {}

    def test_extract_command(self, mock_run_function, mock_stop_function):
        """Test _extract_command helper method"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        # Test normal paths - should extract command as-is
        assert agent._extract_command({"rawPath": "/run"}) == "run"
        assert agent._extract_command({"rawPath": "/execute"}) == "execute"

        # Test Lambda runtime URL
        runtime_path = "/2015-03-31/functions/function/invocations/health"
        assert agent._extract_command({"rawPath": runtime_path}) == "health"

        # Test default
        assert agent._extract_command({}) == ""


class TestAgentCommandProcessing:
    """Test cases for command processing functionality"""

    @pytest.fixture
    def mock_run_function(self):
        def mock_func(agent: AgentContext) -> None:
            agent.log("Executed")

        return mock_func

    @pytest.fixture
    def mock_stop_function(self):
        def mock_func(agent: AgentContext) -> None:
            agent.log("Stopped")

        return mock_func

    def test_process_request_stop_command(self, mock_run_function, mock_stop_function):
        """Test process_request with stop command"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        result = agent.process_request(
            123, "0x123", current_positions=[], command="stop"
        )

        assert result["success"] is True

    def test_process_request_health_command(
        self, mock_run_function, mock_stop_function
    ):
        """Test process_request with health command"""
        agent = Agent(
            run_function=mock_run_function,
            stop_function=mock_stop_function,
        )

        result = agent.process_request(
            123, "0x123", current_positions=[], command="health"
        )

        assert result["status"] == "healthy"

    def test_process_request_unknown_command(
        self, mock_run_function, mock_stop_function
    ):
        """Test process_request with unknown command"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        result = agent.process_request(
            123, "0x123", current_positions=[], command="unknown"
        )

        assert result["success"] is False
        assert "Unknown command" in result["error"]

    def test_process_request_run_command(self, mock_run_function, mock_stop_function):
        """Test process_request with run command (new standard)"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        result = agent.process_request(
            123, "0x123", current_positions=[], command="run"
        )

        assert result["success"] is True

    def test_process_request_execute_command(
        self, mock_run_function, mock_stop_function
    ):
        """Test process_request with execute command (backward compatibility)"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        result = agent.process_request(
            123, "0x123", current_positions=[], command="execute"
        )

        assert result["success"] is True


class TestAgentRunMethod:
    """Test cases for the run method"""

    @pytest.fixture
    def mock_run_function(self):
        def mock_func(agent: AgentContext) -> None:
            pass

        return mock_func

    @pytest.fixture
    def mock_stop_function(self):
        def mock_func(agent: AgentContext) -> None:
            pass

        return mock_func

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", False)
    def test_run_without_fastapi(self, mock_run_function, mock_stop_function):
        """Test run method when FastAPI is not available"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        # Should not raise an error, just log and return
        agent.run()

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", True)
    def test_run_without_app(self, mock_run_function, mock_stop_function):
        """Test run method when FastAPI app is not initialized"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)
        agent.app = None

        # Should not raise an error, just log and return
        agent.run()

    @patch("agent_sdk.agent.FASTAPI_AVAILABLE", True)
    @patch("uvicorn.run")
    def test_run_with_fastapi(
        self, mock_uvicorn_run, mock_run_function, mock_stop_function
    ):
        """Test run method with FastAPI available"""
        agent = Agent(run_function=mock_run_function, stop_function=mock_stop_function)

        agent.run(host="127.0.0.1", port=8080)

        mock_uvicorn_run.assert_called_once_with(
            agent.app, host="127.0.0.1", port=8080, log_config=None
        )


class TestAgentErrorHandling:
    """Test cases for error handling scenarios"""

    @pytest.fixture
    def mock_stop_function(self):
        def mock_func(agent: AgentContext) -> None:
            pass

        return mock_func

    def test_agent_initialization_none_run_function(self, mock_stop_function):
        """Test agent initialization with None execution function"""
        with pytest.raises(ValueError, match="run_function is required"):
            Agent(run_function=None, stop_function=mock_stop_function)

    def test_default_stop_function_usage(self, mock_stop_function):
        """Test that default stop function works"""

        def mock_exec(agent: AgentContext) -> None:
            pass

        agent = Agent(run_function=mock_exec, stop_function=mock_stop_function)

        # Test stop command
        result = agent.process_request(
            123, "0x123", current_positions=[], command="stop"
        )

        assert result["success"] is True

    def test_get_worker_export_without_fastapi(self, mock_stop_function):
        """Test get_worker_export when FastAPI is not available"""

        def mock_exec(agent: AgentContext) -> None:
            pass

        with patch("agent_sdk.agent.FASTAPI_AVAILABLE", False):
            agent = Agent(run_function=mock_exec, stop_function=mock_stop_function)

            result = agent.get_worker_export()

            # Should return the handler function
            assert callable(result)


class TestUtilsFunctionality:
    """Test cases for utils.py functions to improve coverage"""

    @patch("agent_sdk.utils.toml.load")
    @patch("builtins.open")
    @patch("pathlib.Path.exists")
    def test_read_pyproject_config_success(
        self, mock_exists, mock_open, mock_toml_load
    ):
        """Test successful reading of pyproject.toml"""
        mock_config = {
            "project": {
                "name": "test-agent",
                "description": "Test Agent",
                "version": "2.0.0",
            }
        }
        mock_exists.return_value = True
        mock_toml_load.return_value = mock_config

        result = read_pyproject_config()

        assert result == mock_config
        mock_open.assert_called_once()
        mock_toml_load.assert_called_once()

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_read_pyproject_config_error_fallback(self, mock_open):
        """Test error handling and fallback config in read_pyproject_config"""
        result = read_pyproject_config()

        # Should return fallback config
        assert "project" in result
        assert result["project"]["name"] == "circuit-agent"
        assert result["project"]["version"] == "1.0.0"

    @patch("builtins.open")
    @patch("toml.load", side_effect=Exception("TOML parse error"))
    def test_read_pyproject_config_toml_error(self, mock_toml_load, mock_open):
        """Test TOML parsing error handling"""
        result = read_pyproject_config()

        # Should return fallback config
        assert result["project"]["name"] == "circuit-agent"

    def test_get_agent_config_from_pyproject_with_tool_section(self):
        """Test config extraction with tool.circuit section"""
        mock_config = {
            "project": {
                "name": "default-name",
                "description": "Default Description",
                "version": "1.0.0",
            },
            "tool": {
                "circuit": {
                    "name": "Custom Agent Name",
                    "description": "Custom Agent Description",
                }
            },
        }

        with patch("agent_sdk.utils.read_pyproject_config", return_value=mock_config):
            result = get_agent_config_from_pyproject()

            # Should prefer tool.circuit values over project values
            assert result["title"] == "Custom Agent Name"
            assert result["description"] == "Custom Agent Description"
            assert result["version"] == "1.0.0"

    def test_get_agent_config_from_pyproject_without_tool_section(self):
        """Test config extraction without tool.circuit section"""
        mock_config = {
            "project": {
                "name": "project-name",
                "description": "Project Description",
                "version": "2.0.0",
            }
        }

        with patch("agent_sdk.utils.read_pyproject_config", return_value=mock_config):
            result = get_agent_config_from_pyproject()

            # Should use project values
            assert result["title"] == "project-name"
            assert result["description"] == "Project Description"
            assert result["version"] == "2.0.0"

    def test_get_agent_config_from_pyproject_minimal_config(self):
        """Test config extraction with minimal/missing data"""
        mock_config = {}

        with patch("agent_sdk.utils.read_pyproject_config", return_value=mock_config):
            result = get_agent_config_from_pyproject()

            # Should use default values
            assert result["title"] == "Circuit Agent"
            assert result["description"] == "A Circuit Agent"
            assert result["version"] == "1.0.0"
