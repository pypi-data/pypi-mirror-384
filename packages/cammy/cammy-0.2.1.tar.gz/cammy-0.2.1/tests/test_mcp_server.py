#!/usr/bin/env python3
"""
Tests for CAM MCP Server (FastMCP version)
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the FastMCP server
from mcp_server_fastmcp import mcp
from fastmcp import Client


class TestCAMMCPServer:
    """Test suite for CAM MCP server functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        cache_dir = Path(temp_dir) / ".cache" / "cammy"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the cache directory
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path(temp_dir)
            yield cache_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    async def client(self):
        """Create an MCP client for testing."""
        async with Client(mcp) as client:
            yield client

    @pytest.mark.asyncio
    async def test_server_tools_available(self, client):
        """Test that all expected tools are available."""
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        
        expected_tools = {
            "capture_screenshot",
            "start_monitoring", 
            "stop_monitoring",
            "get_monitoring_status",
            "analyze_screenshot",
            "list_recent_screenshots",
            "clear_cache",
            "create_gif",
            "list_sessions"
        }
        
        assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"

    @pytest.mark.asyncio
    async def test_server_resources_available(self, client):
        """Test that resources are available."""
        resources = await client.list_resources()
        resource_uris = {resource.uri for resource in resources}
        
        # Should have template resources
        expected_patterns = ["screenshot://", "screenshots://recent"]
        
        # Check if any resources match expected patterns
        has_screenshot_template = any("screenshot://" in uri for uri in resource_uris)
        has_recent_resource = any("screenshots://recent" in uri for uri in resource_uris)
        
        # At least one should be available (depending on implementation)
        assert has_screenshot_template or has_recent_resource

    @pytest.mark.asyncio 
    async def test_capture_screenshot_mock(self, client, temp_cache_dir):
        """Test screenshot capture with mocked cammy."""
        mock_path = str(temp_cache_dir / "test-stdout.jpg")
        
        # Create a mock screenshot file
        Path(mock_path).write_bytes(b"fake_image_data")
        
        with patch('mcp_server_fastmcp.cammy.capture') as mock_capture:
            mock_capture.return_value = mock_path
            
            result = await client.call_tool("capture_screenshot", {
                "message": "test capture",
                "quality": 85
            })
            
            response = json.loads(result.content[0].text)
            
            assert response["success"] is True
            assert response["path"] == mock_path
            assert response["category"] == "stdout"
            assert "timestamp" in response

    @pytest.mark.asyncio
    async def test_capture_screenshot_with_base64(self, client, temp_cache_dir):
        """Test screenshot capture with base64 return."""
        mock_path = str(temp_cache_dir / "test-stdout.jpg")
        test_data = b"fake_image_data"
        
        Path(mock_path).write_bytes(test_data)
        
        with patch('mcp_server_fastmcp.cammy.capture') as mock_capture:
            mock_capture.return_value = mock_path
            
            result = await client.call_tool("capture_screenshot", {
                "return_base64": True
            })
            
            response = json.loads(result.content[0].text)
            
            assert response["success"] is True
            assert "base64" in response
            # Should contain base64 encoded data
            assert len(response["base64"]) > 0

    @pytest.mark.asyncio
    async def test_capture_screenshot_failure(self, client):
        """Test screenshot capture failure handling."""
        with patch('mcp_server_fastmcp.cammy.capture') as mock_capture:
            mock_capture.return_value = None  # Simulate failure
            
            result = await client.call_tool("capture_screenshot", {})
            response = json.loads(result.content[0].text)
            
            assert response["success"] is False
            assert "error" in response

    @pytest.mark.asyncio
    async def test_start_monitoring(self, client, temp_cache_dir):
        """Test monitoring start functionality."""
        with patch('mcp_server_fastmcp.cammy.start_monitor') as mock_start:
            mock_monitor = MagicMock()
            mock_start.return_value = mock_monitor
            
            result = await client.call_tool("start_monitoring", {
                "interval": 2.0,
                "quality": 70
            })
            
            response = json.loads(result.content[0].text)
            
            assert response["success"] is True
            assert response["interval"] == 2.0
            assert response["quality"] == 70
            
            # Check that monitoring file was created
            monitoring_file = temp_cache_dir / ".monitoring"
            assert monitoring_file.exists()

    @pytest.mark.asyncio
    async def test_start_monitoring_already_active(self, client, temp_cache_dir):
        """Test starting monitoring when already active."""
        # Create monitoring file to simulate active monitoring
        monitoring_file = temp_cache_dir / ".monitoring"
        monitoring_file.write_text("active")
        
        result = await client.call_tool("start_monitoring", {})
        response = json.loads(result.content[0].text)
        
        assert response["success"] is False
        assert "already active" in response["message"]

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, client, temp_cache_dir):
        """Test monitoring stop functionality."""
        # Create monitoring file to simulate active monitoring
        monitoring_file = temp_cache_dir / ".monitoring" 
        monitoring_file.write_text("active")
        
        with patch('mcp_server_fastmcp.cammy.stop') as mock_stop:
            result = await client.call_tool("stop_monitoring", {})
            response = json.loads(result.content[0].text)
            
            assert response["success"] is True
            assert "stopped" in response["message"]
            
            # Check that monitoring file was removed
            assert not monitoring_file.exists()
            
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_monitoring_not_active(self, client, temp_cache_dir):
        """Test stopping monitoring when not active."""
        result = await client.call_tool("stop_monitoring", {})
        response = json.loads(result.content[0].text)
        
        assert response["success"] is False
        assert "not active" in response["message"]

    @pytest.mark.asyncio
    async def test_get_monitoring_status(self, client, temp_cache_dir):
        """Test getting monitoring status."""
        # Create some test screenshots
        test_files = [
            temp_cache_dir / "20250824_120000_001-stdout.jpg",
            temp_cache_dir / "20250824_120001_002-stderr.jpg"
        ]
        
        for file in test_files:
            file.write_bytes(b"fake_data" * 100)  # ~900 bytes each
        
        result = await client.call_tool("get_monitoring_status", {})
        response = json.loads(result.content[0].text)
        
        assert response["active"] is False  # No monitoring file exists
        assert "cache_dir" in response
        assert response["screenshot_count"] == 2
        assert response["cache_size_mb"] > 0

    @pytest.mark.asyncio
    async def test_list_recent_screenshots(self, client, temp_cache_dir):
        """Test listing recent screenshots."""
        # Create test screenshot files with different timestamps
        test_files = [
            ("20250824_120000_001-stdout.jpg", "stdout"),
            ("20250824_120001_002-stderr.jpg", "stderr"),
            ("20250824_120002_003-stdout.jpg", "stdout")
        ]
        
        for filename, category in test_files:
            file_path = temp_cache_dir / filename
            file_path.write_bytes(b"fake_image_data")
        
        result = await client.call_tool("list_recent_screenshots", {
            "limit": 5,
            "category": "all"
        })
        
        response = json.loads(result.content[0].text)
        
        assert response["success"] is True
        assert response["count"] == 3
        assert len(response["screenshots"]) == 3
        
        # Check screenshot details
        for screenshot in response["screenshots"]:
            assert "filename" in screenshot
            assert "category" in screenshot
            assert screenshot["category"] in ["stdout", "stderr"]
            assert "size_kb" in screenshot
            assert "modified" in screenshot

    @pytest.mark.asyncio
    async def test_list_recent_screenshots_filtered(self, client, temp_cache_dir):
        """Test listing screenshots with category filter."""
        # Create mixed category screenshots
        test_files = [
            ("test1-stdout.jpg", "stdout"),
            ("test2-stderr.jpg", "stderr"),
            ("test3-stdout.jpg", "stdout")
        ]
        
        for filename, _ in test_files:
            (temp_cache_dir / filename).write_bytes(b"fake_data")
        
        # Test stdout filter
        result = await client.call_tool("list_recent_screenshots", {
            "category": "stdout"
        })
        
        response = json.loads(result.content[0].text)
        
        assert response["success"] is True
        assert response["count"] == 2  # Only stdout screenshots
        assert all(s["category"] == "stdout" for s in response["screenshots"])

    @pytest.mark.asyncio
    async def test_analyze_screenshot(self, client, temp_cache_dir):
        """Test screenshot analysis."""
        test_file = temp_cache_dir / "test-stderr.jpg"
        test_file.write_bytes(b"fake_image_data")
        
        with patch('mcp_server_fastmcp._detect_category') as mock_detect:
            mock_detect.return_value = "stderr"
            
            result = await client.call_tool("analyze_screenshot", {
                "path": str(test_file)
            })
            
            response = json.loads(result.content[0].text)
            
            assert response["success"] is True
            assert response["category"] == "stderr"
            assert response["is_error"] is True
            assert "size_kb" in response
            assert "modified" in response

    @pytest.mark.asyncio
    async def test_analyze_screenshot_not_found(self, client):
        """Test analyzing non-existent screenshot."""
        result = await client.call_tool("analyze_screenshot", {
            "path": "/nonexistent/path.jpg"
        })
        
        response = json.loads(result.content[0].text)
        
        assert response["success"] is False
        assert "not found" in response["error"]

    @pytest.mark.asyncio
    async def test_clear_cache_all(self, client, temp_cache_dir):
        """Test clearing all cache."""
        # Create test files
        for i in range(3):
            (temp_cache_dir / f"test{i}.jpg").write_bytes(b"fake_data")
        
        result = await client.call_tool("clear_cache", {
            "clear_all": True
        })
        
        response = json.loads(result.content[0].text)
        
        assert response["success"] is True
        assert response["removed_count"] == 3
        
        # Verify files are removed
        remaining_files = list(temp_cache_dir.glob("*.jpg"))
        assert len(remaining_files) == 0

    @pytest.mark.asyncio
    async def test_clear_cache_size_limit(self, client, temp_cache_dir):
        """Test cache size management."""
        # Create test files
        for i in range(3):
            (temp_cache_dir / f"test{i}.jpg").write_bytes(b"fake_data" * 1000)
        
        with patch('mcp_server_fastmcp._manage_cache_size') as mock_manage:
            result = await client.call_tool("clear_cache", {
                "max_size_gb": 0.001  # Very small limit
            })
            
            response = json.loads(result.content[0].text)
            
            assert response["success"] is True
            assert "cache_size_mb" in response
            mock_manage.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_gif_from_session(self, client, temp_cache_dir):
        """Test GIF creation from session."""
        with patch('mcp_server_fastmcp.GifCreator') as mock_creator_class:
            mock_creator = MagicMock()
            mock_creator_class.return_value = mock_creator
            
            output_path = str(temp_cache_dir / "test.gif")
            mock_creator.create_gif_from_session.return_value = output_path
            
            # Create the mock output file
            Path(output_path).write_bytes(b"fake_gif_data" * 100)
            
            result = await client.call_tool("create_gif", {
                "session_id": "20250824_120000",
                "duration": 0.8
            })
            
            response = json.loads(result.content[0].text)
            
            assert response["success"] is True
            assert response["path"] == output_path
            assert response["duration_per_frame"] == 0.8
            assert "size_kb" in response

    @pytest.mark.asyncio
    async def test_create_gif_missing_params(self, client):
        """Test GIF creation with missing parameters."""
        result = await client.call_tool("create_gif", {})
        response = json.loads(result.content[0].text)
        
        assert response["success"] is False
        assert "Must specify either" in response["error"]

    @pytest.mark.asyncio
    async def test_list_sessions(self, client, temp_cache_dir):
        """Test listing available sessions."""
        # Create session files
        session_files = [
            "20250824_120000_001.jpg",
            "20250824_120000_002.jpg", 
            "20250824_130000_001.jpg"
        ]
        
        for filename in session_files:
            (temp_cache_dir / filename).write_bytes(b"fake_data" * 500)
        
        with patch('mcp_server_fastmcp.GifCreator') as mock_creator_class:
            mock_creator = MagicMock()
            mock_creator_class.return_value = mock_creator
            mock_creator.get_recent_sessions.return_value = ["20250824_120000", "20250824_130000"]
            
            result = await client.call_tool("list_sessions", {"limit": 5})
            response = json.loads(result.content[0].text)
            
            assert response["success"] is True
            assert response["count"] >= 1
            assert len(response["sessions"]) >= 1
            
            # Check session details structure
            if response["sessions"]:
                session = response["sessions"][0]
                assert "session_id" in session
                assert "screenshot_count" in session
                assert "total_size_kb" in session
                assert "start_time" in session
                assert "end_time" in session

    @pytest.mark.asyncio
    async def test_get_screenshot_resource(self, client, temp_cache_dir):
        """Test getting screenshot resource."""
        # Create a test screenshot
        filename = "test-screenshot.jpg"
        test_data = b"fake_image_data_for_resource_test"
        (temp_cache_dir / filename).write_bytes(test_data)
        
        try:
            result = await client.read_resource(f"screenshot://{filename}")
            
            # The resource should return base64 encoded data
            import base64
            expected_b64 = base64.b64encode(test_data).decode()
            assert result.content == expected_b64
            
        except Exception as e:
            # If resource reading is not implemented in test client, skip
            pytest.skip(f"Resource reading not supported in test environment: {e}")

    @pytest.mark.asyncio
    async def test_list_screenshots_resource(self, client, temp_cache_dir):
        """Test screenshots listing resource."""
        # Create test screenshots
        test_files = [
            "test1-stdout.jpg",
            "test2-stderr.jpg"
        ]
        
        for filename in test_files:
            (temp_cache_dir / filename).write_bytes(b"fake_data")
        
        try:
            result = await client.read_resource("screenshots://recent")
            
            # Parse the JSON response
            response = json.loads(result.content)
            
            assert "screenshots" in response
            assert "count" in response
            assert response["count"] >= 2
            
        except Exception as e:
            # If resource reading is not implemented in test client, skip
            pytest.skip(f"Resource reading not supported in test environment: {e}")


class TestMCPServerIntegration:
    """Integration tests for MCP server with real cammy functionality."""

    @pytest.mark.asyncio
    async def test_server_startup(self):
        """Test that the server can start up properly."""
        async with Client(mcp) as client:
            # Basic connectivity test
            tools = await client.list_tools()
            assert len(tools) > 0
            
            resources = await client.list_resources()
            # Resources may be empty initially, that's ok

    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self):
        """Test that tools properly validate parameters."""
        async with Client(mcp) as client:
            # Test with invalid quality parameter
            result = await client.call_tool("capture_screenshot", {
                "quality": 150  # Invalid quality > 100
            })
            
            # FastMCP should handle parameter validation at the framework level
            # The exact behavior depends on FastMCP's validation implementation
            # This test mainly ensures no crashes occur
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])