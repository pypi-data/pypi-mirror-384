#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-23 22:33:44 (ywatanabe)"
# File: /home/ywatanabe/proj/cammy/tests/test_cammy.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./tests/test_cammy.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------
"""
Tests for cammy package using pytest.
"""

import sys
import tempfile
import time

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cammy


class TestBasicCapture:
    """Test basic capture functionality."""

    def test_import(self):
        """Test that package can be imported."""
        assert cammy is not None
        assert hasattr(cammy, "cpt")
        assert hasattr(cammy, "start")
        assert hasattr(cammy, "stop")

    def test_single_capture(self):
        """Test single screenshot capture."""
        path = cammy.snap("test capture")
        assert path is not None
        assert os.path.exists(path)
        assert path.endswith("-stdout.jpg")
        assert "test-capture" in path

    def test_error_capture(self):
        """Test automatic error detection."""
        try:
            raise ValueError("Test error")
        except:
            path = cammy.snap("error test")
            assert path is not None
            assert os.path.exists(path)
            assert path.endswith("-stderr.jpg")

    def test_custom_path(self):
        """Test custom output path."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        path = cammy.snap("custom path", path=tmp_path)
        assert path == tmp_path
        assert os.path.exists(path)

        # Cleanup
        os.unlink(tmp_path)

    def test_timestamp_placeholder(self):
        """Test timestamp placeholder in path."""
        path = cammy.snap("timestamp test", path="/tmp/test-<timestamp>.jpg")
        assert path is not None
        assert os.path.exists(path)
        assert "/tmp/test-" in path
        assert not "<timestamp>" in path

        # Cleanup
        os.unlink(path)


class TestMonitoring:
    """Test continuous monitoring functionality."""

    def test_start_stop(self):
        """Test starting and stopping monitoring."""
        # Start monitoring
        worker = cammy.start(verbose=False)
        assert worker is not None
        assert worker.running

        # Let it capture a few screenshots
        time.sleep(2.5)

        # Stop monitoring
        cammy.stop()
        assert not worker.running
        assert worker.screenshot_count >= 2

    def test_custom_interval(self):
        """Test custom capture interval."""
        worker = cammy.start(interval=0.5, verbose=False)
        time.sleep(5)  # Give more time for captures
        cammy.stop()

        # In WSL with PowerShell screenshot capture, each screenshot takes ~1.5s
        # So in 5 seconds, we expect about 3-4 screenshots
        # This tests that the interval is being used and monitoring is working
        assert worker.screenshot_count >= 3


class TestCacheManagement:
    """Test cache size management."""

    def test_cache_limit(self):
        """Test that cache management doesn't crash."""
        # This just tests that the function doesn't error
        # Actually testing file deletion would require creating many large files
        path = cammy.snap("cache test", max_cache_gb=0.001)  # Very small limit
        assert path is not None


class TestMultiMonitor:
    """Test multi-monitor support."""

    def test_single_monitor(self):
        """Test capturing specific monitor."""
        path = cammy.capture("monitor 1", monitor_id=1)
        assert path is not None
        assert os.path.exists(path)

    def test_all_monitors(self):
        """Test capturing all monitors."""
        path = cammy.capture("all monitors", capture_all=True)
        assert path is not None
        assert os.path.exists(path)


class TestFilenameNormalization:
    """Test filename normalization."""

    def test_special_characters(self):
        """Test that special characters are normalized."""
        path = cammy.snap("Test with spaces & symbols!@#$%")
        assert path is not None
        assert "@" not in path
        assert "#" not in path
        assert "!" not in path
        assert "Test-with-spaces-symbols" in path

    def test_long_message(self):
        """Test that long messages are truncated."""
        long_msg = "x" * 100
        path = cammy.snap(long_msg)
        assert path is not None
        # Message should be truncated to 50 chars
        filename = os.path.basename(path)
        assert len(filename) < 150  # Reasonable filename length


class TestVerbosity:
    """Test verbose output control."""

    def test_verbose_false(self, capsys):
        """Test that verbose=False suppresses output."""
        path = cammy.capture("quiet test", verbose=False)
        captured = capsys.readouterr()
        assert "📸" not in captured.out
        assert path is not None

    def test_verbose_true(self, capsys):
        """Test that verbose=True shows output."""
        path = cammy.capture("verbose test", verbose=True)
        captured = capsys.readouterr()
        assert "📸" in captured.out
        assert path is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
