<!-- ---
!-- Timestamp: 2025-10-17 03:56:02
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/cammy/README.md
!-- --- -->

# CAM - Python Screen Capture with MCP Server Support
*- shared visual context between users and AI agents -*

A lightweight, efficient screen capture library with automatic error detection. **Features full MCP (Model Context Protocol) server integration for seamless AI assistant workflows.** Optimized for WSL2 to capture Windows host screens.

## 🎬 Live Demos & Screenshots

### 📸 Single Screenshot Capture
<img src="docs/screenshots/demo-single-capture.jpg" width="400" alt="Demo Screenshot">

*Example of CAM's single screenshot capture functionality with custom message*

| Feature Demo | Description |
|--------------|-------------|
| <details><summary><strong>🔄 Real Monitoring Session</strong></summary><img src="docs/screenshots/monitoring-session-demo.gif" width="280" alt="Real Monitoring Demo"><br><em>Real GIF from actual monitoring session</em><br><br><strong>Session Details:</strong><br>• 30s monitoring interval<br>• 11 automatic captures<br>• 2.8MB optimized GIF<br>• JPEG compression<br>• Timestamp-based naming</details> | <details><summary><strong>📋 Workflow Documentation</strong></summary><img src="docs/screenshots/workflow_demo.gif" width="280" alt="Workflow Demo"><br><em>Step-by-step process capture (230KB, 7 frames)</em><br><br><strong>Features:</strong><br>• Sequential capture<br>• Auto file organization<br>• Visual documentation<br>• Efficient compression</details> |
| <details><summary><strong>🖥️ Continuous Monitoring</strong></summary><img src="docs/screenshots/monitoring_demo.gif" width="280" alt="Monitoring Demo"><br><em>Real-time progress tracking (429KB, 12 frames)</em><br><br><strong>Technical:</strong><br>• Real-time monitoring<br>• Progress visualization<br>• Frame compression<br>• Session management</details> | <details><summary><strong>🚨 Error Detection</strong></summary><img src="docs/screenshots/error_detection_demo.gif" width="280" alt="Error Detection Demo"><br><em>Context-aware categorization (322KB, 5 frames)</em><br><br><strong>Smart Features:</strong><br>• Error detection<br>• stdout/stderr tagging<br>• Exception integration<br>• Intelligent naming</details> |


## Installation

### From PyPI (Recommended)
```bash
pip install cammy
# pip install cammy[full] # For full features including mss and Pillow support:
```

### From Source
```bash
git clone https://github.com/ywatanabe1989/cammy.git
cd cammy

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 🐍 Python API - Beautiful Simplicity

```python
import cammy

# Core functions
cammy.snap()                          # Capture single screenshot
cammy.start()                        # Start monitoring
cammy.stop()                         # Stop monitoring
cammy.create_gif_from_latest_session()  # Create GIF summary

# Multi-desktop features
cammy.get_info()           # List all monitors and windows
cammy.snap(monitor_id=1)             # Capture specific monitor
cammy.snap(capture_all=True)         # Capture all monitors
cammy.start(monitor_id=0)           # Monitor specific screen
```

<details>
<summary><strong>📋 Detailed Usages in Python</strong></summary>

### 🐛 Debug Your Code Visually

```python
import cammy

def process_data(df):
    cammy.snap("before transformation")
    df = df.transform(complex_operation)
    cammy.snap("after transformation")
    return df
```

### 🚨 Automatic Error Screenshots

```python
import cammy

try:
    selenium_driver.click(button)
    api_response = fetch_data()
except Exception as e:
    cammy.snap()  # Auto-adds -stderr suffix
    raise
```

### 🔍 Monitor Long-Running Processes

```python
import cammy

cammy.start()  # Start taking screenshots every second
train_model()  # Your long operation
cammy.stop()

# Multi-monitor monitoring
cammy.start(capture_all=True, interval=2.0)  # All monitors, 2s interval
```

### 🎬 Create GIF Summaries

```python
import cammy

# Method 1: Use Context Manager
with cammy.session() as session:
    # ... your process ...

# Method 2: Start/Stop Manually
cammy.start()
# ... your process ...  
cammy.stop()
cammy.create_gif_from_latest_session()
# 📹 GIF created: ~/.cache/cammy/20250823_104523_summary.gif
```

## Configuration

All configuration through function parameters - no config files needed!

```python
cammy.start(
    output_dir="~/screenshots",  # Where to save
    interval=2.0,                # Seconds between captures
    quality=85,                  # JPEG quality (1-100)
    verbose=False,               # Silent mode
    monitor_id=0,                # Specific monitor (0-based)
    capture_all=False            # Capture all monitors
)
```

### 🖥️ Multi-Desktop & Monitor Features

```python
import cammy

# Enumerate available monitors and windows
info = cammy.get_info()
print(f"Monitors: {info['Monitors']['Count']}")
print(f"Windows: {info['Windows']['VisibleCount']}")

# Capture specific monitor
cammy.snap(monitor_id=0)    # Primary monitor
cammy.snap(monitor_id=1)    # Secondary monitor

# Capture all monitors combined
cammy.snap(capture_all=True)

# Capture specific window by handle
windows = info['Windows']['Details']
if windows:
    handle = windows[0]['Handle']
    path = cammy.capture_window(handle)
    print(f"Captured window: {path}")

# Monitor specific screen continuously
cammy.start(monitor_id=1, interval=3.0)
```

## File Structure

```
~/.cache/cammy/
├── 20250823_104523-message-stdout.jpg    # Normal capture
├── 20250823_104525-error-stderr.jpg      # Error capture  
└── 20250823_104530_0001_*.jpg            # Monitoring mode

Cache automatically managed (1GB default limit, oldest files removed)
```

## Requirements

- Python 3.7+
- WSL environment (for Windows capture)
- PowerShell access to Windows host

Optional:
- `Pillow` - JPEG compression (recommended)
- `mss` - Cross-platform fallback

</details>

<details>
<summary><strong>🤖 MCP Server Integration</strong></summary>

- **AI Assistant Ready** - Built-in MCP server for Claude Code and other AI assistants
- **Direct Screenshot Control** - AI can capture, monitor, and analyze screenshots programmatically
- **Automated Workflows** - Perfect for debugging, documentation, and monitoring tasks
- **Real-time Interaction** - AI assistants can respond to visual changes instantly

### Setup - Just Add JSON!

<!-- ```json
 !-- // Add to your Claude Code settings
 !-- {
 !--   "mcpServers": {
 !--     "cammy": {
 !--       "command": "python", 
 !--       "args": ["/path/to/cammy/mcp_server_cammy.py"]
 !--     }
 !--   }
 !-- }
 !-- ``` -->
``` json
// Add to your Claude Code settings
{
  "mcpServers": {
    "cammy": {
      "command": "python", 
      "args": ["-m", "cammy", "--mcp"]
    }
  }
}
```

### Available MCP Tools

**Core Capture:**
- `capture_screenshot` - Take single screenshots with custom messages
- `start_monitoring` / `stop_monitoring` - Continuous monitoring at configurable intervals
- `get_monitoring_status` - Check current monitoring status

**Analysis & Management:**
- `analyze_screenshot` - AI-powered error detection and categorization
- `list_recent_screenshots` - Browse capture history by category (stdout/stderr)
- `clear_cache` - Manage screenshot cache size

**Advanced Features:**
- `create_gif` - Generate animated summaries from monitoring sessions
- `list_sessions` - List available sessions for GIF creation

</details>


## Use Cases & Examples

### 📸 **Essential Use Cases**
- **Debug visually** - Capture before/after states during development
- **Monitor processes** - Continuous screenshots during long operations
- **Document workflows** - Step-by-step visual documentation
- **Error analysis** - Automatic error categorization and screenshots
- **Multi-monitor setup** - Capture specific monitors or all screens simultaneously
- **Window enumeration** - List and target specific application windows
- **AI-powered automation** - Let AI assistants capture and analyze screens via MCP integration


## Platform Support

| Platform | Support | Notes |
|----------|---------|-------|
| **WSL → Windows** | ✅ Full | Primary focus - DPI-aware, multi-monitor |
| Linux (X11) | ⚠️ Limited | Falls back to mss/scrot |
| macOS | ⚠️ Limited | Requires mss library |
| Windows Native | ❌ | Not implemented |
| Linux (Wayland) | ❌ | Not supported |


## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact
Yusuke.Watanabe@scitex.ai

<!-- EOF -->