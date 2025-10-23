# 🔧 Technical Documentation - Development Project Manager

## Architecture Overview

### Core Components
- **`project_manager_gui.py`** - Main GUI application (4,500+ lines)
- **`project_manager.py`** - Core project analysis logic
- **`run_gui.py`** - Application entry point
- **`config.json`** - Configuration settings

### Key Features Implemented
- ✅ **Modern Dark Theme GUI** - Professional styling with ttk.Style
- ✅ **Comprehensive Context Menu** - 50+ right-click actions
- ✅ **Intelligent Project Detection** - 50+ languages and frameworks
- ✅ **Health Scoring System** - Multi-metric project analysis
- ✅ **Hierarchical Project Structure** - Tree view with lazy loading
- ✅ **Performance Optimization** - Caching, background processing
- ✅ **Git Integration** - Full Git workflow support
- ✅ **Bulk Operations** - Multi-project batch processing

### Performance Optimizations
- **Smart Caching** - Intelligent cache with invalidation
- **Lazy Loading** - Load projects on demand
- **Background Processing** - Non-blocking analysis
- **Directory Limits** - Prevent scanning overload
- **Memory Management** - Efficient resource usage

## API Reference

### Main Classes
- **`ProjectManagerGUI`** - Main application class
- **`ProjectManager`** - Core project management logic

### Key Methods
- **`analyze_project()`** - Comprehensive project analysis
- **`_detect_languages()`** - Language detection
- **`_detect_js_frameworks()`** - JavaScript framework detection
- **`show_context_menu()`** - Right-click context menu
- **`refresh_projects()`** - Project list refresh

## Configuration

### config.json Structure
```json
{
  "projects_dir": "~/Projects",
  "cache_enabled": true,
  "background_processing": true,
  "lazy_loading": false,
  "max_projects_per_scan": 100
}
```

## Dependencies
- **tkinter** - GUI framework (Python standard library)
- **pathlib** - Path handling (Python standard library)
- **json** - Configuration (Python standard library)
- **pickle** - Caching (Python standard library)
- **subprocess** - External commands (Python standard library)

## File Structure
```
project-manager/
├── project_manager_gui.py    # Main GUI (4,500+ lines)
├── project_manager.py      # Core logic
├── run_gui.py                # Entry point
├── config.json              # Configuration
├── requirements.txt         # Dependencies
├── README.md               # Main documentation
├── USER_GUIDE.md           # User guide
└── TECHNICAL_DOCS.md       # This file
```

## Development Notes
- **GUI Framework**: Tkinter with ttk.Style for modern theming
- **Project Detection**: File-based analysis with framework detection
- **Caching**: Pickle-based cache with modification time invalidation
- **Performance**: Optimized for large project collections
- **Cross-Platform**: Windows, macOS, Linux support
