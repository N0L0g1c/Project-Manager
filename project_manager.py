#!/usr/bin/env python3
"""
Development Project Manager
A comprehensive tool for managing multiple development projects with automated setup,
monitoring, and maintenance capabilities.
"""

import os
import sys
import json
import yaml
import subprocess
import shutil
import time
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import logging
from dataclasses import dataclass, asdict
import psutil
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import print as rprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Project:
    name: str
    path: str
    type: str
    language: str
    framework: str
    status: str
    last_modified: str
    size: str
    dependencies: List[str]
    git_remote: Optional[str]
    health_score: int
    issues: List[str]
    notes: str

@dataclass
class ProjectTemplate:
    name: str
    type: str
    language: str
    framework: str
    setup_commands: List[str]
    dependencies: List[str]
    config_files: Dict[str, str]
    description: str

class ProjectManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.console = Console()
        self.projects = []
        self.templates = []
        self.config = self.load_config()
        self.setup_directories()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        default_config = {
            "projects_dir": os.path.expanduser("~/Projects"),
            "templates_dir": os.path.expanduser("~/ProjectTemplates"),
            "backup_dir": os.path.expanduser("~/ProjectBackups"),
            "monitoring": {
                "enabled": True,
                "check_interval": 300,
                "health_threshold": 70
            },
            "git": {
                "auto_commit": True,
                "commit_message": "Auto-commit: {timestamp}",
                "push_on_save": False
            },
            "backup": {
                "enabled": True,
                "frequency": "daily",
                "retention_days": 30
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def setup_directories(self):
        """Create necessary directories"""
        dirs = [
            self.config["projects_dir"],
            self.config["templates_dir"],
            self.config["backup_dir"]
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def scan_projects(self) -> List[Project]:
        """Scan for existing projects"""
        projects = []
        projects_dir = Path(self.config["projects_dir"])
        
        if not projects_dir.exists():
            return projects
        
        for project_path in projects_dir.iterdir():
            if project_path.is_dir():
                try:
                    project = self.analyze_project(project_path)
                    if project:
                        projects.append(project)
                except Exception as e:
                    logger.error(f"Error analyzing project {project_path}: {e}")
        
        self.projects = projects
        return projects
    
    def analyze_project(self, project_path: Path) -> Optional[Project]:
        """Analyze a project directory and extract information"""
        try:
            # Basic project info
            name = project_path.name
            path = str(project_path)
            
            # Detect project type and language
            project_type, language, framework = self.detect_project_type(project_path)
            
            # Get file stats
            stat = project_path.stat()
            last_modified = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
            size = self.get_directory_size(project_path)
            
            # Check git status
            git_remote = self.get_git_remote(project_path)
            
            # Analyze dependencies
            dependencies = self.get_dependencies(project_path, language)
            
            # Calculate health score
            health_score = self.calculate_health_score(project_path, language)
            
            # Check for issues
            issues = self.check_project_issues(project_path, language)
            
            # Get project status
            status = self.get_project_status(project_path)
            
            return Project(
                name=name,
                path=path,
                type=project_type,
                language=language,
                framework=framework,
                status=status,
                last_modified=last_modified,
                size=size,
                dependencies=dependencies,
                git_remote=git_remote,
                health_score=health_score,
                issues=issues,
                notes=""
            )
        except Exception as e:
            logger.error(f"Error analyzing project {project_path}: {e}")
            return None
    
    def detect_project_type(self, project_path: Path) -> tuple:
        """Detect project type, language, and framework"""
        # Check for common files
        files_to_check = {
            'package.json': ('nodejs', 'javascript', 'node'),
            'requirements.txt': ('python', 'python', 'flask'),
            'Cargo.toml': ('rust', 'rust', 'cargo'),
            'go.mod': ('go', 'go', 'go'),
            'pom.xml': ('java', 'java', 'maven'),
            'composer.json': ('php', 'php', 'composer'),
            'Gemfile': ('ruby', 'ruby', 'bundler'),
            'Dockerfile': ('docker', 'docker', 'docker'),
            'docker-compose.yml': ('docker', 'docker', 'docker-compose'),
            'Makefile': ('c', 'c', 'make'),
            'CMakeLists.txt': ('cpp', 'cpp', 'cmake')
        }
        
        for file_name, (project_type, language, framework) in files_to_check.items():
            if (project_path / file_name).exists():
                return project_type, language, framework
        
        # Check for common directories
        if (project_path / 'src').exists():
            return 'generic', 'unknown', 'unknown'
        
        return 'unknown', 'unknown', 'unknown'
    
    def get_directory_size(self, path: Path) -> str:
        """Get human-readable directory size"""
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        # Convert to human readable
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024.0:
                return f"{total_size:.1f} {unit}"
            total_size /= 1024.0
        return f"{total_size:.1f} TB"
    
    def get_git_remote(self, project_path: Path) -> Optional[str]:
        """Get git remote URL"""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def get_dependencies(self, project_path: Path, language: str) -> List[str]:
        """Get project dependencies based on language"""
        dependencies = []
        
        if language == 'javascript':
            package_json = project_path / 'package.json'
            if package_json.exists():
                try:
                    with open(package_json) as f:
                        data = json.load(f)
                    dependencies = list(data.get('dependencies', {}).keys())
                except Exception:
                    pass
        
        elif language == 'python':
            requirements_txt = project_path / 'requirements.txt'
            if requirements_txt.exists():
                try:
                    with open(requirements_txt) as f:
                        dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                except Exception:
                    pass
        
        return dependencies[:10]  # Limit to first 10 dependencies
    
    def calculate_health_score(self, project_path: Path, language: str) -> int:
        """Calculate project health score (0-100)"""
        score = 100
        
        # Check for common issues
        issues = []
        
        # Check for README
        if not (project_path / 'README.md').exists():
            score -= 10
            issues.append("Missing README.md")
        
        # Check for .gitignore
        if not (project_path / '.gitignore').exists():
            score -= 5
            issues.append("Missing .gitignore")
        
        # Check for tests
        test_dirs = ['tests', 'test', '__tests__', 'spec']
        has_tests = any((project_path / test_dir).exists() for test_dir in test_dirs)
        if not has_tests:
            score -= 15
            issues.append("No test directory found")
        
        # Check for documentation
        doc_dirs = ['docs', 'documentation', 'doc']
        has_docs = any((project_path / doc_dir).exists() for doc_dir in doc_dirs)
        if not has_docs:
            score -= 5
            issues.append("No documentation directory")
        
        # Check for large files
        large_files = []
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                large_files.append(file_path.name)
        
        if large_files:
            score -= 10
            issues.append(f"Large files found: {', '.join(large_files[:3])}")
        
        return max(0, score)
    
    def check_project_issues(self, project_path: Path, language: str) -> List[str]:
        """Check for common project issues"""
        issues = []
        
        # Check for common problems
        if not (project_path / 'README.md').exists():
            issues.append("Missing README.md")
        
        if not (project_path / '.gitignore').exists():
            issues.append("Missing .gitignore")
        
        # Check for node_modules in git
        if (project_path / 'node_modules').exists() and (project_path / '.git').exists():
            issues.append("node_modules should be in .gitignore")
        
        # Check for Python cache files
        if language == 'python':
            cache_dirs = ['__pycache__', '.pytest_cache']
            for cache_dir in cache_dirs:
                if (project_path / cache_dir).exists():
                    issues.append(f"Python cache directory found: {cache_dir}")
        
        return issues
    
    def get_project_status(self, project_path: Path) -> str:
        """Get project status (active, inactive, etc.)"""
        # Check last modification time
        stat = project_path.stat()
        last_modified = datetime.datetime.fromtimestamp(stat.st_mtime)
        days_since_modified = (datetime.datetime.now() - last_modified).days
        
        if days_since_modified < 7:
            return "Active"
        elif days_since_modified < 30:
            return "Recent"
        elif days_since_modified < 90:
            return "Inactive"
        else:
            return "Stale"
    
    def create_project(self, name: str, template: str = None, language: str = None) -> bool:
        """Create a new project"""
        try:
            project_path = Path(self.config["projects_dir"]) / name
            
            if project_path.exists():
                self.console.print(f"[red]Project '{name}' already exists![/red]")
                return False
            
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize git
            subprocess.run(['git', 'init'], cwd=project_path, check=True)
            
            # Create basic files
            self.create_basic_files(project_path, name, language)
            
            # Apply template if specified
            if template:
                self.apply_template(project_path, template)
            
            self.console.print(f"[green]Project '{name}' created successfully![/green]")
            return True
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            self.console.print(f"[red]Error creating project: {e}[/red]")
            return False
    
    def create_basic_files(self, project_path: Path, name: str, language: str = None):
        """Create basic project files"""
        # Create README.md
        readme_content = f"""# {name}

## Description
{name} project

## Setup
\`\`\`bash
# Install dependencies
# Add setup instructions here

# Run the project
# Add run instructions here
\`\`\`

## Development
\`\`\`bash
# Development commands
# Add development instructions here
\`\`\`
"""
        with open(project_path / 'README.md', 'w') as f:
            f.write(readme_content)
        
        # Create .gitignore
        gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Build
dist/
build/
*.egg-info/
"""
        with open(project_path / '.gitignore', 'w') as f:
            f.write(gitignore_content)
        
        # Create language-specific files
        if language == 'python':
            self.create_python_project(project_path, name)
        elif language == 'javascript':
            self.create_javascript_project(project_path, name)
        elif language == 'rust':
            self.create_rust_project(project_path, name)
    
    def create_python_project(self, project_path: Path, name: str):
        """Create Python project structure"""
        # Create main Python file
        main_py = f"""#!/usr/bin/env python3
\"\"\"
{name} - Main module
\"\"\"

def main():
    print("Hello from {name}!")

if __name__ == "__main__":
    main()
"""
        with open(project_path / f"{name}.py", 'w') as f:
            f.write(main_py)
        
        # Create requirements.txt
        with open(project_path / 'requirements.txt', 'w') as f:
            f.write("# Add your dependencies here\n")
        
        # Create setup.py
        setup_py = f"""from setuptools import setup, find_packages

setup(
    name="{name}",
    version="0.1.0",
    description="A Python project",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.7",
)
"""
        with open(project_path / 'setup.py', 'w') as f:
            f.write(setup_py)
    
    def create_javascript_project(self, project_path: Path, name: str):
        """Create JavaScript project structure"""
        # Create package.json
        package_json = {
            "name": name,
            "version": "1.0.0",
            "description": f"A JavaScript project: {name}",
            "main": "index.js",
            "scripts": {
                "start": "node index.js",
                "dev": "node index.js",
                "test": "echo \"Error: no test specified\" && exit 1"
            },
            "keywords": [],
            "author": "Your Name",
            "license": "MIT"
        }
        
        with open(project_path / 'package.json', 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Create index.js
        index_js = f"""// {name} - Main entry point

console.log('Hello from {name}!');

// Add your code here
"""
        with open(project_path / 'index.js', 'w') as f:
            f.write(index_js)
    
    def create_rust_project(self, project_path: Path, name: str):
        """Create Rust project structure"""
        # Create Cargo.toml
        cargo_toml = f"""[package]
name = "{name}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
        with open(project_path / 'Cargo.toml', 'w') as f:
            f.write(cargo_toml)
        
        # Create src directory and main.rs
        src_dir = project_path / 'src'
        src_dir.mkdir(exist_ok=True)
        
        main_rs = f"""fn main() {{
    println!("Hello from {name}!");
}}
"""
        with open(src_dir / 'main.rs', 'w') as f:
            f.write(main_rs)
    
    def apply_template(self, project_path: Path, template_name: str):
        """Apply a project template"""
        # This would load and apply a template
        # For now, just log the action
        logger.info(f"Applying template {template_name} to {project_path}")
    
    def list_projects(self):
        """List all projects with details"""
        projects = self.scan_projects()
        
        if not projects:
            self.console.print("[yellow]No projects found![/yellow]")
            return
        
        # Create table
        table = Table(title="Development Projects")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Language", style="green")
        table.add_column("Status", style="blue")
        table.add_column("Health", style="red")
        table.add_column("Size", style="yellow")
        table.add_column("Last Modified", style="dim")
        
        for project in projects:
            health_color = "green" if project.health_score >= 80 else "yellow" if project.health_score >= 60 else "red"
            table.add_row(
                project.name,
                project.type,
                project.language,
                project.status,
                f"[{health_color}]{project.health_score}%[/{health_color}]",
                project.size,
                project.last_modified[:10]
            )
        
        self.console.print(table)
    
    def show_project_details(self, project_name: str):
        """Show detailed information about a project"""
        projects = self.scan_projects()
        project = next((p for p in projects if p.name == project_name), None)
        
        if not project:
            self.console.print(f"[red]Project '{project_name}' not found![/red]")
            return
        
        # Create detailed panel
        content = f"""
[bold]Project:[/bold] {project.name}
[bold]Path:[/bold] {project.path}
[bold]Type:[/bold] {project.type}
[bold]Language:[/bold] {project.language}
[bold]Framework:[/bold] {project.framework}
[bold]Status:[/bold] {project.status}
[bold]Health Score:[/bold] {project.health_score}%
[bold]Size:[/bold] {project.size}
[bold]Last Modified:[/bold] {project.last_modified}
[bold]Git Remote:[/bold] {project.git_remote or 'None'}
[bold]Dependencies:[/bold] {', '.join(project.dependencies[:5])}
[bold]Issues:[/bold] {len(project.issues)} found
"""
        
        if project.issues:
            content += "\n[bold]Issues:[/bold]\n"
            for issue in project.issues:
                content += f"  • {issue}\n"
        
        panel = Panel(content, title=f"Project Details: {project.name}", border_style="blue")
        self.console.print(panel)
    
    def backup_project(self, project_name: str) -> bool:
        """Backup a project"""
        try:
            projects = self.scan_projects()
            project = next((p for p in projects if p.name == project_name), None)
            
            if not project:
                self.console.print(f"[red]Project '{project_name}' not found![/red]")
                return False
            
            # Create backup directory
            backup_dir = Path(self.config["backup_dir"]) / f"{project_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy project
            shutil.copytree(project.path, backup_dir / project_name)
            
            self.console.print(f"[green]Project '{project_name}' backed up to {backup_dir}[/green]")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up project: {e}")
            self.console.print(f"[red]Error backing up project: {e}[/red]")
            return False
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        try:
            backup_dir = Path(self.config["backup_dir"])
            retention_days = self.config["backup"]["retention_days"]
            
            for backup_path in backup_dir.iterdir():
                if backup_path.is_dir():
                    # Check if backup is older than retention period
                    stat = backup_path.stat()
                    days_old = (datetime.datetime.now() - datetime.datetime.fromtimestamp(stat.st_mtime)).days
                    
                    if days_old > retention_days:
                        shutil.rmtree(backup_path)
                        logger.info(f"Removed old backup: {backup_path}")
            
            self.console.print("[green]Old backups cleaned up![/green]")
            
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
            self.console.print(f"[red]Error cleaning up backups: {e}[/red]")
    
    def monitor_projects(self):
        """Monitor project health and status"""
        if not self.config["monitoring"]["enabled"]:
            return
        
        projects = self.scan_projects()
        issues_found = []
        
        for project in projects:
            if project.health_score < self.config["monitoring"]["health_threshold"]:
                issues_found.append(f"{project.name}: Health score {project.health_score}%")
            
            if project.issues:
                issues_found.append(f"{project.name}: {len(project.issues)} issues")
        
        if issues_found:
            self.console.print("[yellow]Project monitoring alerts:[/yellow]")
            for issue in issues_found:
                self.console.print(f"  • {issue}")
        else:
            self.console.print("[green]All projects are healthy![/green]")
    
    def run_interactive_mode(self):
        """Run interactive mode"""
        while True:
            self.console.print("\n[bold blue]Development Project Manager[/bold blue]")
            self.console.print("1. List projects")
            self.console.print("2. Show project details")
            self.console.print("3. Create new project")
            self.console.print("4. Backup project")
            self.console.print("5. Monitor projects")
            self.console.print("6. Cleanup old backups")
            self.console.print("7. Configuration")
            self.console.print("8. Exit")
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "1":
                self.list_projects()
            elif choice == "2":
                project_name = Prompt.ask("Enter project name")
                self.show_project_details(project_name)
            elif choice == "3":
                name = Prompt.ask("Enter project name")
                language = Prompt.ask("Enter language (python/javascript/rust)", default="python")
                self.create_project(name, language=language)
            elif choice == "4":
                project_name = Prompt.ask("Enter project name")
                self.backup_project(project_name)
            elif choice == "5":
                self.monitor_projects()
            elif choice == "6":
                self.cleanup_old_backups()
            elif choice == "7":
                self.show_config()
            elif choice == "8":
                break
    
    def show_config(self):
        """Show current configuration"""
        config_panel = Panel(
            json.dumps(self.config, indent=2),
            title="Configuration",
            border_style="green"
        )
        self.console.print(config_panel)

def main():
    parser = argparse.ArgumentParser(description="Development Project Manager")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("--list", action="store_true", help="List all projects")
    parser.add_argument("--create", help="Create a new project")
    parser.add_argument("--language", help="Project language for creation")
    parser.add_argument("--backup", help="Backup a project")
    parser.add_argument("--monitor", action="store_true", help="Monitor project health")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    manager = ProjectManager(args.config)
    
    if args.list:
        manager.list_projects()
    elif args.create:
        language = args.language or "python"
        manager.create_project(args.create, language=language)
    elif args.backup:
        manager.backup_project(args.backup)
    elif args.monitor:
        manager.monitor_projects()
    elif args.interactive:
        manager.run_interactive_mode()
    else:
        manager.run_interactive_mode()

if __name__ == "__main__":
    main()
