# 📖 User Guide - Development Project Manager

A comprehensive guide to using the Development Project Manager effectively.

## 🎯 Getting Started

### **First Launch**
1. **Start the Application**
   ```bash
   python run_gui.py
   ```

2. **Set Projects Directory**
   - The app will prompt you to set your projects directory
   - Choose the folder containing your development projects
   - Default: `~/Projects` (or `C:\Users\YourName\Projects` on Windows)

3. **Initial Scan**
   - The app will automatically scan and analyze your projects
   - This may take a few minutes for large collections
   - Progress is shown in the status bar

### **Understanding the Interface**

#### **Main Window Layout**
```
┌─────────────────────────────────────────────────────────┐
│ 🚀 Development Project Manager                          │
├─────────────────────────────────────────────────────────┤
│ 📊 Projects  │ ✨ Create  │ 📊 Monitoring  │ ⚙️ Settings │
├─────────────────────────────────────────────────────────┤
│ Project Tree View (Left)     │ Project Details (Right)  │
│ ┌─────────────────────────┐  │ ┌─────────────────────┐   │
│ │ 📁 Tools               │  │ │ Project Information │   │
│ │   📁 dev-project-      │  │ │ Health: 85%         │   │
│ │   📁 api-testing-      │  │ │ Type: Python        │   │
│ │   📁 crypto-trading-   │  │ │ Language: Python    │   │
│ │   📁 database-         │  │ │ Status: Active      │   │
│ └─────────────────────────┘  │ └─────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│ Status: 🟢 Ready                                        │
└─────────────────────────────────────────────────────────┘
```

## 🖱️ Navigation & Interaction

### **Project Tree View**

#### **Basic Navigation**
- **Single Click** - Select project
- **Double Click** - Expand/collapse folders
- **Right Click** - Open context menu
- **Ctrl/Cmd + Click** - Multi-select projects

#### **Tree Structure**
```
📁 Collection Folder
├── 📁 Sub-project 1
│   ├── 📁 Nested Project A
│   └── 📁 Nested Project B
├── 📁 Sub-project 2
└── 📁 Sub-project 3
```

#### **Health Indicators**
- **🟢 Green** - Healthy (80-100%)
- **🟡 Yellow** - Warning (60-79%)
- **🔴 Red** - Critical (0-59%)

### **Project Details Panel**

#### **Information Display**
- **Project Name** - Full project name
- **Type** - Project type (Web, Desktop, Mobile, etc.)
- **Language** - Primary programming language
- **Status** - Project status (Active, Inactive, etc.)
- **Health Score** - Overall project health percentage
- **Size** - Project size in human-readable format
- **Modified** - Last modification date

#### **Health Breakdown**
- **Code Quality** - Code structure and best practices
- **Documentation** - README and documentation coverage
- **Testing** - Test coverage and quality
- **Dependencies** - Dependency health and updates
- **Security** - Security best practices
- **Performance** - Build times and optimization

## 🎯 Context Menu Actions

### **📁 Project Management**

#### **Open in Explorer**
- Opens the project folder in your system's file manager
- Works on Windows, macOS, and Linux

#### **Analyze Project**
- Forces a complete re-analysis of the selected project
- Updates health scores and project information
- Useful after making significant changes

#### **Generate Report**
- Creates a comprehensive project report
- Includes health metrics, dependencies, and recommendations
- Exports to a readable format

### **🛠️ Development Tools**

#### **Open in VS Code**
- Launches VS Code with the project folder
- Requires VS Code to be installed and in PATH

#### **Open Terminal**
- Opens a terminal/command prompt in the project directory
- Platform-specific terminal applications

#### **Open in IDE**
- Auto-detects the appropriate IDE based on project type
- Supports VS Code, IntelliJ, and other IDEs

#### **Open in Browser**
- Opens web projects in your default browser
- Looks for common web files (index.html, etc.)

### **📚 Git Operations**

#### **Git Status**
- Shows the current Git repository status
- Displays modified, staged, and untracked files
- Opens in a dialog window

#### **Git Pull**
- Pulls the latest changes from the remote repository
- Updates your local copy with remote changes

#### **Git Push**
- Pushes local changes to the remote repository
- Requires proper Git configuration

#### **Create Branch**
- Creates a new Git branch
- Prompts for branch name
- Switches to the new branch

#### **Git Log**
- Shows the last 10 commits
- Displays commit messages and authors
- Opens in a dialog window

#### **Git Statistics**
- Shows commit count and contributors
- Displays project activity metrics

### **📦 Bulk Operations** (Multi-select)

#### **Bulk Operations Dialog**
- Appears when multiple projects are selected
- Provides batch operations for efficiency

#### **Update All Dependencies**
- Updates dependencies for all selected projects
- Supports npm, pip, and other package managers

#### **Clean All Projects**
- Removes build artifacts and temporary files
- Cleans node_modules, dist, build folders

#### **Run All Tests**
- Executes test suites for all selected projects
- Supports multiple testing frameworks

#### **Generate All Reports**
- Creates reports for all selected projects
- Combines into a single comprehensive report

#### **Export All Projects**
- Exports all selected projects to a single location
- Creates organized export structure

### **🏥 Health & Analysis**

#### **Deep Analysis**
- Performs comprehensive project analysis
- Includes code complexity, dependency health, documentation coverage
- Provides detailed insights and recommendations

#### **Security Scan**
- Scans for common security vulnerabilities
- Checks for hardcoded secrets and sensitive information
- Identifies potential security issues

#### **Performance Check**
- Analyzes project performance metrics
- Checks file sizes, build times, and resource usage
- Provides optimization recommendations

#### **Test Coverage**
- Detects test files and frameworks
- Analyzes test coverage and quality
- Identifies missing test coverage

#### **Dependency Check**
- Analyzes dependency health and updates
- Identifies outdated or vulnerable dependencies
- Provides update recommendations

### **🤖 Automation**

#### **Auto-Update Dependencies**
- Automatically updates project dependencies
- Supports npm, pip, and other package managers
- Handles version conflicts and compatibility

#### **Auto-Cleanup**
- Removes build artifacts and temporary files
- Cleans common build directories
- Frees up disk space

#### **Auto-Generate Docs**
- Generates basic README files for projects
- Creates project documentation templates
- Improves project documentation coverage

#### **Run Tests**
- Executes project test suites
- Supports multiple testing frameworks
- Provides test results and coverage

#### **Build Project**
- Builds projects using appropriate build tools
- Supports npm, maven, gradle, and other build systems
- Handles build errors and warnings

### **🚀 Advanced Features**

#### **Code Quality Analysis**
- Analyzes code quality metrics
- Checks for best practices and standards
- Provides quality improvement suggestions

#### **Performance Profiling**
- Profiles project performance
- Analyzes resource usage and optimization
- Identifies performance bottlenecks

#### **Security Audit**
- Performs comprehensive security audit
- Checks for security best practices
- Identifies security vulnerabilities

#### **Bundle Analysis**
- Analyzes project bundle sizes
- Identifies large dependencies and files
- Provides optimization recommendations

#### **API Documentation**
- Generates API documentation
- Creates endpoint documentation
- Improves API discoverability

## ⚙️ Settings & Configuration

### **Project Settings**

#### **Background Processing**
- **Enabled**: Projects are analyzed in the background
- **Disabled**: All analysis happens immediately
- **Recommendation**: Enable for better performance

#### **Lazy Loading**
- **Enabled**: Projects are loaded on demand
- **Disabled**: All projects are loaded immediately
- **Recommendation**: Enable for large project collections

#### **Cache Management**
- **Clear Cache**: Removes cached project data
- **Cache Location**: `~/.dev-project-manager/cache/`
- **Recommendation**: Clear cache periodically

### **Performance Optimization**

#### **Directory Limits**
- **Max Projects per Scan**: Limit projects scanned at once
- **Max Depth**: Limit directory scanning depth
- **Recommendation**: Adjust based on your system performance

#### **Memory Management**
- **Background Processing**: Reduces memory usage
- **Lazy Loading**: Loads projects on demand
- **Cache Management**: Manages memory usage

## 🎨 Customization

### **Theme Customization**
- **Dark Theme**: Professional dark theme (default)
- **Light Theme**: Light theme option
- **Custom Colors**: Customize color scheme

### **Layout Customization**
- **Resizable Panes**: Adjust pane sizes
- **Column Widths**: Customize tree view columns
- **Window Size**: Remember window size and position

### **Behavior Customization**
- **Auto-Refresh**: Automatically refresh project list
- **Notifications**: Enable/disable notifications
- **Keyboard Shortcuts**: Customize keyboard shortcuts

## 🔧 Troubleshooting

### **Common Issues**

#### **GUI Not Starting**
1. Check Python version (3.8+ required)
2. Verify all dependencies are installed
3. Check for display/graphics issues
4. Try running with `--debug` flag

#### **Projects Not Loading**
1. Verify projects directory path
2. Check file permissions
3. Clear cache and restart
4. Check for corrupted project files

#### **Performance Issues**
1. Enable lazy loading
2. Reduce directory scan limits
3. Clear cache regularly
4. Close unused applications
5. Check system resources

#### **Git Operations Failing**
1. Verify Git is installed
2. Check repository status
3. Ensure proper Git configuration
4. Check network connectivity

#### **Context Menu Not Working**
1. Ensure projects are selected
2. Check for permission issues
3. Verify required tools are installed
4. Try refreshing the project list

### **Debug Mode**
```bash
python run_gui.py --debug
```

### **Cache Management**
- **Clear Cache**: Settings → Clear Cache
- **Cache Location**: `~/.dev-project-manager/cache/`
- **Manual Clear**: Delete cache directory

### **Log Files**
- **Location**: `~/.dev-project-manager/logs/`
- **Level**: Debug, Info, Warning, Error
- **Rotation**: Automatic log rotation

## 📊 Best Practices

### **Project Organization**
1. **Use Clear Naming**: Descriptive project names
2. **Organize by Type**: Group similar projects
3. **Keep README Updated**: Maintain project documentation
4. **Regular Updates**: Keep dependencies updated

### **Health Maintenance**
1. **Regular Analysis**: Run health checks regularly
2. **Address Issues**: Fix health issues promptly
3. **Monitor Trends**: Watch for declining health
4. **Documentation**: Keep documentation current

### **Performance Optimization**
1. **Use Lazy Loading**: For large project collections
2. **Enable Caching**: For faster subsequent loads
3. **Background Processing**: For non-blocking operations
4. **Regular Cleanup**: Clear cache and temporary files

### **Security Best Practices**
1. **Regular Scans**: Run security scans regularly
2. **Update Dependencies**: Keep dependencies current
3. **Secure Configuration**: Use secure configurations
4. **Monitor Vulnerabilities**: Watch for security issues

## 🚀 Advanced Usage

### **Command Line Options**
```bash
python run_gui.py [options]

Options:
  --debug          Enable debug mode
  --config FILE   Use custom config file
  --projects DIR  Set projects directory
  --no-cache      Disable caching
  --help          Show help message
```

### **Configuration File**
```json
{
  "projects_dir": "~/Projects",
  "cache_enabled": true,
  "background_processing": true,
  "lazy_loading": false,
  "max_projects_per_scan": 100,
  "health_check_interval": 3600,
  "theme": "dark",
  "auto_refresh": true
}
```

### **Keyboard Shortcuts**
- **F5**: Refresh project list
- **Ctrl+R**: Refresh project list
- **Ctrl+A**: Select all projects
- **Delete**: Delete selected projects
- **F2**: Rename project
- **Ctrl+C**: Copy project info
- **Ctrl+V**: Paste project info

## 📞 Support & Help

### **Getting Help**
1. **Check Documentation**: Read this guide thoroughly
2. **GitHub Issues**: Report bugs and request features
3. **Community**: Join discussions and get help
4. **Debug Mode**: Use debug mode for troubleshooting

### **Reporting Issues**
1. **Describe the Problem**: Clear description of the issue
2. **Include Steps**: Steps to reproduce the problem
3. **System Information**: OS, Python version, etc.
4. **Log Files**: Include relevant log files

### **Feature Requests**
1. **Describe the Feature**: Clear description of the requested feature
2. **Use Case**: Explain why the feature is needed
3. **Examples**: Provide examples if possible
4. **Priority**: Indicate the importance of the feature

---

**📖 This user guide covers all the features and capabilities of the Development Project Manager. For additional help, check the GitHub repository or create an issue.**
