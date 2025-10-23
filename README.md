# 🚀 Development Project Manager

A powerful, modern GUI application for managing and analyzing development projects with advanced features, intelligent project detection, and comprehensive development tools integration.

![Project Manager](https://img.shields.io/badge/Project%20Manager-v2.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## ✨ Features

### 🎯 **Core Project Management**
- **Intelligent Project Detection** - Automatically discovers and analyzes projects
- **Multi-Language Support** - Detects 50+ programming languages and frameworks
- **Hierarchical Project Structure** - Tree-view with expandable folders
- **Project Health Scoring** - Comprehensive health analysis with detailed metrics
- **Smart Caching System** - Fast loading with intelligent cache management

### 🛠️ **Development Tools Integration**
- **IDE Integration** - Open projects in VS Code, IntelliJ, and other IDEs
- **Terminal Integration** - Open terminal in project directories
- **Git Operations** - Full Git workflow support (status, pull, push, branches)
- **File Explorer** - Quick access to project files
- **Browser Integration** - Open web projects in browser

### 📊 **Advanced Analytics & Reporting**
- **Project Analytics** - Detailed project metrics and insights
- **Health Monitoring** - Real-time project health tracking
- **Performance Analysis** - Code quality and performance metrics
- **Security Scanning** - Automated security vulnerability detection
- **Dependency Analysis** - Dependency health and update management

### 🤖 **Automation & Workflow**
- **Bulk Operations** - Multi-project operations and batch processing
- **Auto-Update Dependencies** - Smart dependency management
- **Auto-Generate Documentation** - Automated README generation
- **Test Execution** - Run tests across multiple projects
- **Build Automation** - Automated project building

### 🎨 **Modern User Interface**
- **Dark Theme** - Professional dark theme with modern styling
- **Resizable Panes** - Flexible layout with resizable sections
- **Context Menus** - Right-click context menus with 50+ actions
- **Multi-Selection** - Select and operate on multiple projects
- **Responsive Design** - Optimized for different screen sizes

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git (for Git operations)
- Your preferred IDE (VS Code, IntelliJ, etc.)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/N0L0g1c/project-manager.git
cd project-manager
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python run_gui.py
```

### First Time Setup

1. **Configure Projects Directory:**
   - The app will prompt you to set your projects directory
   - Default: `~/Projects` (or `C:\Users\YourName\Projects` on Windows)

2. **Initial Project Scan:**
   - The app will automatically scan and analyze your projects
   - This may take a few minutes for large project collections

3. **Explore Features:**
   - Right-click on projects for context menus
   - Use the tree view to navigate hierarchical projects
   - Check the health scores and project details

## 📖 User Guide

### 🎯 **Main Interface**

#### **Project Tree View**
- **Hierarchical Display** - Projects organized in expandable tree structure
- **Health Indicators** - Color-coded health scores (🟢 Healthy, 🟡 Warning, 🔴 Critical)
- **Multi-Selection** - Hold Ctrl/Cmd to select multiple projects
- **Quick Actions** - Double-click to expand/collapse folders

#### **Project Details Panel**
- **Comprehensive Information** - Project type, language, health, size, and modification date
- **Health Breakdown** - Detailed health analysis with specific metrics
- **Framework Detection** - Automatically detected frameworks and technologies
- **Multi-Language Support** - Shows all detected languages in multi-language projects

### 🖱️ **Right-Click Context Menu**

#### **📁 Project Management**
- **Open in Explorer** - Open project in file manager
- **Analyze Project** - Force re-analysis of selected projects
- **Generate Report** - Create comprehensive project reports

#### **🛠️ Development Tools**
- **Open in VS Code** - Launch VS Code with project
- **Open Terminal** - Terminal in project directory
- **Open in IDE** - Auto-detect and open in appropriate IDE
- **Open in Browser** - For web projects

#### **📚 Git Operations**
- **Git Status** - Show repository status
- **Git Pull** - Pull latest changes
- **Git Push** - Push changes
- **Create Branch** - Create new branches
- **Git Log** - View commit history
- **Git Statistics** - Commit counts and contributors

#### **📦 Bulk Operations** (Multi-select)
- **Update All Dependencies** - Batch dependency updates
- **Clean All Projects** - Remove build artifacts
- **Run All Tests** - Batch test execution
- **Generate All Reports** - Bulk reporting
- **Export All Projects** - Batch export

#### **🏥 Health & Analysis**
- **Deep Analysis** - Comprehensive project analysis
- **Security Scan** - Security vulnerability detection
- **Performance Check** - Performance metrics
- **Test Coverage** - Test file detection
- **Dependency Check** - Dependency health

#### **🤖 Automation**
- **Auto-Update Dependencies** - Smart dependency updates
- **Auto-Cleanup** - Remove build artifacts
- **Auto-Generate Docs** - Generate README files
- **Run Tests** - Execute test suites
- **Build Project** - Build projects

#### **🚀 Advanced Features**
- **Code Quality Analysis** - Code quality metrics
- **Performance Profiling** - Performance analysis
- **Security Audit** - Security assessment
- **Bundle Analysis** - Bundle size analysis
- **API Documentation** - Generate API docs

### ⚙️ **Settings & Configuration**

#### **Project Settings**
- **Background Processing** - Enable/disable background analysis
- **Lazy Loading** - Enable/disable lazy loading for performance
- **Cache Management** - Clear cache and manage storage
- **Directory Settings** - Configure project directories

#### **Performance Optimization**
- **Smart Caching** - Intelligent cache management
- **Lazy Loading** - Load projects on demand
- **Background Processing** - Non-blocking analysis
- **Memory Management** - Efficient resource usage

## 🔧 Advanced Features

### 🧠 **Intelligent Project Detection**

#### **Supported Project Types**
- **Web Applications** - React, Vue, Angular, Next.js, Nuxt
- **Backend Services** - Node.js, Python, Java, C#, Go
- **Mobile Apps** - React Native, Flutter, Xamarin
- **Desktop Applications** - Electron, Tauri, Qt
- **Data Science** - Jupyter, R, Python ML
- **DevOps** - Docker, Kubernetes, CI/CD
- **Documentation** - GitBook, Docusaurus, MkDocs

#### **Framework Detection**
- **Frontend**: React, Vue, Angular, Svelte, Astro
- **Backend**: Express, FastAPI, Django, Spring, ASP.NET
- **Mobile**: React Native, Flutter, Ionic
- **Build Tools**: Webpack, Vite, Rollup, Parcel
- **Testing**: Jest, Mocha, Pytest, JUnit
- **Styling**: Tailwind, Bootstrap, Material-UI

### 📊 **Health Scoring System**

#### **Health Metrics**
- **Code Quality** - Code structure and best practices
- **Documentation** - README, comments, and docs coverage
- **Testing** - Test coverage and quality
- **Dependencies** - Dependency health and updates
- **Security** - Security best practices and vulnerabilities
- **Performance** - Build times and optimization
- **Maintenance** - Recent activity and updates

#### **Health Categories**
- **🟢 Healthy (80-100%)** - Excellent project health
- **🟡 Warning (60-79%)** - Good with some issues
- **🔴 Critical (0-59%)** - Needs attention

### 🚀 **Performance Features**

#### **Optimization Techniques**
- **Smart Caching** - Intelligent cache with invalidation
- **Lazy Loading** - Load projects on demand
- **Background Processing** - Non-blocking operations
- **Memory Management** - Efficient resource usage
- **Directory Limits** - Prevent scanning overload

#### **Large Project Support**
- **Hierarchical Loading** - Load projects in hierarchy
- **Batch Processing** - Process multiple projects efficiently
- **Progress Tracking** - Real-time progress updates
- **Error Recovery** - Graceful error handling

## 🛠️ Development

### **Project Structure**
```
project-manager/
├── project_manager_gui.py    # Main GUI application
├── project_manager.py       # Core project management logic
├── run_gui.py                # Application entry point
├── config.json              # Configuration settings
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### **Configuration**

#### **config.json**
```json
{
  "projects_dir": "~/Projects",
  "cache_enabled": true,
  "background_processing": true,
  "lazy_loading": false,
  "max_projects_per_scan": 100,
  "health_check_interval": 3600
}
```

### **Adding New Features**

#### **Context Menu Actions**
1. Add new method to `ProjectManagerGUI` class
2. Add menu item to `show_context_menu` method
3. Implement the functionality
4. Add error handling and user feedback

#### **Project Analysis**
1. Extend `analyze_project` method
2. Add new detection logic
3. Update health scoring
4. Add to project details display

## 📋 Requirements

### **System Requirements**
- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 100MB for application, additional space for cache

### **Dependencies**
```
tkinter          # GUI framework (included with Python)
pathlib          # Path handling (included with Python)
json             # Configuration (included with Python)
pickle           # Caching (included with Python)
subprocess       # External commands (included with Python)
```

### **Optional Dependencies**
- **Git** - For Git operations
- **Node.js** - For JavaScript project analysis
- **Python pip** - For Python project analysis
- **IDE** - VS Code, IntelliJ, etc. for IDE integration

## 🐛 Troubleshooting

### **Common Issues**

#### **GUI Not Starting**
- Check Python version (3.8+ required)
- Verify all dependencies are installed
- Check for display/graphics issues

#### **Projects Not Loading**
- Verify projects directory path
- Check file permissions
- Clear cache and restart

#### **Performance Issues**
- Enable lazy loading
- Reduce directory scan limits
- Clear cache regularly
- Close unused applications

#### **Git Operations Failing**
- Verify Git is installed
- Check repository status
- Ensure proper Git configuration

### **Debug Mode**
```bash
python run_gui.py --debug
```

### **Cache Management**
- Clear cache: Settings → Clear Cache
- Cache location: `~/.dev-project-manager/cache/`
- Manual cache clear: Delete cache directory

## 🤝 Contributing

### **How to Contribute**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### **Development Setup**
```bash
git clone https://github.com/N0L0g1c/project-manager.git
cd project-manager
pip install -r requirements.txt
python run_gui.py
```

### **Code Style**
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Include error handling

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Tkinter** - GUI framework
- **Python Community** - For excellent libraries and tools
- **Open Source Projects** - For inspiration and best practices
- **Contributors** - For feedback and improvements

## 📞 Support

### **Getting Help**
- **Issues**: [GitHub Issues](https://github.com/N0L0g1c/project-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/N0L0g1c/project-manager/discussions)
- **Documentation**: [Wiki](https://github.com/N0L0g1c/project-manager/wiki)

### **Feature Requests**
- Submit feature requests via GitHub Issues
- Include use case and expected behavior
- Provide examples if possible

---

**🚀 Development Project Manager - Manage your projects like a pro!**