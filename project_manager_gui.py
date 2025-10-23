#!/usr/bin/env python3
"""
Development Project Manager - GUI Version
A visual interface for managing multiple development projects with automated setup,
monitoring, and maintenance capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import subprocess
import shutil
import datetime
from pathlib import Path
import threading
import webbrowser
from typing import Dict, List, Optional
import psutil
import requests
import sys
import time
import hashlib
import pickle

class ProjectManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Development Project Manager")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        # Set window icon and styling
        self.root.resizable(True, True)
        self.root.minsize(1000, 700)
        
        # Configuration
        self.config_path = "config.json"
        self.config = self.load_config()
        self.projects = []
        
        # Cache setup
        self.cache_dir = Path.home() / '.dev-project-manager' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'project_cache.pkl'
        
        # Background processing variables
        self.background_queue = []
        self.processing_in_background = False
        self.batch_size = 2  # Process 1-2 projects at a time
        
        # Define colors early for use in widgets
        self.colors = {
            'bg_primary': '#0d1117',      # GitHub dark
            'bg_secondary': '#161b22',    # Slightly lighter
            'bg_tertiary': '#21262d',     # Even lighter
            'accent': '#238636',          # GitHub green
            'accent_hover': '#2ea043',    # Lighter green
            'text_primary': '#f0f6fc',    # Almost white
            'text_secondary': '#8b949e',  # Muted text
            'text_accent': '#58a6ff',     # Blue accent
            'border': '#30363d',          # Subtle borders
            'success': '#238636',         # Green
            'warning': '#d29922',         # Orange
            'error': '#f85149',           # Red
            'info': '#58a6ff'             # Blue
        }
        
        # Create GUI elements
        self.create_widgets()
        self.setup_styles()
        self.load_projects()
        
    def load_config(self):
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
                print(f"Error loading config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title with emoji and modern styling
        title_label = ttk.Label(main_frame, text="🚀 Development Project Manager", 
                                style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Projects tab
        self.create_projects_tab()
        
        # Create Project tab
        self.create_create_tab()
        
        # Monitoring tab
        self.create_monitoring_tab()
        
        # Settings tab
        self.create_settings_tab()
        
        # Status bar with modern styling
        self.status_var = tk.StringVar()
        self.status_var.set("🟢 Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              style='Status.TLabel')
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def create_projects_tab(self):
        """Create modern projects management tab"""
        projects_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(projects_frame, text="📁 Projects")
        
        # Top frame for controls with modern styling
        controls_frame = ttk.Frame(projects_frame, style='Card.TFrame')
        controls_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Control buttons with modern styling
        refresh_btn = ttk.Button(controls_frame, text="🔄 Refresh", 
                               command=self.refresh_projects)
        refresh_btn.pack(side=tk.LEFT, padx=(15, 10), pady=10)
        
        backup_btn = ttk.Button(controls_frame, text="💾 Backup Selected", 
                               command=self.backup_selected_project,
                               style='Secondary.TButton')
        backup_btn.pack(side=tk.LEFT, padx=(0, 10), pady=10)
        
        open_btn = ttk.Button(controls_frame, text="📂 Open in Explorer", 
                             command=self.open_project_folder,
                             style='Secondary.TButton')
        open_btn.pack(side=tk.LEFT, padx=(0, 10), pady=10)
        
        # Health filter with modern styling
        health_var = tk.StringVar(value="All")
        health_combo = ttk.Combobox(controls_frame, textvariable=health_var, 
                                   values=["All", "Healthy (80%+)", "Warning (60-79%)", "Critical (<60%)"],
                                   state="readonly")
        health_combo.pack(side=tk.RIGHT, padx=(10, 15), pady=10)
        health_combo.bind('<<ComboboxSelected>>', self.filter_projects)
        
        # Create resizable paned window for tree and details
        main_paned = ttk.PanedWindow(projects_frame, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Top pane: Projects treeview with modern styling
        tree_frame = ttk.Frame(main_paned, style='Card.TFrame')
        main_paned.add(tree_frame, weight=3)  # Give more space to tree
        
        # Tree header with modern styling
        tree_header = ttk.Label(tree_frame, text="📊 Project Overview", style='Heading.TLabel')
        tree_header.pack(pady=(10, 5), padx=10, anchor=tk.W)
        
        # Create treeview with hierarchical support and modern styling
        self.tree = ttk.Treeview(tree_frame, columns=('type', 'language', 'status', 'health', 'size', 'modified'), 
                                 show='tree headings', style='Treeview')
        
        # Configure columns with modern headers
        self.tree.heading('#0', text='📁 Project Name')
        self.tree.heading('type', text='🏗️ Type')
        self.tree.heading('language', text='💻 Language')
        self.tree.heading('status', text='📊 Status')
        self.tree.heading('health', text='💚 Health')
        self.tree.heading('size', text='📏 Size')
        self.tree.heading('modified', text='📅 Last Modified')
        
        # Configure column widths for better hierarchy display
        self.tree.column('#0', width=300, minwidth=200)
        self.tree.column('type', width=100, minwidth=80)
        self.tree.column('language', width=120, minwidth=100)
        self.tree.column('status', width=80, minwidth=60)
        self.tree.column('health', width=80, minwidth=60)
        self.tree.column('size', width=80)
        self.tree.column('modified', width=120)
        
        # Scrollbars for tree
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars with proper positioning
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initially hide horizontal scrollbar
        h_scrollbar.pack_forget()
        
        # Bind events for lazy loading and interaction
        self.tree.bind('<Double-1>', self.toggle_project_expansion)
        self.tree.bind('<<TreeviewSelect>>', self.show_project_details)
        self.tree.bind('<<TreeviewOpen>>', self.on_tree_expand)
        self.tree.bind('<<TreeviewClose>>', self.on_tree_collapse)
        self.tree.bind('<Button-3>', self.show_context_menu)  # Right-click context menu
        
        # Track which items have been fully loaded
        self.loaded_items = set()
        
        # Multi-selection support
        self.tree.configure(selectmode='extended')  # Allow multiple selection
        
        # Store scrollbar reference for dynamic visibility
        self.h_scrollbar = h_scrollbar
        
        # Bind events to check scrollbar visibility
        self.tree.bind('<Configure>', self._check_scrollbar_visibility)
        self.tree.bind('<Button-1>', self._check_scrollbar_visibility)
        self.tree.bind('<Key>', self._check_scrollbar_visibility)
        
        # Bottom pane: Project details with modern styling
        details_frame = ttk.LabelFrame(main_paned, text="📋 Project Details", style='TLabelframe')
        main_paned.add(details_frame, weight=1)  # Give less space to details
        
        # Modern text widget with dark theme
        self.details_text = tk.Text(details_frame, 
                                   height=8, 
                                   wrap=tk.WORD,
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_primary'],
                                   font=('Consolas', 10),
                                   insertbackground=self.colors['text_primary'],
                                   selectbackground=self.colors['accent'],
                                   selectforeground=self.colors['text_primary'],
                                   borderwidth=0,
                                   relief='flat')
        
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
    
    def create_create_tab(self):
        """Create modern new project tab"""
        create_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(create_frame, text="✨ Create Project")
        
        # Create resizable paned window for form and templates
        create_paned = ttk.PanedWindow(create_frame, orient=tk.VERTICAL)
        create_paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top pane: Project creation form with modern styling
        form_frame = ttk.LabelFrame(create_paned, text="🆕 New Project", style='TLabelframe')
        create_paned.add(form_frame, weight=1)  # Give less space to form
        
        # Project name with modern styling
        ttk.Label(form_frame, text="📝 Project Name:", style='TLabel').grid(row=0, column=0, sticky=tk.W, padx=15, pady=10)
        self.project_name_var = tk.StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=self.project_name_var, width=40)
        name_entry.grid(row=0, column=1, padx=15, pady=10)
        
        # Language selection with modern styling
        ttk.Label(form_frame, text="💻 Language:", style='TLabel').grid(row=1, column=0, sticky=tk.W, padx=15, pady=10)
        self.language_var = tk.StringVar(value="python")
        language_combo = ttk.Combobox(form_frame, textvariable=self.language_var, 
                                     values=["python", "javascript", "typescript", "java", "csharp", "cpp", "c", "go", "rust", 
                                            "php", "ruby", "swift", "kotlin", "dart", "scala", "groovy", "haskell", "clojure",
                                            "lua", "perl", "r", "julia", "nim", "zig", "v", "assembly",
                                            "html", "css", "vue", "react", "angular", "svelte", "nextjs", "nuxt", "gatsby",
                                            "bash", "powershell", "batch", "zsh", "fish",
                                            "sql", "markdown", "json", "yaml", "xml"],
                                     state="readonly")
        language_combo.grid(row=1, column=1, padx=15, pady=10)
        
        # Framework selection with modern styling
        ttk.Label(form_frame, text="🏗️ Framework:", style='TLabel').grid(row=2, column=0, sticky=tk.W, padx=15, pady=10)
        self.framework_var = tk.StringVar()
        framework_entry = ttk.Entry(form_frame, textvariable=self.framework_var, width=40)
        framework_entry.grid(row=2, column=1, padx=15, pady=10)
        
        # Description with modern styling
        ttk.Label(form_frame, text="📝 Description:", style='TLabel').grid(row=3, column=0, sticky=tk.W, padx=15, pady=10)
        self.description_var = tk.StringVar()
        desc_entry = ttk.Entry(form_frame, textvariable=self.description_var, width=40)
        desc_entry.grid(row=3, column=1, padx=15, pady=10)
        
        # Create button with modern styling
        create_btn = ttk.Button(form_frame, text="✨ Create Project", command=self.create_new_project)
        create_btn.grid(row=4, column=1, padx=15, pady=20, sticky=tk.E)
        
        # Bottom pane: Templates section with modern styling
        templates_frame = ttk.LabelFrame(create_paned, text="📋 Project Templates", style='TLabelframe')
        create_paned.add(templates_frame, weight=3)  # Give more space to templates
        
        # Template list with modern dark theme
        self.template_listbox = tk.Listbox(templates_frame, 
                                          height=10,
                                          bg=self.colors['bg_secondary'],
                                          fg=self.colors['text_primary'],
                                          font=('Segoe UI', 10),
                                          selectbackground=self.colors['accent'],
                                          selectforeground=self.colors['text_primary'],
                                          borderwidth=0,
                                          relief='flat')
        template_scrollbar = ttk.Scrollbar(templates_frame, orient=tk.VERTICAL, command=self.template_listbox.yview)
        self.template_listbox.configure(yscrollcommand=template_scrollbar.set)
        
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        template_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load templates
        self.load_templates()
    
    def create_monitoring_tab(self):
        """Create modern project monitoring tab"""
        monitor_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(monitor_frame, text="📊 Monitoring")
        
        # Monitoring controls
        controls_frame = ttk.Frame(monitor_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Start monitoring button
        start_btn = ttk.Button(controls_frame, text="Start Monitoring", 
                               command=self.start_monitoring)
        start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop monitoring button
        stop_btn = ttk.Button(controls_frame, text="Stop Monitoring", 
                              command=self.stop_monitoring)
        stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Health threshold
        ttk.Label(controls_frame, text="Health Threshold:").pack(side=tk.LEFT, padx=(20, 5))
        self.health_threshold_var = tk.IntVar(value=70)
        threshold_spinbox = ttk.Spinbox(controls_frame, from_=0, to=100, 
                                       textvariable=self.health_threshold_var, width=10)
        threshold_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Monitoring status
        self.monitoring_status_var = tk.StringVar(value="Stopped")
        status_label = ttk.Label(controls_frame, textvariable=self.monitoring_status_var)
        status_label.pack(side=tk.RIGHT)
        
        # Monitoring results
        results_frame = ttk.LabelFrame(monitor_frame, text="Monitoring Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.monitoring_text = tk.Text(results_frame, wrap=tk.WORD)
        monitor_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.monitoring_text.yview)
        self.monitoring_text.configure(yscrollcommand=monitor_scrollbar.set)
        
        self.monitoring_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        monitor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Monitoring thread
        self.monitoring_thread = None
        self.monitoring_running = False
    
    def create_settings_tab(self):
        """Create modern settings tab"""
        settings_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Settings form
        form_frame = ttk.LabelFrame(settings_frame, text="Configuration")
        form_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Projects directory
        ttk.Label(form_frame, text="Projects Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.projects_dir_var = tk.StringVar(value=self.config["projects_dir"])
        projects_dir_entry = ttk.Entry(form_frame, textvariable=self.projects_dir_var, width=50)
        projects_dir_entry.grid(row=0, column=1, padx=5, pady=5)
        browse_btn = ttk.Button(form_frame, text="Browse", command=self.browse_projects_dir)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Backup directory
        ttk.Label(form_frame, text="Backup Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.backup_dir_var = tk.StringVar(value=self.config["backup_dir"])
        backup_dir_entry = ttk.Entry(form_frame, textvariable=self.backup_dir_var, width=50)
        backup_dir_entry.grid(row=1, column=1, padx=5, pady=5)
        backup_browse_btn = ttk.Button(form_frame, text="Browse", command=self.browse_backup_dir)
        backup_browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Performance settings
        performance_frame = ttk.LabelFrame(form_frame, text="Performance")
        performance_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=10)
        
        # Lazy loading option
        self.lazy_loading_var = tk.BooleanVar(value=False)
        lazy_loading_check = ttk.Checkbutton(performance_frame, text="Fast Loading (Skip Heavy Analysis)", 
                                           variable=self.lazy_loading_var)
        lazy_loading_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Background processing option
        self.background_processing_var = tk.BooleanVar(value=True)
        background_check = ttk.Checkbutton(performance_frame, text="Background Health Checks (Keep UI Responsive)", 
                                         variable=self.background_processing_var)
        background_check.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Cache management
        cache_frame = ttk.Frame(performance_frame)
        cache_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        ttk.Label(cache_frame, text="Cache Management:").pack(side=tk.LEFT, padx=(0, 10))
        clear_cache_btn = ttk.Button(cache_frame, text="Clear Cache", command=self.clear_cache)
        clear_cache_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        cache_info_btn = ttk.Button(cache_frame, text="Cache Info", command=self.show_cache_info)
        cache_info_btn.pack(side=tk.LEFT)
        
        # Monitoring settings
        monitoring_frame = ttk.LabelFrame(form_frame, text="Monitoring")
        monitoring_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=10)
        
        # Enable monitoring
        self.monitoring_enabled_var = tk.BooleanVar(value=self.config["monitoring"]["enabled"])
        monitoring_check = ttk.Checkbutton(monitoring_frame, text="Enable Monitoring", 
                                          variable=self.monitoring_enabled_var)
        monitoring_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Check interval
        ttk.Label(monitoring_frame, text="Check Interval (seconds):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.check_interval_var = tk.IntVar(value=self.config["monitoring"]["check_interval"])
        interval_spinbox = ttk.Spinbox(monitoring_frame, from_=60, to=3600, 
                                      textvariable=self.check_interval_var, width=10)
        interval_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Save button
        save_btn = ttk.Button(form_frame, text="Save Settings", command=self.save_settings)
        save_btn.grid(row=3, column=1, padx=5, pady=20, sticky=tk.E)
        
        # Reload projects button
        reload_btn = ttk.Button(form_frame, text="Reload Projects", command=self.load_projects)
        reload_btn.grid(row=3, column=0, padx=5, pady=20, sticky=tk.W)
    
    def setup_styles(self):
        """Setup modern dark theme GUI styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors are already defined in __init__
        
        # Configure main window
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure styles with modern dark theme
        style.configure('TLabel', 
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10))
        
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 18, 'bold'),
                       foreground=self.colors['text_primary'],
                       background=self.colors['bg_primary'])
        
        style.configure('Heading.TLabel', 
                       font=('Segoe UI', 12, 'bold'),
                       foreground=self.colors['text_primary'],
                       background=self.colors['bg_primary'])
        
        style.configure('Status.TLabel', 
                       font=('Segoe UI', 10),
                       foreground=self.colors['text_secondary'],
                       background=self.colors['bg_primary'])
        
        # Enhanced treeview with modern styling
        style.configure('Treeview', 
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_secondary'],
                       borderwidth=0,
                       font=('Segoe UI', 10))
        
        style.configure('Treeview.Heading', 
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=1,
                       relief='flat')
        
        # Modern notebook styling
        style.configure('TNotebook', 
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        style.configure('TNotebook.Tab', 
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_secondary'],
                       padding=[20, 12],
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0)
        
        style.map('TNotebook.Tab', 
                 background=[('selected', self.colors['accent']),
                            ('active', self.colors['bg_secondary'])],
                 foreground=[('selected', self.colors['text_primary']),
                           ('active', self.colors['text_primary'])])
        
        # Modern button styling
        style.configure('TButton', 
                         background=self.colors['accent'],
                         foreground=self.colors['text_primary'],
                         font=('Segoe UI', 10, 'bold'),
                         borderwidth=0,
                         focuscolor='none',
                         padding=[15, 8])
        
        style.map('TButton', 
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent'])])
        
        # Secondary button style
        style.configure('Secondary.TButton',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10),
                       borderwidth=1,
                       focuscolor='none',
                       padding=[12, 6])
        
        style.map('Secondary.TButton',
                 background=[('active', self.colors['bg_secondary']),
                           ('pressed', self.colors['bg_tertiary'])])
        
        # Modern entry styling
        style.configure('TEntry', 
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_secondary'],
                       borderwidth=1,
                       font=('Segoe UI', 10),
                       insertcolor=self.colors['text_primary'])
        
        style.map('TEntry',
                 fieldbackground=[('focus', self.colors['bg_tertiary'])])
        
        # Modern combobox styling
        style.configure('TCombobox', 
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_secondary'],
                       borderwidth=1,
                       font=('Segoe UI', 10))
        
        # Frame styling
        style.configure('TFrame', 
                       background=self.colors['bg_primary'])
        
        style.configure('Card.TFrame',
                       background=self.colors['bg_secondary'],
                       relief='flat',
                       borderwidth=1)
        
        # Label frame styling
        style.configure('TLabelframe', 
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       relief='flat')
        
        style.configure('TLabelframe.Label', 
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_accent'],
                       font=('Segoe UI', 11, 'bold'))
        
        # Progress bar styling
        style.configure('TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['bg_tertiary'],
                       borderwidth=0,
                       lightcolor=self.colors['accent'],
                       darkcolor=self.colors['accent'])
        
        # Scrollbar styling
        style.configure('TScrollbar',
                       background=self.colors['bg_tertiary'],
                       troughcolor=self.colors['bg_secondary'],
                       borderwidth=0,
                       arrowcolor=self.colors['text_secondary'],
                       darkcolor=self.colors['bg_tertiary'],
                       lightcolor=self.colors['bg_tertiary'])
        
        style.map('TScrollbar',
                 background=[('active', self.colors['bg_secondary'])])
    
    def load_projects(self):
        """Load projects from directory with caching support (optimized for large folders)"""
        try:
            projects_dir = Path(self.config["projects_dir"])
            if not projects_dir.exists():
                self.status_var.set(f"Projects directory does not exist: {projects_dir}")
                self.projects = []
                self.refresh_projects()
                return
            
            # Show loading status
            self.status_var.set("Loading projects... Please wait")
            self.root.update()  # Update GUI to show status
            
            # Load cache
            cache = self._load_cache()
            cache_hits = 0
            cache_misses = 0
            
            self.projects = []
            self.hierarchical_projects = {}  # Store hierarchical structure
            
            # Load projects with hierarchical detection and caching
            print(f"Starting project scan in: {projects_dir}")
            self._load_hierarchical_projects(projects_dir, parent_path=None, depth=0, cache=cache, cache_hits=cache_hits, cache_misses=cache_misses)
            project_count = len(self.projects)
            
            # Save updated cache
            self._save_cache(cache)
            
            self.refresh_projects()
            self.status_var.set(f"Loaded {project_count} projects (Cache: {cache_hits} hits, {cache_misses} misses) from {projects_dir}")
            print(f"Project loading completed. Found {project_count} projects. Cache: {cache_hits} hits, {cache_misses} misses")
            
            # Start background processing if queue has items
            if self.background_queue:
                self.start_background_processing()
            
        except Exception as e:
            error_msg = f"Error loading projects: {e}"
            print(error_msg)
            self.status_var.set(error_msg)
            self.projects = []
            self.refresh_projects()
    
    def start_background_processing(self):
        """Start background processing of queued projects"""
        if not self.processing_in_background and self.background_queue:
            self.processing_in_background = True
            self.status_var.set(f"Background processing {len(self.background_queue)} projects...")
            self.process_background_batch()
    
    def process_background_batch(self):
        """Process a small batch of projects in the background"""
        if not self.background_queue or not self.processing_in_background:
            self.processing_in_background = False
            self.status_var.set("Background processing completed")
            return
        
        # Process up to batch_size projects
        batch = self.background_queue[:self.batch_size]
        self.background_queue = self.background_queue[self.batch_size:]
        
        print(f"Processing background batch: {[p.name for p in batch]}")
        
        # Process each project in the batch
        for project_path in batch:
            try:
                # Perform full analysis
                project_info = self.analyze_project(project_path)
                
                # Update the project in the list
                for i, project in enumerate(self.projects):
                    if project.get('path') == str(project_path):
                        self.projects[i].update(project_info)
                        break
                
                # Update cache
                cache = self._load_cache()
                if cache is not None:
                    self._cache_project(project_path, project_info, cache)
                    self._save_cache(cache)
                
                print(f"  Background analysis completed: {project_path.name} - {project_info.get('health', 'N/A')}%")
                
            except Exception as e:
                print(f"  Background analysis error for {project_path.name}: {e}")
        
        # Update the GUI
        self.refresh_projects()
        
        # Schedule next batch
        if self.background_queue:
            self.root.after(100, self.process_background_batch)  # 100ms delay between batches
        else:
            self.processing_in_background = False
            self.status_var.set("Background processing completed")
            print("Background processing completed")
    
    def _load_hierarchical_projects(self, base_path: Path, parent_path: Path = None, depth: int = 0, cache: Dict = None, cache_hits: int = 0, cache_misses: int = 0):
        """Recursively load projects with hierarchical structure (ultra-optimized for large folders)"""
        if depth > 2:  # Allow deeper scanning for better hierarchy detection
            return
        
        # Optimized limits for faster loading
        max_dirs_per_level = 15 if depth == 0 else 8 if depth == 1 else 5
        dirs_scanned = 0
        
        try:
            # Get directory list and sort by name for consistent behavior
            dirs = [d for d in base_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
            dirs.sort(key=lambda x: x.name.lower())
            
            for project_path in dirs:
                if dirs_scanned >= max_dirs_per_level:
                    print(f"Warning: Reached directory limit ({max_dirs_per_level}) at depth {depth}")
                    break
                    
                dirs_scanned += 1
                
                # Ultra-quick check for obvious non-project directories
                if self._is_obvious_non_project(project_path):
                    print(f"Skipping obvious non-project: {project_path.name}")
                    continue
                
                # Update GUI periodically to prevent freezing
                if dirs_scanned % 5 == 0:
                    self.root.update_idletasks()
                
                try:
                    # Lightweight project check (no heavy analysis yet)
                    print(f"Checking directory: {project_path.name}")
                    if self._is_likely_project_directory(project_path):
                        print(f"Found project: {project_path.name}")
                        # Try to get from cache first
                        project_info = None
                        if cache is not None:
                            project_info = self._get_cached_project(project_path, cache)
                            if project_info:
                                cache_hits += 1
                                print(f"  Using cached data for {project_path.name}")
                            else:
                                print(f"  No cached data for {project_path.name}")
                        
                        # If not in cache, analyze the project
                        if project_info is None:
                            cache_misses += 1
                            # Always use quick analysis for initial loading for speed
                            project_info = self._quick_analyze_project(project_path)
                            print(f"  Quick analysis for {project_path.name}")
                            
                            # Add to background queue for full analysis if enabled
                            if getattr(self, 'background_processing_var', None) and self.background_processing_var.get():
                                self.background_queue.append(project_path)
                                print(f"  Queued for background analysis: {project_path.name}")
                            
                            # Cache the result
                            if project_info and cache is not None:
                                self._cache_project(project_path, project_info, cache)
                        
                        if project_info:
                            # Smart parent detection
                            detected_parent = self._detect_parent_project(project_path, base_path, parent_path)
                            project_info['parent'] = detected_parent
                            project_info['depth'] = depth
                            project_info['path'] = str(project_path)
                            project_info['relative_path'] = str(project_path.relative_to(Path(self.config["projects_dir"])))
                            
                            self.projects.append(project_info)
                            
                            # Store in hierarchical structure
                            if detected_parent:
                                parent_key = detected_parent
                                if parent_key not in self.hierarchical_projects:
                                    self.hierarchical_projects[parent_key] = []
                                self.hierarchical_projects[parent_key].append(project_info)
                            
                            # Smart recursion: only recurse if project might contain sub-projects
                            if self._might_contain_subprojects(project_path):
                                print(f"  Recursively scanning for sub-projects: {project_path.name}")
                                self._load_hierarchical_projects(project_path, project_path, depth + 1, cache, cache_hits, cache_misses)
                        else:
                            print(f"  Project info is None for {project_path.name}")
                    
                except Exception as e:
                    print(f"Error analyzing project {project_path}: {e}")
                    continue
                else:
                    # If we get here, the directory was checked but not considered a project
                    print(f"Directory not considered project: {project_path.name}")
                    
        except PermissionError:
            print(f"Permission denied accessing {base_path}")
        except Exception as e:
            print(f"Error scanning directory {base_path}: {e}")
    
    def _is_likely_project_directory(self, project_path: Path) -> bool:
        """Enhanced project detection including collection folders"""
        # Check for obvious project indicators
        quick_indicators = [
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml',
            'composer.json', 'Gemfile', 'setup.py', 'README.md'
        ]
        
        for indicator in quick_indicators:
            if (project_path / indicator).exists():
                return True
        
        # Check for common source directories
        for src_dir in ['src', 'lib', 'app']:
            if (project_path / src_dir).exists():
                return True
        
        # Check for language files
        for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c']:
            if list(project_path.glob(f'*{ext}')):
                return True
        
        # NEW: Check for collection folders (folders containing multiple sub-projects)
        if self._is_collection_folder(project_path):
            return True
        
        return False
    
    def _is_collection_folder(self, project_path: Path) -> bool:
        """Check if a folder is a collection of projects (like Tools, Projects, etc.)"""
        try:
            # Count subdirectories that look like projects
            subdirs = [d for d in project_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
            
            if len(subdirs) < 3:  # Need at least 3 subdirectories to be considered a collection
                return False
            
            # Count how many subdirectories look like projects
            project_like_count = 0
            for subdir in subdirs:
                if self._has_project_indicators(subdir):
                    project_like_count += 1
            
            # If more than half of subdirectories look like projects, it's a collection folder
            return project_like_count >= len(subdirs) * 0.5
            
        except Exception:
            return False
    
    def _quick_analyze_project(self, project_path: Path) -> dict:
        """Quick project analysis without heavy computation"""
        try:
            name = project_path.name
            size = self.get_directory_size(project_path)
            
            # Check if this is a collection folder
            if self._is_collection_folder(project_path):
                # Count sub-projects for collection folders
                subdirs = [d for d in project_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
                project_count = len([d for d in subdirs if self._has_project_indicators(d)])
                
                return {
                    'name': name,
                    'path': str(project_path),
                    'type': f"Collection ({project_count} projects)",
                    'language': 'multi-language',
                    'framework': 'Collection',
                    'health': 75,  # Collection folders get good health
                    'size': f"{len(subdirs)} items",
                    'status': 'Collection',
                    'modified': 'Unknown'
                }
            else:
                # Quick project type detection
                project_type, language, framework = self._quick_detect_project_type(project_path)
                
                # Simple health score (no heavy analysis)
                health_score = 50  # Default score, will be calculated later if needed
                
                return {
                    'name': name,
                    'path': str(project_path),
                    'type': project_type,
                    'language': language,
                    'framework': framework,
                    'health': health_score,
                    'size': size,
                    'status': 'Unknown',
                    'modified': 'Unknown'
                }
        except Exception as e:
            print(f"Error in quick analysis of {project_path}: {e}")
            return None
    
    def _quick_detect_project_type(self, project_path: Path) -> tuple:
        """Quick project type detection without heavy file scanning"""
        # Check for obvious indicators
        if (project_path / 'package.json').exists():
            return ('nodejs', 'javascript', 'node')
        elif (project_path / 'requirements.txt').exists() or (project_path / 'setup.py').exists():
            return ('python', 'python', 'flask')
        elif (project_path / 'Cargo.toml').exists():
            return ('rust', 'rust', 'cargo')
        elif (project_path / 'go.mod').exists():
            return ('go', 'go', 'go')
        elif (project_path / 'pom.xml').exists():
            return ('java', 'java', 'maven')
        elif (project_path / 'composer.json').exists():
            return ('php', 'php', 'composer')
        elif (project_path / 'Gemfile').exists():
            return ('ruby', 'ruby', 'bundler')
        else:
            return ('generic', 'unknown', 'unknown')
    
    def _is_obvious_monorepo(self, project_path: Path) -> bool:
        """Quick check for obvious monorepo structure"""
        monorepo_indicators = ['packages', 'apps', 'services', 'modules', 'libs']
        for indicator in monorepo_indicators:
            if (project_path / indicator).exists():
                return True
        return False
    
    def _is_obvious_non_project(self, project_path: Path) -> bool:
        """Quick check for obvious non-project directories to skip early"""
        obvious_non_projects = {
            # Common non-project folders
            'node_modules', 'venv', 'env', '.venv', '.env', '__pycache__',
            'target', 'build', 'dist', 'out', 'bin', 'obj', 'classes',
            '.git', '.svn', '.hg', '.bzr', '.vscode', '.idea', '.vs',
            'tmp', 'temp', 'cache', '.cache', 'logs', '.logs',
            '.next', '.nuxt', '.gatsby', '.svelte-kit', '.astro',
            'public', 'static', 'assets', 'media', 'docs', 'documentation'
        }
        
        return project_path.name.lower() in obvious_non_projects
    
    def _should_recurse_into_project(self, project_path: Path) -> bool:
        """Determine if we should recurse into a project directory"""
        # Don't recurse into obvious single-purpose projects
        single_purpose_indicators = [
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml'
        ]
        
        # If it has a clear package manager, it's likely a single project
        for indicator in single_purpose_indicators:
            if (project_path / indicator).exists():
                return False
        
        # Only recurse if it looks like a monorepo or multi-project structure
        monorepo_indicators = ['packages', 'apps', 'services', 'modules', 'libs', 'components']
        for indicator in monorepo_indicators:
            if (project_path / indicator).exists():
                return True
        
        # Check for multiple package.json files (monorepo)
        package_json_count = len(list(project_path.rglob('package.json')))
        if package_json_count > 1:
            return True
        
        # Check for multiple language files in subdirectories
        language_files = list(project_path.rglob('*.py')) + list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts'))
        if len(language_files) > 10:  # Likely a monorepo
            return True
        
        return False
    
    def _detect_parent_project(self, project_path: Path, base_path: Path, explicit_parent: Path = None) -> str:
        """Smart parent detection for hierarchical relationships"""
        # If explicit parent is provided, use it
        if explicit_parent:
            return str(explicit_parent)
        
        # Check if this project is inside another project
        current_path = project_path.parent
        
        # Look for parent project indicators in parent directories
        while current_path != base_path and current_path != base_path.parent:
            # Check if parent directory is a project
            if self._is_likely_project_directory(current_path):
                return str(current_path)
            current_path = current_path.parent
        
        # No parent found
        return None
    
    def _might_contain_subprojects(self, project_path: Path) -> bool:
        """Check if a project might contain sub-projects"""
        # First check if this is a collection folder
        if self._is_collection_folder(project_path):
            return True
        
        # Check for common sub-project indicators
        subproject_indicators = [
            'packages', 'apps', 'libs', 'services', 'modules', 'components',
            'src', 'lib', 'app', 'client', 'server', 'frontend', 'backend'
        ]
        
        for indicator in subproject_indicators:
            if (project_path / indicator).exists():
                # Check if the subdirectory contains projects
                subdir = project_path / indicator
                if subdir.is_dir():
                    # Quick check for project files in subdirectory
                    for item in subdir.iterdir():
                        if item.is_dir() and not item.name.startswith('.'):
                            # Check if this subdirectory looks like a project
                            if self._has_project_indicators(item):
                                return True
        
        # Check for workspace/monorepo files
        workspace_files = ['package.json', 'lerna.json', 'nx.json', 'rush.json']
        for file in workspace_files:
            if (project_path / file).exists():
                return True
        
        return False
    
    def _has_project_indicators(self, path: Path) -> bool:
        """Quick check if a path has project indicators"""
        indicators = [
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml',
            'composer.json', 'Gemfile', 'setup.py', 'README.md', 'src', 'lib', 'app'
        ]
        
        for indicator in indicators:
            if (path / indicator).exists():
                return True
        
        return False
    
    def _is_project_directory(self, project_path: Path) -> bool:
        """Check if a directory is a project (has project indicators)"""
        # Exclude framework-generated folders and common non-project directories
        excluded_folders = {
            # Node.js frameworks
            'node_modules', '.next', '.nuxt', '.vuepress', '.docusaurus',
            'dist', 'build', 'out', '.output', '.vercel', '.netlify',
            
            # Python frameworks
            '__pycache__', '.pytest_cache', '.mypy_cache', 'venv', 'env',
            '.venv', '.env', 'site-packages', 'egg-info',
            
            # Java frameworks
            'target', '.gradle', '.mvn', 'bin', 'classes',
            
            # Build outputs
            'build', 'dist', 'out', 'target', 'bin', 'obj',
            
            # IDE and editor folders
            '.vscode', '.idea', '.vs', '.eclipse', '.settings',
            
            # Version control
            '.git', '.svn', '.hg', '.bzr',
            
            # OS folders
            '.DS_Store', 'Thumbs.db', '.Trash',
            
            # Temporary folders
            'tmp', 'temp', 'cache', '.cache', 'logs', '.logs',
            
            # Framework-specific
            '.next', '.nuxt', '.gatsby', '.svelte-kit', '.astro',
            'public', 'static', 'assets', 'media'
        }
        
        # Skip excluded folders
        if project_path.name.lower() in excluded_folders:
            return False
        
        # Skip hidden folders (except .git for git repos)
        if project_path.name.startswith('.') and project_path.name != '.git':
            return False
        
        project_indicators = [
            # Package managers
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml',
            'composer.json', 'Gemfile', 'setup.py', 'pyproject.toml',
            
            # Build files
            'Makefile', 'CMakeLists.txt', 'build.gradle', 'build.xml',
            
            # Configuration files
            'Dockerfile', 'docker-compose.yml', '.gitignore', 'README.md',
            
            # Source directories
            'src', 'lib', 'app', 'source', 'code'
        ]
        
        # Check for package managers and build files
        for indicator in project_indicators[:10]:  # Package managers and build files
            if (project_path / indicator).exists():
                return True
        
        # Check for source directories
        for src_dir in ['src', 'lib', 'app', 'source', 'code']:
            if (project_path / src_dir).exists():
                return True
        
        # Check for language files (but exclude common framework files)
        framework_files = {
            'next.config.js', 'nuxt.config.js', 'vue.config.js', 'svelte.config.js',
            'tailwind.config.js', 'postcss.config.js', 'babel.config.js',
            'webpack.config.js', 'rollup.config.js', 'vite.config.js',
            'jest.config.js', 'cypress.config.js', 'playwright.config.js'
        }
        
        for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.dart', '.sh']:
            files = list(project_path.glob(f'*{ext}'))
            # Filter out framework config files
            actual_source_files = [f for f in files if f.name not in framework_files]
            if actual_source_files:
                return True
        
        # Check for README or .git (common project indicators)
        if (project_path / 'README.md').exists() or (project_path / '.git').exists():
            return True
        
        return False
    
    def clear_cache(self):
        """Clear the project cache"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                messagebox.showinfo("Cache Cleared", "Project cache has been cleared successfully.")
                print("Cache cleared successfully")
            else:
                messagebox.showinfo("Cache Cleared", "No cache file found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear cache: {e}")
            print(f"Error clearing cache: {e}")
    
    def show_cache_info(self):
        """Show cache information"""
        try:
            cache = self._load_cache()
            cache_size = len(cache)
            cache_file_size = 0
            if self.cache_file.exists():
                cache_file_size = self.cache_file.stat().st_size
            
            info = f"""Cache Information:
• Cached Projects: {cache_size}
• Cache File Size: {cache_file_size / 1024:.1f} KB
• Cache Location: {self.cache_file}
• Cache Directory: {self.cache_dir}"""
            
            messagebox.showinfo("Cache Information", info)
            print(f"Cache info: {cache_size} projects, {cache_file_size / 1024:.1f} KB")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get cache info: {e}")
            print(f"Error getting cache info: {e}")
    
    def _get_cache_key(self, project_path: Path) -> str:
        """Generate a cache key for a project based on its path and modification time"""
        try:
            # Get the most recent modification time of key files
            key_files = ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml', 
                        'composer.json', 'Gemfile', 'setup.py', 'pyproject.toml', 'README.md']
            
            max_mtime = 0
            for key_file in key_files:
                file_path = project_path / key_file
                if file_path.exists():
                    max_mtime = max(max_mtime, file_path.stat().st_mtime)
            
            # If no key files, use directory modification time
            if max_mtime == 0:
                max_mtime = project_path.stat().st_mtime
            
            # Create hash from path and modification time
            cache_string = f"{project_path}_{max_mtime}"
            return hashlib.md5(cache_string.encode()).hexdigest()
        except:
            # Fallback to path hash
            return hashlib.md5(str(project_path).encode()).hexdigest()
    
    def _load_cache(self) -> Dict:
        """Load project cache from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                    print(f"Loaded cache with {len(cache)} entries")
                    return cache
        except Exception as e:
            print(f"Error loading cache: {e}")
        return {}
    
    def _save_cache(self, cache: Dict):
        """Save project cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache, f)
                print(f"Saved cache with {len(cache)} entries")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _get_cached_project(self, project_path: Path, cache: Dict) -> Optional[Dict]:
        """Get cached project data if available and valid"""
        cache_key = self._get_cache_key(project_path)
        if cache_key in cache:
            cached_data = cache[cache_key]
            # Check if the project still exists and hasn't been modified
            if project_path.exists():
                try:
                    current_key = self._get_cache_key(project_path)
                    if current_key == cache_key:
                        print(f"Using cached data for {project_path.name}")
                        return cached_data
                except:
                    pass
        return None
    
    def _cache_project(self, project_path: Path, project_data: Dict, cache: Dict):
        """Cache project data"""
        cache_key = self._get_cache_key(project_path)
        cache[cache_key] = project_data
        print(f"Cached data for {project_path.name}")
    
    def analyze_project(self, project_path: Path) -> Optional[Dict]:
        """Analyze a project directory"""
        try:
            name = project_path.name
            path = str(project_path)
            
            # Detect project type
            project_type, language, framework = self.detect_project_type(project_path)
            
            # Detect JavaScript frameworks specifically
            js_frameworks = self._detect_js_frameworks(project_path)
            
            # If we detected JS frameworks, use them for better project type detection
            if js_frameworks and language in ['javascript', 'typescript']:
                # Use the most relevant framework as the main framework
                framework_priority = ['nextjs', 'nuxt', 'gatsby', 'remix', 'astro', 'svelte', 'angular', 'react', 'vue']
                for priority_framework in framework_priority:
                    if priority_framework in js_frameworks:
                        framework = priority_framework
                        break
                
                # Update project type based on framework
                if framework in ['nextjs', 'nuxt', 'gatsby', 'remix', 'astro']:
                    project_type = 'fullstack'
                elif framework in ['react', 'vue', 'angular', 'svelte']:
                    project_type = 'frontend'
                elif framework in ['express', 'nestjs', 'fastify', 'koa']:
                    project_type = 'backend'
            
            # Get file stats
            stat = project_path.stat()
            last_modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
            size = self.get_directory_size(project_path)
            
            # Calculate health score
            health_score = self.calculate_health_score(project_path, language)
            
            # Get project status
            status = self.get_project_status(project_path)
            
            return {
                'name': name,
                'path': path,
                'type': project_type,
                'language': language,
                'framework': framework,
                'frameworks': js_frameworks if js_frameworks else [],
                'status': status,
                'health': health_score,
                'size': size,
                'modified': last_modified
            }
        except Exception as e:
            print(f"Error analyzing project {project_path}: {e}")
            return None
    
    def _detect_languages(self, project_path: Path) -> list:
        """Detect all programming languages in a project"""
        languages = []
        
        # Comprehensive file extension to language mapping
        lang_extensions = {
            # Python ecosystem
            '.py': 'python', '.pyi': 'python', '.pyc': 'python', '.pyo': 'python',
            
            # JavaScript/TypeScript ecosystem
            '.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript',
            '.ts': 'typescript', '.tsx': 'typescript', '.d.ts': 'typescript',
            
            # Java ecosystem
            '.java': 'java', '.kt': 'kotlin', '.scala': 'scala', '.groovy': 'groovy',
            '.jsp': 'jsp', '.jspx': 'jsp',
            
            # C/C++ ecosystem
            '.c': 'c', '.h': 'c', '.cpp': 'cpp', '.cxx': 'cpp', '.cc': 'cpp',
            '.hpp': 'cpp', '.hxx': 'cpp', '.h++': 'cpp', '.c++': 'cpp',
            
            # C# ecosystem
            '.cs': 'csharp', '.csx': 'csharp',
            
            # Go
            '.go': 'go',
            
            # Rust
            '.rs': 'rust',
            
            # PHP
            '.php': 'php', '.phtml': 'php', '.php3': 'php', '.php4': 'php', '.php5': 'php',
            
            # Ruby
            '.rb': 'ruby', '.rbw': 'ruby', '.rake': 'ruby',
            
            # Shell scripting
            '.sh': 'bash', '.bash': 'bash', '.zsh': 'zsh', '.fish': 'fish',
            '.ps1': 'powershell', '.psm1': 'powershell', '.psd1': 'powershell',
            '.bat': 'batch', '.cmd': 'batch',
            
            # Web technologies
            '.html': 'html', '.htm': 'html', '.xhtml': 'html',
            '.css': 'css', '.scss': 'scss', '.sass': 'sass', '.less': 'less',
            '.xml': 'xml', '.svg': 'svg',
            
            # Data formats
            '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.toml': 'toml',
            '.ini': 'ini', '.cfg': 'config', '.conf': 'config',
            
            # Database
            '.sql': 'sql', '.sqlite': 'sqlite', '.db': 'database',
            
            # Documentation
            '.md': 'markdown', '.rst': 'restructuredtext', '.tex': 'latex',
            '.txt': 'text', '.log': 'log',
            
            # Mobile development
            '.swift': 'swift', '.m': 'objective-c', '.mm': 'objective-c++',
            '.dart': 'dart', '.java': 'java',  # Android
            
            # Functional languages
            '.hs': 'haskell', '.elm': 'elm', '.fs': 'fsharp', '.fsx': 'fsharp',
            '.clj': 'clojure', '.cljs': 'clojurescript',
            
            # Scripting languages
            '.lua': 'lua', '.pl': 'perl', '.pm': 'perl',
            '.r': 'r', '.R': 'r',
            '.jl': 'julia',
            
            # System languages
            '.asm': 'assembly', '.s': 'assembly',
            '.nim': 'nim', '.zig': 'zig', '.v': 'v',
            
            # Web frameworks and tools
            '.vue': 'vue', '.svelte': 'svelte',
            '.jsx': 'react', '.tsx': 'react',
            '.angular': 'angular',
            
            # Configuration and build
            '.dockerfile': 'dockerfile', '.makefile': 'makefile',
            '.cmake': 'cmake', '.gradle': 'gradle',
            '.maven': 'maven', '.ant': 'ant',
            
            # Other
            '.shader': 'shader', '.glsl': 'glsl', '.hlsl': 'hlsl',
            '.proto': 'protobuf', '.thrift': 'thrift',
            '.graphql': 'graphql', '.gql': 'graphql'
        }
        
        # Check all files for language indicators
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                # Check file extension
                if file_path.suffix.lower() in lang_extensions:
                    lang = lang_extensions[file_path.suffix.lower()]
                    if lang not in languages:
                        languages.append(lang)
                
                # Check for specific configuration files and frameworks
                config_files = {
                    # JavaScript/Node.js ecosystem
                    'package.json': 'javascript', 'yarn.lock': 'javascript', 'package-lock.json': 'javascript',
                    'webpack.config.js': 'javascript', 'rollup.config.js': 'javascript',
                    'vite.config.js': 'javascript', 'next.config.js': 'nextjs',
                    'nuxt.config.js': 'nuxt', 'nuxt.config.ts': 'nuxt',
                    'vue.config.js': 'vue', 'vue.config.ts': 'vue',
                    'angular.json': 'angular', 'angular-cli.json': 'angular',
                    'svelte.config.js': 'svelte', 'svelte.config.cjs': 'svelte', 'svelte.config.ts': 'svelte',
                    'remix.config.js': 'remix', 'remix.config.ts': 'remix',
                    'astro.config.js': 'astro', 'astro.config.mjs': 'astro', 'astro.config.ts': 'astro',
                    'gatsby-config.js': 'gatsby', 'gatsby-config.ts': 'gatsby',
                    'sanity.config.js': 'sanity', 'sanity.config.ts': 'sanity',
                    'tailwind.config.js': 'tailwind', 'tailwind.config.ts': 'tailwind',
                    'postcss.config.js': 'postcss', 'postcss.config.ts': 'postcss',
                    'babel.config.js': 'babel', 'babel.config.json': 'babel',
                    'jest.config.js': 'jest', 'jest.config.ts': 'jest',
                    'cypress.config.js': 'cypress', 'cypress.config.ts': 'cypress',
                    'playwright.config.js': 'playwright', 'playwright.config.ts': 'playwright',
                    'vitest.config.js': 'vitest', 'vitest.config.ts': 'vitest',
                    'eslint.config.js': 'eslint', 'eslint.config.mjs': 'eslint',
                    'prettier.config.js': 'prettier', 'prettier.config.json': 'prettier',
                    'tsconfig.json': 'typescript', 'jsconfig.json': 'javascript',
                    'turborepo.json': 'turborepo', 'nx.json': 'nx',
                    'lerna.json': 'lerna', 'rush.json': 'rush',
                    
                    # Python ecosystem
                    'requirements.txt': 'python', 'pyproject.toml': 'python', 'setup.py': 'python',
                    'Pipfile': 'python', 'poetry.lock': 'python', 'conda.yml': 'python',
                    'Django': 'django', 'Flask': 'flask', 'FastAPI': 'fastapi',
                    
                    # Java ecosystem
                    'pom.xml': 'java', 'build.gradle': 'java', 'build.gradle.kts': 'java',
                    'gradle.properties': 'java', 'settings.gradle': 'java',
                    'spring-boot': 'spring', 'maven': 'maven',
                    
                    # C# ecosystem
                    '*.csproj': 'csharp', '*.sln': 'csharp', '*.vbproj': 'vbnet',
                    'project.json': 'csharp', 'global.json': 'csharp',
                    
                    # Go
                    'go.mod': 'go', 'go.sum': 'go', 'Gopkg.toml': 'go',
                    
                    # Rust
                    'Cargo.toml': 'rust', 'Cargo.lock': 'rust',
                    
                    # PHP
                    'composer.json': 'php', 'composer.lock': 'php',
                    'laravel': 'laravel', 'symfony': 'symfony',
                    
                    # Ruby
                    'Gemfile': 'ruby', 'Gemfile.lock': 'ruby', 'Rakefile': 'ruby',
                    'rails': 'rails', 'sinatra': 'sinatra',
                    
                    # Web frameworks
                    'next.js': 'nextjs', 'nuxt.js': 'nuxt', 'gatsby': 'gatsby',
                    'svelte': 'svelte', 'vue': 'vue', 'react': 'react',
                    'angular': 'angular', 'ember': 'ember',
                    
                    # Mobile frameworks
                    'react-native': 'react-native', 'flutter': 'flutter',
                    'ionic': 'ionic', 'cordova': 'cordova',
                    
                    # Build tools
                    'Makefile': 'make', 'CMakeLists.txt': 'cmake',
                    'Dockerfile': 'docker', 'docker-compose.yml': 'docker',
                    'Jenkinsfile': 'jenkins', '.github/workflows': 'github-actions',
                    
                    # Configuration
                    'webpack': 'webpack', 'babel': 'babel', 'eslint': 'eslint',
                    'prettier': 'prettier', 'typescript': 'typescript',
                    'tailwind': 'tailwind', 'bootstrap': 'bootstrap',
                    
                    # Database
                    'prisma': 'prisma', 'sequelize': 'sequelize', 'mongoose': 'mongoose',
                    'typeorm': 'typeorm', 'sqlalchemy': 'sqlalchemy',
                    
                    # Testing
                    'jest': 'jest', 'mocha': 'mocha', 'cypress': 'cypress',
                    'pytest': 'pytest', 'unittest': 'unittest',
                    
                    # Documentation
                    'docusaurus': 'docusaurus', 'gitbook': 'gitbook',
                    'mkdocs': 'mkdocs', 'sphinx': 'sphinx'
                }
                
                # Check for framework-specific files
                for config_file, language in config_files.items():
                    if file_path.name == config_file or config_file in file_path.name:
                        if language not in languages:
                            languages.append(language)
        
        # Filter out documentation and configuration languages for main detection
        documentation_langs = {'markdown', 'text', 'log', 'json', 'yaml', 'xml', 'ini', 'config', 'sqlite', 'database'}
        main_languages = [lang for lang in languages if lang not in documentation_langs]
        
        # If we have main languages, return those; otherwise return all languages
        return sorted(main_languages) if main_languages else sorted(languages)
    
    def _detect_js_frameworks(self, project_path: Path) -> list:
        """Detect JavaScript frameworks by analyzing package.json and other config files"""
        frameworks = []
        
        # Check package.json for framework dependencies
        package_json_path = project_path / 'package.json'
        if package_json_path.exists():
            try:
                import json
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                # Check dependencies and devDependencies
                all_deps = {}
                all_deps.update(package_data.get('dependencies', {}))
                all_deps.update(package_data.get('devDependencies', {}))
                all_deps.update(package_data.get('peerDependencies', {}))
                
                # Framework detection based on dependencies
                framework_deps = {
                    # React ecosystem
                    'react': 'react', 'react-dom': 'react', 'next': 'nextjs',
                    'gatsby': 'gatsby', 'remix': 'remix',
                    
                    # Vue ecosystem
                    'vue': 'vue', 'nuxt': 'nuxt', 'vue-router': 'vue',
                    'vuex': 'vue', 'pinia': 'vue',
                    
                    # Angular ecosystem
                    '@angular/core': 'angular', '@angular/common': 'angular',
                    '@angular/platform-browser': 'angular',
                    
                    # Svelte ecosystem
                    'svelte': 'svelte', 'sveltekit': 'svelte',
                    
                    # Astro
                    'astro': 'astro',
                    
                    # Build tools
                    'vite': 'vite', 'webpack': 'webpack', 'rollup': 'rollup',
                    'parcel': 'parcel', 'esbuild': 'esbuild',
                    
                    # CSS frameworks
                    'tailwindcss': 'tailwind', 'bootstrap': 'bootstrap',
                    'bulma': 'bulma', 'materialize-css': 'materialize',
                    'antd': 'antd', 'chakra-ui': 'chakra', 'mantine': 'mantine',
                    
                    # Testing frameworks
                    'jest': 'jest', 'vitest': 'vitest', 'cypress': 'cypress',
                    'playwright': 'playwright', 'puppeteer': 'puppeteer',
                    'testing-library': 'testing-library',
                    
                    # State management
                    'redux': 'redux', 'mobx': 'mobx', 'zustand': 'zustand',
                    'jotai': 'jotai', 'recoil': 'recoil',
                    
                    # UI libraries
                    'material-ui': 'mui', '@mui/material': 'mui',
                    'ant-design': 'antd', 'semantic-ui-react': 'semantic',
                    'react-bootstrap': 'react-bootstrap',
                    
                    # Backend frameworks
                    'express': 'express', 'fastify': 'fastify', 'koa': 'koa',
                    'nest': 'nestjs', 'adonisjs': 'adonisjs',
                    
                    # Database ORMs
                    'prisma': 'prisma', 'sequelize': 'sequelize', 'mongoose': 'mongoose',
                    'typeorm': 'typeorm', 'drizzle': 'drizzle',
                    
                    # Full-stack frameworks
                    't3': 't3', 'blitz': 'blitz', 'redwood': 'redwood',
                    'sails': 'sails', 'strapi': 'strapi', 'keystone': 'keystone'
                }
                
                # Check for framework dependencies
                for dep, framework in framework_deps.items():
                    if dep in all_deps:
                        if framework not in frameworks:
                            frameworks.append(framework)
                
                # Check for specific framework patterns in package.json
                scripts = package_data.get('scripts', {})
                for script_name, script_content in scripts.items():
                    if isinstance(script_content, str):
                        if 'next' in script_content and 'nextjs' not in frameworks:
                            frameworks.append('nextjs')
                        elif 'nuxt' in script_content and 'nuxt' not in frameworks:
                            frameworks.append('nuxt')
                        elif 'gatsby' in script_content and 'gatsby' not in frameworks:
                            frameworks.append('gatsby')
                        elif 'remix' in script_content and 'remix' not in frameworks:
                            frameworks.append('remix')
                        elif 'astro' in script_content and 'astro' not in frameworks:
                            frameworks.append('astro')
                        elif 'svelte' in script_content and 'svelte' not in frameworks:
                            frameworks.append('svelte')
                
            except Exception as e:
                print(f"Error reading package.json: {e}")
        
        # Check for framework-specific config files
        framework_configs = {
            'next.config.js': 'nextjs', 'next.config.ts': 'nextjs',
            'nuxt.config.js': 'nuxt', 'nuxt.config.ts': 'nuxt',
            'vue.config.js': 'vue', 'vue.config.ts': 'vue',
            'angular.json': 'angular', 'angular-cli.json': 'angular',
            'svelte.config.js': 'svelte', 'svelte.config.ts': 'svelte',
            'remix.config.js': 'remix', 'remix.config.ts': 'remix',
            'astro.config.js': 'astro', 'astro.config.ts': 'astro',
            'gatsby-config.js': 'gatsby', 'gatsby-config.ts': 'gatsby',
            'tailwind.config.js': 'tailwind', 'tailwind.config.ts': 'tailwind',
            'vite.config.js': 'vite', 'vite.config.ts': 'vite',
            'webpack.config.js': 'webpack', 'webpack.config.ts': 'webpack',
            'rollup.config.js': 'rollup', 'rollup.config.ts': 'rollup',
            'jest.config.js': 'jest', 'jest.config.ts': 'jest',
            'cypress.config.js': 'cypress', 'cypress.config.ts': 'cypress',
            'playwright.config.js': 'playwright', 'playwright.config.ts': 'playwright',
            'vitest.config.js': 'vitest', 'vitest.config.ts': 'vitest'
        }
        
        for config_file, framework in framework_configs.items():
            if (project_path / config_file).exists():
                if framework not in frameworks:
                    frameworks.append(framework)
        
        return frameworks
    
    def _determine_primary_language(self, languages: list, project_path: Path) -> str:
        """Determine the primary language in a multi-language project"""
        # Language priority based on common project patterns
        language_priority = {
            # Web development
            'javascript': 10, 'typescript': 10, 'html': 8, 'css': 7,
            'vue': 9, 'react': 9, 'angular': 9, 'svelte': 9,
            'nextjs': 9, 'nuxt': 9, 'gatsby': 9,
            
            # Backend languages
            'python': 8, 'java': 8, 'csharp': 8, 'go': 8, 'rust': 8,
            'php': 7, 'ruby': 7, 'nodejs': 7,
            
            # Mobile development
            'swift': 8, 'dart': 8, 'kotlin': 8, 'react-native': 8,
            
            # System languages
            'c': 6, 'cpp': 6, 'assembly': 5,
            
            # Scripting
            'bash': 5, 'powershell': 5, 'lua': 4, 'perl': 4,
            
            # Data and documentation
            'sql': 4, 'markdown': 3, 'json': 3, 'yaml': 3
        }
        
        # Check for framework indicators that might indicate primary language
        framework_indicators = {
            'package.json': 'javascript',
            'requirements.txt': 'python',
            'Cargo.toml': 'rust',
            'go.mod': 'go',
            'pom.xml': 'java',
            'composer.json': 'php',
            'Gemfile': 'ruby'
        }
        
        # Check for framework files first
        for file_name, lang in framework_indicators.items():
            if (project_path / file_name).exists() and lang in languages:
                return lang
        
        # If no framework file, use priority system
        scored_languages = []
        for lang in languages:
            score = language_priority.get(lang, 1)
            scored_languages.append((score, lang))
        
        # Return highest priority language
        scored_languages.sort(reverse=True)
        return scored_languages[0][1] if scored_languages else languages[0]
    
    def detect_project_type(self, project_path: Path) -> tuple:
        """Detect project type, language, and framework with multi-language support"""
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
        
        # Detect all languages in the project
        languages = self._detect_languages(project_path)
        
        # If multiple languages detected, return specific languages
        if len(languages) > 1:
            # Determine primary language based on common patterns
            primary_lang = self._determine_primary_language(languages, project_path)
            return ('multi-language', f"{', '.join(languages)}", f"mixed ({primary_lang})")
        
        # Check for bash scripting projects
        bash_files = list(project_path.glob('*.sh'))
        if bash_files:
            # Check if it's a shell script collection or automation project
            if len(bash_files) > 1 or any('install' in f.name.lower() or 'setup' in f.name.lower() or 'deploy' in f.name.lower() for f in bash_files):
                return ('bash-automation', 'bash', 'shell')
            else:
                return ('bash-script', 'bash', 'shell')
        
        # Check for shell script directories
        shell_dirs = ['scripts', 'bin', 'tools', 'automation']
        for shell_dir in shell_dirs:
            if (project_path / shell_dir).exists():
                shell_files = list((project_path / shell_dir).glob('*.sh'))
                if shell_files:
                    return ('bash-automation', 'bash', 'shell')
        
        for file_name, (project_type, language, framework) in files_to_check.items():
            if (project_path / file_name).exists():
                return project_type, language, framework
        
        if (project_path / 'src').exists():
            return 'generic', 'unknown', 'unknown'
        
        return 'unknown', 'unknown', 'unknown'
    
    def get_directory_size(self, path: Path) -> str:
        """Get human-readable directory size"""
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024.0:
                return f"{total_size:.1f} {unit}"
            total_size /= 1024.0
        return f"{total_size:.1f} TB"
    
    def calculate_health_score(self, project_path: Path, language: str) -> int:
        """Calculate comprehensive project health score (0-100) with multi-language support"""
        score = 100
        
        # Detect if this is a multi-language project
        languages = self._detect_languages(project_path)
        is_multi_language = len(languages) > 1
        
        # === ESSENTIAL DOCUMENTATION ===
        if not (project_path / 'README.md').exists():
            score -= 10
        if not (project_path / '.gitignore').exists():
            score -= 5
        
        # === TESTING INFRASTRUCTURE ===
        test_dirs = ['tests', 'test', '__tests__', 'spec', 'test_', 'tests_']
        test_files = ['test_*.py', '*_test.py', '*.test.js', '*.spec.js', '*.test.ts']
        has_tests = any((project_path / test_dir).exists() for test_dir in test_dirs)
        has_test_files = any(project_path.glob(pattern) for pattern in test_files)
        if not has_tests and not has_test_files:
            score -= 15
        
        # === DOCUMENTATION ===
        doc_dirs = ['docs', 'documentation', 'doc', 'wiki']
        doc_files = ['CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE', 'LICENSE.txt', 'LICENSE.md']
        has_docs = any((project_path / doc_dir).exists() for doc_dir in doc_dirs)
        has_doc_files = any((project_path / doc_file).exists() for doc_file in doc_files)
        if not has_docs and not has_doc_files:
            score -= 5
        
        # === VERSION CONTROL ===
        if not (project_path / '.git').exists():
            score -= 10  # No git repository
        else:
            # Check for git hooks
            git_hooks = project_path / '.git' / 'hooks'
            if git_hooks.exists() and any(git_hooks.glob('*')):
                score += 2  # Bonus for git hooks
        
        # === SECURITY CHECKS ===
        security_files = ['.env.example', 'security.md', 'SECURITY.md']
        has_security = any((project_path / sec_file).exists() for sec_file in security_files)
        if not has_security:
            score -= 3
        
        # Check for hardcoded secrets (basic check)
        secret_patterns = ['password', 'secret', 'key', 'token', 'api_key']
        has_secrets = False
        for file_path in project_path.rglob('*.py'):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        if any(pattern in content for pattern in secret_patterns):
                            has_secrets = True
                            break
                except:
                    pass
        if has_secrets:
            score -= 5  # Potential security issue
        
        # === MULTI-LANGUAGE PROJECT BONUS ===
        if is_multi_language:
            score += 5  # Bonus for multi-language projects (complexity management)
            
            # Check for cross-language integration
            if self._check_cross_language_integration(project_path, languages):
                score += 3  # Bonus for good integration
        
        # === LANGUAGE-SPECIFIC CHECKS ===
        if is_multi_language:
            # For multi-language projects, check all languages
            for lang in languages:
                if lang == 'python':
                    score += self._check_python_health(project_path) // 2  # Reduced weight for multi-lang
                elif lang == 'javascript':
                    score += self._check_javascript_health(project_path) // 2
                elif lang == 'rust':
                    score += self._check_rust_health(project_path) // 2
                elif lang == 'go':
                    score += self._check_go_health(project_path) // 2
                elif lang == 'java':
                    score += self._check_java_health(project_path) // 2
                elif lang == 'bash':
                    score += self._check_bash_health(project_path) // 2
        else:
            # Single language projects get full weight
            if language == 'python':
                score += self._check_python_health(project_path)
            elif language == 'javascript':
                score += self._check_javascript_health(project_path)
            elif language == 'rust':
                score += self._check_rust_health(project_path)
            elif language == 'go':
                score += self._check_go_health(project_path)
            elif language == 'java':
                score += self._check_java_health(project_path)
            elif language == 'bash':
                score += self._check_bash_health(project_path)
        
        # === DEPENDENCY MANAGEMENT ===
        dep_files = {
            'python': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile'],
            'javascript': ['package.json', 'yarn.lock', 'package-lock.json'],
            'rust': ['Cargo.toml'],
            'go': ['go.mod', 'go.sum'],
            'java': ['pom.xml', 'build.gradle', 'gradle.properties'],
            'bash': ['requirements.txt', 'dependencies.txt', 'packages.txt', 'install.sh']
        }
        
        if is_multi_language:
            # For multi-language projects, check dependencies for each language
            missing_deps = 0
            for lang in languages:
                if lang in dep_files:
                    has_dep_file = any((project_path / dep_file).exists() for dep_file in dep_files[lang])
                    if not has_dep_file:
                        missing_deps += 1
            if missing_deps > 0:
                score -= missing_deps * 4  # Penalty per missing language dependency
        else:
            # Single language dependency check
            if language in dep_files:
                has_dep_file = any((project_path / dep_file).exists() for dep_file in dep_files[language])
                if not has_dep_file:
                    score -= 8
        
        # === CONFIGURATION FILES ===
        config_files = ['.editorconfig', '.gitattributes', 'docker-compose.yml', 'Dockerfile']
        has_config = any((project_path / config_file).exists() for config_file in config_files)
        if has_config:
            score += 3  # Bonus for good configuration
        
        # === CODE QUALITY INDICATORS ===
        # Check for linting configuration
        lint_files = ['.eslintrc', '.eslintrc.js', '.eslintrc.json', '.pylintrc', 'pyproject.toml']
        has_linting = any((project_path / lint_file).exists() for lint_file in lint_files)
        if has_linting:
            score += 2
        
        # Check for CI/CD
        ci_dirs = ['.github', '.gitlab-ci', '.circleci', '.travis', '.jenkins']
        has_ci = any((project_path / ci_dir).exists() for ci_dir in ci_dirs)
        if has_ci:
            score += 5  # Bonus for CI/CD
        
        # === PROJECT STRUCTURE ===
        # Check for proper source organization
        src_dirs = ['src', 'lib', 'app', 'source']
        has_src = any((project_path / src_dir).exists() for src_dir in src_dirs)
        if has_src:
            score += 2
        
        # Check for build/compilation files
        build_files = ['Makefile', 'CMakeLists.txt', 'build.sh', 'compile.sh']
        has_build = any((project_path / build_file).exists() for build_file in build_files)
        if has_build:
            score += 2
        
        # === MAINTENANCE INDICATORS ===
        # Check for recent activity (files modified in last 30 days)
        recent_files = 0
        try:
            for file_path in project_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    if (datetime.datetime.now() - datetime.datetime.fromtimestamp(file_path.stat().st_mtime)).days < 30:
                        recent_files += 1
                        if recent_files >= 3:  # At least 3 recent files
                            score += 2
                            break
        except:
            pass
        
        # === SIZE AND COMPLEXITY ===
        # Check for reasonable project size (not too small, not too large)
        try:
            total_files = len(list(project_path.rglob('*')))
            if total_files < 3:
                score -= 5  # Too small, might be incomplete
            elif total_files > 1000:
                score -= 2  # Very large, might need organization
        except:
            pass
        
        return max(0, min(100, score))  # Ensure score is between 0-100
    
    def _check_python_health(self, project_path: Path) -> int:
        """Check Python-specific health indicators"""
        score = 0
        
        # Check for virtual environment
        venv_dirs = ['venv', 'env', '.venv', '.env']
        if any((project_path / venv_dir).exists() for venv_dir in venv_dirs):
            score += 2
        
        # Check for requirements.txt with pinned versions
        req_file = project_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    content = f.read()
                    if '==' in content or '>=' in content:
                        score += 2  # Pinned versions
            except:
                pass
        
        # Check for __init__.py files (proper Python package structure)
        init_files = list(project_path.rglob('__init__.py'))
        if len(init_files) > 0:
            score += 1
        
        return score
    
    def _check_javascript_health(self, project_path: Path) -> int:
        """Check JavaScript-specific health indicators"""
        score = 0
        
        # Check for package.json with proper scripts
        pkg_file = project_path / 'package.json'
        if pkg_file.exists():
            try:
                with open(pkg_file, 'r') as f:
                    import json
                    pkg_data = json.load(f)
                    if 'scripts' in pkg_data and len(pkg_data['scripts']) > 0:
                        score += 2
                    if 'devDependencies' in pkg_data:
                        score += 1
            except:
                pass
        
        # Check for node_modules (dependencies installed)
        if (project_path / 'node_modules').exists():
            score += 1
        
        return score
    
    def _check_rust_health(self, project_path: Path) -> int:
        """Check Rust-specific health indicators"""
        score = 0
        
        # Check for Cargo.toml with proper metadata
        cargo_file = project_path / 'Cargo.toml'
        if cargo_file.exists():
            try:
                with open(cargo_file, 'r') as f:
                    content = f.read()
                    if 'version' in content and 'authors' in content:
                        score += 2
                    if 'dependencies' in content:
                        score += 1
            except:
                pass
        
        # Check for Cargo.lock (dependencies locked)
        if (project_path / 'Cargo.lock').exists():
            score += 1
        
        return score
    
    def _check_go_health(self, project_path: Path) -> int:
        """Check Go-specific health indicators"""
        score = 0
        
        # Check for go.mod with proper module declaration
        go_mod = project_path / 'go.mod'
        if go_mod.exists():
            try:
                with open(go_mod, 'r') as f:
                    content = f.read()
                    if 'module' in content:
                        score += 2
            except:
                pass
        
        # Check for go.sum (dependencies locked)
        if (project_path / 'go.sum').exists():
            score += 1
        
        return score
    
    def _check_java_health(self, project_path: Path) -> int:
        """Check Java-specific health indicators"""
        score = 0
        
        # Check for Maven or Gradle
        if (project_path / 'pom.xml').exists() or (project_path / 'build.gradle').exists():
            score += 2
        
        # Check for proper Java package structure
        java_files = list(project_path.rglob('*.java'))
        if len(java_files) > 0:
            score += 1
        
        return score
    
    def _check_bash_health(self, project_path: Path) -> int:
        """Check Bash-specific health indicators"""
        score = 0
        
        # Check for shell script files
        bash_files = list(project_path.glob('*.sh'))
        if bash_files:
            score += 2  # Has shell scripts
        
        # Check for proper shebang in scripts
        proper_shebang = False
        for bash_file in bash_files:
            try:
                with open(bash_file, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#!/bin/bash') or first_line.startswith('#!/usr/bin/env bash'):
                        proper_shebang = True
                        break
            except:
                pass
        
        if proper_shebang:
            score += 2  # Proper shebang
        
        # Check for error handling in scripts
        error_handling = False
        for bash_file in bash_files:
            try:
                with open(bash_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'set -e' in content or 'set -o errexit' in content or 'trap' in content:
                        error_handling = True
                        break
            except:
                pass
        
        if error_handling:
            score += 2  # Good error handling
        
        # Check for logging in scripts
        logging = False
        for bash_file in bash_files:
            try:
                with open(bash_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'echo' in content and ('log' in content or 'Log' in content):
                        logging = True
                        break
            except:
                pass
        
        if logging:
            score += 1  # Has logging
        
        # Check for configuration files
        config_files = ['config.sh', 'settings.sh', '.env', 'config.json']
        has_config = any((project_path / config_file).exists() for config_file in config_files)
        if has_config:
            score += 1  # Has configuration
        
        # Check for documentation in scripts (comments)
        documented_scripts = 0
        for bash_file in bash_files:
            try:
                with open(bash_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    comment_lines = len([line for line in content.split('\n') if line.strip().startswith('#')])
                    total_lines = len([line for line in content.split('\n') if line.strip()])
                    if total_lines > 0 and comment_lines / total_lines > 0.1:  # At least 10% comments
                        documented_scripts += 1
            except:
                pass
        
        if documented_scripts > 0:
            score += 1  # Well-documented scripts
        
        # Check for automation/CI integration
        automation_files = ['install.sh', 'setup.sh', 'deploy.sh', 'build.sh', 'test.sh']
        has_automation = any((project_path / auto_file).exists() for auto_file in automation_files)
        if has_automation:
            score += 2  # Has automation scripts
        
        return score
    
    def _has_dependency_files(self, project_path: Path, language: str) -> bool:
        """Check if project has appropriate dependency files"""
        dep_files = {
            'python': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile'],
            'javascript': ['package.json', 'yarn.lock', 'package-lock.json'],
            'rust': ['Cargo.toml'],
            'go': ['go.mod', 'go.sum'],
            'java': ['pom.xml', 'build.gradle', 'gradle.properties'],
            'bash': ['requirements.txt', 'dependencies.txt', 'packages.txt', 'install.sh']
        }
        
        if language in dep_files:
            return any((project_path / dep_file).exists() for dep_file in dep_files[language])
        return False
    
    def _get_health_recommendations(self, project_path: Path, health_score: int) -> str:
        """Get specific recommendations to improve project health"""
        recommendations = []
        
        if health_score >= 90:
            return "🎉 Excellent! Your project is in great shape. Keep up the good work!"
        
        if not (project_path / 'README.md').exists():
            recommendations.append("📝 Add a README.md file with project description and setup instructions")
        
        if not (project_path / '.git').exists():
            recommendations.append("🔧 Initialize a Git repository: git init")
        
        if not (project_path / '.gitignore').exists():
            recommendations.append("🚫 Create a .gitignore file to exclude unnecessary files")
        
        test_dirs = ['tests', 'test', '__tests__', 'spec']
        if not any((project_path / test_dir).exists() for test_dir in test_dirs):
            recommendations.append("🧪 Add a test directory and write unit tests")
        
        doc_dirs = ['docs', 'documentation', 'doc']
        if not any((project_path / doc_dir).exists() for doc_dir in doc_dirs):
            recommendations.append("📚 Create a docs/ directory for additional documentation")
        
        if not any((project_path / sec_file).exists() for sec_file in ['.env.example', 'security.md', 'SECURITY.md']):
            recommendations.append("🔒 Add security documentation and .env.example file")
        
        ci_dirs = ['.github', '.gitlab-ci', '.circleci']
        if not any((project_path / ci_dir).exists() for ci_dir in ci_dirs):
            recommendations.append("⚙️ Set up CI/CD pipeline for automated testing and deployment")
        
        config_files = ['.editorconfig', '.gitattributes']
        if not any((project_path / config_file).exists() for config_file in config_files):
            recommendations.append("⚙️ Add configuration files like .editorconfig and .gitattributes")
        
        if health_score < 50:
            recommendations.append("🚨 This project needs significant attention. Consider refactoring and adding missing components.")
        
        return "\n".join(f"• {rec}" for rec in recommendations) if recommendations else "✅ No specific recommendations at this time."
    
    def get_project_status(self, project_path: Path) -> str:
        """Get project status"""
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
    
    def refresh_projects(self):
        """Refresh projects list with smart hierarchical structure"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add projects to tree
        if not self.projects:
            # Insert a message when no projects are found
            self.tree.insert('', 'end', text="No projects found", 
                           values=("", "", "", "", "", ""))
        else:
            # Group projects by hierarchy
            root_projects = [p for p in self.projects if p.get('parent') is None]
            sub_projects = [p for p in self.projects if p.get('parent') is not None]
            
            print(f"Hierarchy: {len(root_projects)} root projects, {len(sub_projects)} sub-projects")
            
            # Add root projects with their sub-projects
            for root_project in root_projects:
                self._add_project_to_tree(root_project, self.projects)
        
        # Check scrollbar visibility after loading projects
        self.root.after(100, self._check_scrollbar_visibility)
    
    def _add_project_to_tree(self, project, all_projects, parent_item=''):
        """Add a project to the tree with proper hierarchical structure"""
        # Use project name without indentation (tree handles hierarchy)
        display_name = project['name']
        
        # Debug info
        parent_info = f" (parent: {parent_item})" if parent_item else " (root)"
        print(f"  Adding to tree: {display_name}{parent_info}")
        
        # Add project to tree
        health_color = "green" if project['health'] >= 80 else "yellow" if project['health'] >= 60 else "red"
        item_id = self.tree.insert(parent_item, 'end', text=display_name, 
                           values=(project['type'], project['language'], project['status'], 
                                 f"{project['health']}%", project['size'], project['modified']))
        
        # Find and add sub-projects
        project_path = project.get('path', '')
        sub_projects = [p for p in all_projects if p.get('parent') == project_path]
        
        print(f"    Looking for sub-projects of {project_path}: found {len(sub_projects)}")
        
        # If there are sub-projects, add them as children (collapsed by default)
        if sub_projects:
            for sub_project in sub_projects:
                print(f"    Adding sub-project: {sub_project['name']}")
                self._add_project_to_tree(sub_project, all_projects, item_id)
            # Keep parent collapsed initially to show hierarchy
            self.tree.item(item_id, open=False)
            print(f"    Set {display_name} to collapsed")
    
    def on_tree_expand(self, event):
        """Handle tree expansion with lazy loading"""
        item = self.tree.focus()
        if not item:
            return
        
        # Mark as loaded to prevent re-analysis
        self.loaded_items.add(item)
        
        # If this is a collection folder, load its sub-projects lazily
        if self.tree.item(item, 'values')[0] == 'Collection':  # Check if it's a collection
            self.load_collection_subprojects(item)
    
    def on_tree_collapse(self, event):
        """Handle tree collapse"""
        # No special handling needed for collapse
        pass
    
    def load_collection_subprojects(self, parent_item):
        """Load sub-projects for a collection folder lazily"""
        try:
            # Get the project path from the item
            item_text = self.tree.item(parent_item, 'text')
            project_path = None
            
            # Find the project in our projects list
            for project in self.projects:
                if project['name'] == item_text:
                    project_path = Path(project['path'])
                    break
            
            if not project_path or not project_path.exists():
                return
            
            # Check if this is a collection folder
            if not self._is_collection_folder(project_path):
                return
            
            # Get existing children to avoid duplicates
            existing_children = self.tree.get_children(parent_item)
            if existing_children:
                return  # Already loaded
            
            # Load sub-projects with quick analysis only
            subdirs = [d for d in project_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
            
            for subdir in subdirs[:10]:  # Limit to 10 for performance
                if self._has_project_indicators(subdir):
                    # Quick analysis only - no heavy computation
                    project_info = self._quick_analyze_project(subdir)
                    if project_info:
                        # Add to tree with minimal data
                        child_item = self.tree.insert(parent_item, 'end', 
                                                   text=project_info['name'],
                                                   values=('Quick', 'Loading...', 'Loading...', 'Loading...', 'Loading...', 'Loading...'))
                        
                        # Store the project info for later use
                        self.tree.set(child_item, 'project_path', str(subdir))
                        
        except Exception as e:
            print(f"Error loading collection subprojects: {e}")
    
    def show_context_menu(self, event):
        """Show comprehensive right-click context menu"""
        # Get the item under the cursor
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # Select the item if not already selected
        if item not in self.tree.selection():
            self.tree.selection_set(item)
        
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0, bg=self.colors['bg_secondary'], 
                              fg=self.colors['text_primary'], activebackground=self.colors['accent'],
                              activeforeground=self.colors['text_primary'])
        
        # Get selected items
        selected_items = self.tree.selection()
        is_multiple = len(selected_items) > 1
        
        # === PROJECT MANAGEMENT ===
        context_menu.add_command(label="📁 Open in Explorer", command=self.open_in_explorer)
        context_menu.add_command(label="🔍 Analyze Project", command=self.analyze_selected_projects)
        context_menu.add_command(label="📊 Generate Report", command=self.generate_project_report)
        context_menu.add_separator()
        
        # === DEVELOPMENT TOOLS ===
        dev_menu = tk.Menu(context_menu, tearoff=0, bg=self.colors['bg_secondary'], 
                          fg=self.colors['text_primary'], activebackground=self.colors['accent'])
        dev_menu.add_command(label="🔧 Open in VS Code", command=self.open_in_vscode)
        dev_menu.add_command(label="💻 Open Terminal", command=self.open_terminal)
        dev_menu.add_command(label="📝 Open in IDE", command=self.open_in_ide)
        dev_menu.add_command(label="🌐 Open in Browser", command=self.open_in_browser)
        context_menu.add_cascade(label="🛠️ Development Tools", menu=dev_menu)
        
        # === GIT OPERATIONS ===
        git_menu = tk.Menu(context_menu, tearoff=0, bg=self.colors['bg_secondary'], 
                           fg=self.colors['text_primary'], activebackground=self.colors['accent'])
        git_menu.add_command(label="📋 Git Status", command=self.git_status)
        git_menu.add_command(label="🔄 Git Pull", command=self.git_pull)
        git_menu.add_command(label="📤 Git Push", command=self.git_push)
        git_menu.add_command(label="🌿 Create Branch", command=self.create_branch)
        git_menu.add_separator()
        git_menu.add_command(label="📊 Git Log", command=self.git_log)
        git_menu.add_command(label="📈 Git Statistics", command=self.git_statistics)
        context_menu.add_cascade(label="📚 Git Operations", menu=git_menu)
        
        # === PROJECT OPERATIONS ===
        if is_multiple:
            context_menu.add_command(label="📦 Bulk Operations", command=self.bulk_operations)
            context_menu.add_separator()
        
        context_menu.add_command(label="📋 Copy Project Info", command=self.copy_project_info)
        context_menu.add_command(label="📁 Duplicate Project", command=self.duplicate_project)
        context_menu.add_command(label="📤 Export Project", command=self.export_project)
        context_menu.add_separator()
        
        # === HEALTH & ANALYSIS ===
        health_menu = tk.Menu(context_menu, tearoff=0, bg=self.colors['bg_secondary'], 
                             fg=self.colors['text_primary'], activebackground=self.colors['accent'])
        health_menu.add_command(label="🔍 Deep Analysis", command=self.deep_analysis)
        health_menu.add_command(label="🔒 Security Scan", command=self.security_scan)
        health_menu.add_command(label="📊 Performance Check", command=self.performance_check)
        health_menu.add_command(label="🧪 Test Coverage", command=self.test_coverage)
        health_menu.add_command(label="📦 Dependency Check", command=self.dependency_check)
        context_menu.add_cascade(label="🏥 Health & Analysis", menu=health_menu)
        
        # === AUTOMATION ===
        auto_menu = tk.Menu(context_menu, tearoff=0, bg=self.colors['bg_secondary'], 
                           fg=self.colors['text_primary'], activebackground=self.colors['accent'])
        auto_menu.add_command(label="🔄 Auto-Update Dependencies", command=self.auto_update_dependencies)
        auto_menu.add_command(label="🧹 Auto-Cleanup", command=self.auto_cleanup)
        auto_menu.add_command(label="📝 Auto-Generate Docs", command=self.auto_generate_docs)
        auto_menu.add_command(label="🧪 Run Tests", command=self.run_tests)
        auto_menu.add_command(label="🏗️ Build Project", command=self.build_project)
        context_menu.add_cascade(label="🤖 Automation", menu=auto_menu)
        
        # === ADVANCED FEATURES ===
        advanced_menu = tk.Menu(context_menu, tearoff=0, bg=self.colors['bg_secondary'], 
                              fg=self.colors['text_primary'], activebackground=self.colors['accent'])
        advanced_menu.add_command(label="🔍 Code Quality Analysis", command=self.code_quality_analysis)
        advanced_menu.add_command(label="📈 Performance Profiling", command=self.performance_profiling)
        advanced_menu.add_command(label="🔒 Security Audit", command=self.security_audit)
        advanced_menu.add_command(label="📊 Bundle Analysis", command=self.bundle_analysis)
        advanced_menu.add_command(label="🌐 API Documentation", command=self.generate_api_docs)
        context_menu.add_cascade(label="🚀 Advanced Features", menu=advanced_menu)
        
        # === PROJECT SETTINGS ===
        context_menu.add_separator()
        context_menu.add_command(label="⚙️ Project Settings", command=self.project_settings)
        context_menu.add_command(label="🏷️ Add Tags", command=self.add_project_tags)
        context_menu.add_command(label="📝 Add Notes", command=self.add_project_notes)
        
        # === DANGER ZONE ===
        context_menu.add_separator()
        danger_menu = tk.Menu(context_menu, tearoff=0, bg=self.colors['bg_secondary'], 
                             fg=self.colors['error'], activebackground=self.colors['error'],
                             activeforeground=self.colors['text_primary'])
        danger_menu.add_command(label="🗑️ Delete Project", command=self.delete_project)
        danger_menu.add_command(label="📦 Archive Project", command=self.archive_project)
        context_menu.add_cascade(label="⚠️ Danger Zone", menu=danger_menu)
        
        # Show the context menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def toggle_project_expansion(self, event):
        """Toggle project expansion/collapse on double-click"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        # Toggle the item's open/closed state
        if self.tree.item(item, 'open'):
            self.tree.item(item, open=False)
        else:
            self.tree.item(item, open=True)
    
    def show_project_details(self, event):
        """Show project details with lazy loading"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        display_name = item['text']
        
        # Extract actual project name (remove indentation)
        project_name = display_name.strip()
        
        # Check if this is a lazy-loaded item that needs full analysis
        project_path = self.tree.set(item, 'project_path')
        if project_path and project_path != '':
            # This is a lazy-loaded item, do full analysis now
            try:
                full_project_info = self.analyze_project(Path(project_path))
                if full_project_info:
                    # Update the tree item with full details
                    self.tree.item(item, values=(
                        full_project_info.get('type', 'Unknown'),
                        full_project_info.get('language', 'Unknown'),
                        full_project_info.get('status', 'Unknown'),
                        f"{full_project_info.get('health', 0)}%",
                        full_project_info.get('size', 'Unknown'),
                        full_project_info.get('modified', 'Unknown')
                    ))
                    project_info = full_project_info
                else:
                    return
            except Exception as e:
                print(f"Error analyzing lazy-loaded project: {e}")
                return
        else:
            # Find project info by matching the actual project name
            project_info = None
            for project in self.projects:
                if project['name'] == project_name or project['name'] in display_name:
                    project_info = project
                    break
            
            if not project_info:
                return
        
        # Display comprehensive details
        health_score = project_info['health']
        health_status = "🟢 Healthy" if health_score >= 80 else "🟡 Warning" if health_score >= 60 else "🔴 Critical"
    
    # === CONTEXT MENU METHODS ===
    
    def open_in_explorer(self):
        """Open selected project in file explorer"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                import subprocess
                import platform
                try:
                    if platform.system() == "Windows":
                        subprocess.run(["explorer", str(project_path)], check=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", str(project_path)], check=True)
                    else:  # Linux
                        subprocess.run(["xdg-open", str(project_path)], check=True)
                except Exception as e:
                    print(f"Error opening explorer: {e}")
    
    def analyze_selected_projects(self):
        """Analyze selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🔍 Analyzing selected projects...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Force full analysis
                    project_info = self.analyze_project(project_path)
                    if project_info:
                        # Update tree item with new data
                        self.tree.item(item, values=(
                            project_info.get('type', 'Unknown'),
                            project_info.get('language', 'Unknown'),
                            project_info.get('status', 'Unknown'),
                            f"{project_info.get('health', 0)}%",
                            project_info.get('size', 'Unknown'),
                            project_info.get('modified', 'Unknown')
                        ))
                except Exception as e:
                    print(f"Error analyzing project: {e}")
        
        self.status_var.set("✅ Analysis complete")
        self.refresh_projects()
    
    def generate_project_report(self):
        """Generate comprehensive project report"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        report_data = []
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    project_info = self.analyze_project(project_path)
                    if project_info:
                        report_data.append(project_info)
                except Exception as e:
                    print(f"Error generating report for {project_path}: {e}")
        
        if report_data:
            self._show_report_dialog(report_data)
    
    def open_in_vscode(self):
        """Open project in VS Code"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import subprocess
                    subprocess.run(["code", str(project_path)], check=True)
                except Exception as e:
                    print(f"Error opening in VS Code: {e}")
    
    def open_terminal(self):
        """Open terminal in project directory"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import subprocess
                    import platform
                    if platform.system() == "Windows":
                        subprocess.run(["cmd", "/c", "start", "cmd", "/k", f"cd /d {project_path}"], check=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", "-a", "Terminal", str(project_path)], check=True)
                    else:  # Linux
                        subprocess.run(["gnome-terminal", "--working-directory", str(project_path)], check=True)
                except Exception as e:
                    print(f"Error opening terminal: {e}")
    
    def open_in_ide(self):
        """Open project in IDE (auto-detect)"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Try to detect IDE based on project type
                    if (project_path / "package.json").exists():
                        # Node.js project - try VS Code
                        import subprocess
                        subprocess.run(["code", str(project_path)], check=True)
                    elif (project_path / "pom.xml").exists():
                        # Java project - try IntelliJ
                        import subprocess
                        subprocess.run(["idea", str(project_path)], check=True)
                    else:
                        # Default to VS Code
                        import subprocess
                        subprocess.run(["code", str(project_path)], check=True)
                except Exception as e:
                    print(f"Error opening in IDE: {e}")
    
    def open_in_browser(self):
        """Open project in browser (if it has a web interface)"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Look for common web files
                    web_files = ["index.html", "index.htm", "app.html", "main.html"]
                    for web_file in web_files:
                        if (project_path / web_file).exists():
                            import webbrowser
                            webbrowser.open(f"file://{project_path / web_file}")
                            break
                except Exception as e:
                    print(f"Error opening in browser: {e}")
    
    def _get_project_path_from_item(self, item):
        """Get project path from tree item"""
        try:
            # Check if it's a lazy-loaded item
            project_path = self.tree.set(item, 'project_path')
            if project_path and project_path != '':
                return Path(project_path)
            
            # Otherwise, find in projects list
            item_text = self.tree.item(item, 'text')
            for project in self.projects:
                if project['name'] == item_text:
                    return Path(project['path'])
        except Exception as e:
            print(f"Error getting project path: {e}")
        return None
    
    def _check_scrollbar_visibility(self, event=None):
        """Check if horizontal scrollbar should be visible and position it correctly"""
        try:
            # Get the tree's content width
            self.tree.update_idletasks()
            
            # Check if content is wider than the tree widget
            tree_width = self.tree.winfo_width()
            content_width = self.tree.column('#0', 'width', None)
            
            # Add width of other columns
            for col in self.tree['columns']:
                col_width = self.tree.column(col, 'width', None)
                if col_width:
                    content_width += col_width
            
            # Show/hide horizontal scrollbar based on content width
            if content_width > tree_width and tree_width > 0:
                # Content is wider than tree - show scrollbar
                if not self.h_scrollbar.winfo_viewable():
                    self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=(0, 0, 0, 0))
            else:
                # Content fits - hide scrollbar
                if self.h_scrollbar.winfo_viewable():
                    self.h_scrollbar.pack_forget()
                    
        except Exception as e:
            # Silently handle any errors to avoid disrupting the UI
            pass
    
    # === GIT OPERATIONS ===
    
    def git_status(self):
        """Show Git status for selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import subprocess
                    result = subprocess.run(["git", "status", "--porcelain"], 
                                          cwd=project_path, capture_output=True, text=True)
                    if result.returncode == 0:
                        self._show_git_status_dialog(project_path.name, result.stdout)
                    else:
                        print(f"Not a Git repository: {project_path.name}")
                except Exception as e:
                    print(f"Error getting Git status: {e}")
    
    def git_pull(self):
        """Pull latest changes for Git repositories"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🔄 Pulling latest changes...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import subprocess
                    result = subprocess.run(["git", "pull"], cwd=project_path, 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✅ Pulled changes for {project_path.name}")
                    else:
                        print(f"❌ Error pulling {project_path.name}: {result.stderr}")
                except Exception as e:
                    print(f"Error pulling changes: {e}")
        
        self.status_var.set("✅ Git pull complete")
    
    def git_push(self):
        """Push changes for Git repositories"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("📤 Pushing changes...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import subprocess
                    result = subprocess.run(["git", "push"], cwd=project_path, 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✅ Pushed changes for {project_path.name}")
                    else:
                        print(f"❌ Error pushing {project_path.name}: {result.stderr}")
                except Exception as e:
                    print(f"Error pushing changes: {e}")
        
        self.status_var.set("✅ Git push complete")
    
    def create_branch(self):
        """Create new Git branch"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Get branch name from user
        branch_name = tk.simpledialog.askstring("Create Branch", "Enter branch name:")
        if not branch_name:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import subprocess
                    result = subprocess.run(["git", "checkout", "-b", branch_name], 
                                          cwd=project_path, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✅ Created branch '{branch_name}' for {project_path.name}")
                    else:
                        print(f"❌ Error creating branch: {result.stderr}")
                except Exception as e:
                    print(f"Error creating branch: {e}")
    
    def git_log(self):
        """Show Git log for selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import subprocess
                    result = subprocess.run(["git", "log", "--oneline", "-10"], 
                                          cwd=project_path, capture_output=True, text=True)
                    if result.returncode == 0:
                        self._show_git_log_dialog(project_path.name, result.stdout)
                    else:
                        print(f"Not a Git repository: {project_path.name}")
                except Exception as e:
                    print(f"Error getting Git log: {e}")
    
    def git_statistics(self):
        """Show Git statistics for selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import subprocess
                    # Get commit count
                    commit_result = subprocess.run(["git", "rev-list", "--count", "HEAD"], 
                                                 cwd=project_path, capture_output=True, text=True)
                    # Get contributors
                    contrib_result = subprocess.run(["git", "shortlog", "-sn"], 
                                                  cwd=project_path, capture_output=True, text=True)
                    
                    stats = f"Commits: {commit_result.stdout.strip()}\n\nContributors:\n{contrib_result.stdout}"
                    self._show_git_stats_dialog(project_path.name, stats)
                except Exception as e:
                    print(f"Error getting Git statistics: {e}")
    
    # === BULK OPERATIONS ===
    
    def bulk_operations(self):
        """Show bulk operations dialog for multiple projects"""
        selected_items = self.tree.selection()
        if len(selected_items) < 2:
            return
        
        # Create bulk operations dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("📦 Bulk Operations")
        dialog.geometry("500x400")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Create bulk operations interface
        ttk.Label(dialog, text=f"Bulk Operations for {len(selected_items)} projects", 
                 style='Title.TLabel').pack(pady=10)
        
        # Operation buttons
        operations_frame = ttk.Frame(dialog, style='TFrame')
        operations_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Button(operations_frame, text="🔄 Update All Dependencies", 
                  command=lambda: self._bulk_update_dependencies(selected_items)).pack(fill=tk.X, pady=5)
        ttk.Button(operations_frame, text="🧹 Clean All Projects", 
                  command=lambda: self._bulk_clean_projects(selected_items)).pack(fill=tk.X, pady=5)
        ttk.Button(operations_frame, text="🧪 Run All Tests", 
                  command=lambda: self._bulk_run_tests(selected_items)).pack(fill=tk.X, pady=5)
        ttk.Button(operations_frame, text="📊 Generate All Reports", 
                  command=lambda: self._bulk_generate_reports(selected_items)).pack(fill=tk.X, pady=5)
        ttk.Button(operations_frame, text="📤 Export All Projects", 
                  command=lambda: self._bulk_export_projects(selected_items)).pack(fill=tk.X, pady=5)
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def _bulk_update_dependencies(self, selected_items):
        """Bulk update dependencies for selected projects"""
        self.status_var.set("🔄 Updating dependencies...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Check for package.json (Node.js)
                    if (project_path / "package.json").exists():
                        import subprocess
                        subprocess.run(["npm", "update"], cwd=project_path, check=True)
                        print(f"✅ Updated dependencies for {project_path.name}")
                except Exception as e:
                    print(f"Error updating dependencies for {project_path.name}: {e}")
        
        self.status_var.set("✅ Bulk dependency update complete")
    
    def _bulk_clean_projects(self, selected_items):
        """Bulk clean selected projects"""
        self.status_var.set("🧹 Cleaning projects...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Clean common build artifacts
                    import shutil
                    clean_dirs = ["node_modules", "dist", "build", "__pycache__", ".pytest_cache"]
                    for clean_dir in clean_dirs:
                        clean_path = project_path / clean_dir
                        if clean_path.exists():
                            shutil.rmtree(clean_path)
                    print(f"✅ Cleaned {project_path.name}")
                except Exception as e:
                    print(f"Error cleaning {project_path.name}: {e}")
        
        self.status_var.set("✅ Bulk clean complete")
    
    def _bulk_run_tests(self, selected_items):
        """Bulk run tests for selected projects"""
        self.status_var.set("🧪 Running tests...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Try different test commands
                    import subprocess
                    test_commands = [
                        ["npm", "test"],
                        ["python", "-m", "pytest"],
                        ["python", "-m", "unittest"],
                        ["mvn", "test"]
                    ]
                    
                    for cmd in test_commands:
                        try:
                            subprocess.run(cmd, cwd=project_path, check=True, capture_output=True)
                            print(f"✅ Tests passed for {project_path.name}")
                            break
                        except:
                            continue
                except Exception as e:
                    print(f"Error running tests for {project_path.name}: {e}")
        
        self.status_var.set("✅ Bulk test run complete")
    
    def _bulk_generate_reports(self, selected_items):
        """Bulk generate reports for selected projects"""
        self.status_var.set("📊 Generating reports...")
        self.root.update()
        
        report_data = []
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    project_info = self.analyze_project(project_path)
                    if project_info:
                        report_data.append(project_info)
                except Exception as e:
                    print(f"Error generating report for {project_path.name}: {e}")
        
        if report_data:
            self._show_report_dialog(report_data)
        
        self.status_var.set("✅ Bulk report generation complete")
    
    def _bulk_export_projects(self, selected_items):
        """Bulk export selected projects"""
        self.status_var.set("📤 Exporting projects...")
        self.root.update()
        
        # Create export directory
        export_dir = Path.home() / "Desktop" / "ProjectExports"
        export_dir.mkdir(exist_ok=True)
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import shutil
                    dest_path = export_dir / project_path.name
                    shutil.copytree(project_path, dest_path, ignore=shutil.ignore_patterns(
                        'node_modules', '__pycache__', '.git', 'dist', 'build'
                    ))
                    print(f"✅ Exported {project_path.name}")
                except Exception as e:
                    print(f"Error exporting {project_path.name}: {e}")
        
        self.status_var.set(f"✅ Projects exported to {export_dir}")
    
    # === PROJECT OPERATIONS ===
    
    def copy_project_info(self):
        """Copy project information to clipboard"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        info_text = ""
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    project_info = self.analyze_project(project_path)
                    if project_info:
                        info_text += f"Project: {project_info['name']}\n"
                        info_text += f"Type: {project_info['type']}\n"
                        info_text += f"Language: {project_info['language']}\n"
                        info_text += f"Health: {project_info['health']}%\n"
                        info_text += f"Size: {project_info['size']}\n"
                        info_text += f"Modified: {project_info['modified']}\n\n"
                except Exception as e:
                    print(f"Error copying project info: {e}")
        
        if info_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(info_text)
            self.status_var.set("📋 Project info copied to clipboard")
    
    def duplicate_project(self):
        """Duplicate selected project"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Get new name
                    new_name = tk.simpledialog.askstring("Duplicate Project", 
                                                       f"Enter new name for {project_path.name}:")
                    if not new_name:
                        continue
                    
                    # Create duplicate
                    import shutil
                    parent_dir = project_path.parent
                    new_path = parent_dir / new_name
                    shutil.copytree(project_path, new_path, ignore=shutil.ignore_patterns(
                        'node_modules', '__pycache__', '.git', 'dist', 'build'
                    ))
                    
                    print(f"✅ Duplicated {project_path.name} to {new_name}")
                    self.refresh_projects()
                except Exception as e:
                    print(f"Error duplicating project: {e}")
    
    def export_project(self):
        """Export project to archive"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import shutil
                    import os
                    
                    # Create archive
                    archive_path = Path.home() / "Desktop" / f"{project_path.name}.zip"
                    shutil.make_archive(str(archive_path.with_suffix('')), 'zip', project_path)
                    
                    print(f"✅ Exported {project_path.name} to {archive_path}")
                    self.status_var.set(f"📤 Project exported to {archive_path}")
                except Exception as e:
                    print(f"Error exporting project: {e}")
    
    # === HEALTH & ANALYSIS ===
    
    def deep_analysis(self):
        """Perform deep analysis on selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🔍 Performing deep analysis...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Perform comprehensive analysis
                    project_info = self.analyze_project(project_path)
                    if project_info:
                        # Additional deep analysis
                        self._perform_deep_analysis(project_path, project_info)
                except Exception as e:
                    print(f"Error in deep analysis: {e}")
        
        self.status_var.set("✅ Deep analysis complete")
    
    def _perform_deep_analysis(self, project_path, project_info):
        """Perform additional deep analysis"""
        try:
            # Analyze code complexity
            complexity_score = self._analyze_code_complexity(project_path)
            
            # Analyze dependencies
            dependency_health = self._analyze_dependencies(project_path)
            
            # Analyze documentation
            doc_coverage = self._analyze_documentation(project_path)
            
            print(f"Deep analysis for {project_path.name}:")
            print(f"  Complexity: {complexity_score}")
            print(f"  Dependencies: {dependency_health}")
            print(f"  Documentation: {doc_coverage}")
            
        except Exception as e:
            print(f"Error in deep analysis: {e}")
    
    def _analyze_code_complexity(self, project_path):
        """Analyze code complexity"""
        try:
            # Simple complexity analysis based on file structure
            total_files = len(list(project_path.rglob("*.py"))) + len(list(project_path.rglob("*.js")))
            if total_files < 10:
                return "Low"
            elif total_files < 50:
                return "Medium"
            else:
                return "High"
        except:
            return "Unknown"
    
    def _analyze_dependencies(self, project_path):
        """Analyze dependency health"""
        try:
            if (project_path / "package.json").exists():
                return "Node.js dependencies detected"
            elif (project_path / "requirements.txt").exists():
                return "Python dependencies detected"
            else:
                return "No dependency files found"
        except:
            return "Unknown"
    
    def _analyze_documentation(self, project_path):
        """Analyze documentation coverage"""
        try:
            doc_files = len(list(project_path.rglob("README*"))) + len(list(project_path.rglob("*.md")))
            if doc_files > 0:
                return f"{doc_files} documentation files found"
            else:
                return "No documentation found"
        except:
            return "Unknown"
    
    def security_scan(self):
        """Perform security scan on selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🔒 Performing security scan...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Basic security checks
                    security_issues = self._perform_security_scan(project_path)
                    if security_issues:
                        print(f"Security issues found in {project_path.name}:")
                        for issue in security_issues:
                            print(f"  - {issue}")
                    else:
                        print(f"✅ No security issues found in {project_path.name}")
                except Exception as e:
                    print(f"Error in security scan: {e}")
        
        self.status_var.set("✅ Security scan complete")
    
    def _perform_security_scan(self, project_path):
        """Perform basic security scan"""
        issues = []
        try:
            # Check for common security issues
            if (project_path / ".env").exists():
                issues.append("Environment file found - check for secrets")
            
            # Check for hardcoded secrets (basic check)
            for file_path in project_path.rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'password' in content.lower() and '=' in content:
                            issues.append(f"Potential hardcoded password in {file_path.name}")
                except:
                    continue
        except:
            pass
        
        return issues
    
    def performance_check(self):
        """Perform performance check on selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("📊 Performing performance check...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Basic performance analysis
                    size = self._get_directory_size(project_path)
                    file_count = len(list(project_path.rglob("*")))
                    
                    print(f"Performance check for {project_path.name}:")
                    print(f"  Size: {size}")
                    print(f"  Files: {file_count}")
                except Exception as e:
                    print(f"Error in performance check: {e}")
        
        self.status_var.set("✅ Performance check complete")
    
    def test_coverage(self):
        """Check test coverage for selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🧪 Checking test coverage...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Look for test files
                    test_files = list(project_path.rglob("*test*")) + list(project_path.rglob("*spec*"))
                    if test_files:
                        print(f"✅ Found {len(test_files)} test files in {project_path.name}")
                    else:
                        print(f"⚠️ No test files found in {project_path.name}")
                except Exception as e:
                    print(f"Error checking test coverage: {e}")
        
        self.status_var.set("✅ Test coverage check complete")
    
    def dependency_check(self):
        """Check dependencies for selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("📦 Checking dependencies...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Check for dependency files
                    dep_files = []
                    if (project_path / "package.json").exists():
                        dep_files.append("package.json")
                    if (project_path / "requirements.txt").exists():
                        dep_files.append("requirements.txt")
                    if (project_path / "Pipfile").exists():
                        dep_files.append("Pipfile")
                    if (project_path / "pom.xml").exists():
                        dep_files.append("pom.xml")
                    
                    if dep_files:
                        print(f"✅ Found dependency files in {project_path.name}: {', '.join(dep_files)}")
                    else:
                        print(f"⚠️ No dependency files found in {project_path.name}")
                except Exception as e:
                    print(f"Error checking dependencies: {e}")
        
        self.status_var.set("✅ Dependency check complete")
    
    # === AUTOMATION ===
    
    def auto_update_dependencies(self):
        """Auto-update dependencies for selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🔄 Auto-updating dependencies...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Update based on project type
                    if (project_path / "package.json").exists():
                        import subprocess
                        subprocess.run(["npm", "update"], cwd=project_path, check=True)
                        print(f"✅ Updated npm dependencies for {project_path.name}")
                    elif (project_path / "requirements.txt").exists():
                        import subprocess
                        subprocess.run(["pip", "install", "--upgrade", "-r", "requirements.txt"], 
                                     cwd=project_path, check=True)
                        print(f"✅ Updated pip dependencies for {project_path.name}")
                except Exception as e:
                    print(f"Error updating dependencies for {project_path.name}: {e}")
        
        self.status_var.set("✅ Auto-update complete")
    
    def auto_cleanup(self):
        """Auto-cleanup selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🧹 Auto-cleaning projects...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Clean common build artifacts
                    import shutil
                    clean_dirs = ["node_modules", "dist", "build", "__pycache__", ".pytest_cache", "target"]
                    for clean_dir in clean_dirs:
                        clean_path = project_path / clean_dir
                        if clean_path.exists():
                            shutil.rmtree(clean_path)
                    print(f"✅ Cleaned {project_path.name}")
                except Exception as e:
                    print(f"Error cleaning {project_path.name}: {e}")
        
        self.status_var.set("✅ Auto-cleanup complete")
    
    def auto_generate_docs(self):
        """Auto-generate documentation for selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("📝 Auto-generating documentation...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Generate basic README if it doesn't exist
                    readme_path = project_path / "README.md"
                    if not readme_path.exists():
                        self._generate_basic_readme(project_path)
                        print(f"✅ Generated README for {project_path.name}")
                    else:
                        print(f"ℹ️ README already exists for {project_path.name}")
                except Exception as e:
                    print(f"Error generating docs for {project_path.name}: {e}")
        
        self.status_var.set("✅ Auto-documentation complete")
    
    def _generate_basic_readme(self, project_path):
        """Generate basic README for project"""
        try:
            readme_content = f"""# {project_path.name}

## Description
Auto-generated project documentation.

## Installation
```bash
# Add installation instructions here
```

## Usage
```bash
# Add usage instructions here
```

## Development
```bash
# Add development instructions here
```

## License
Add license information here.
"""
            with open(project_path / "README.md", 'w', encoding='utf-8') as f:
                f.write(readme_content)
        except Exception as e:
            print(f"Error generating README: {e}")
    
    def run_tests(self):
        """Run tests for selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🧪 Running tests...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Try different test commands
                    import subprocess
                    test_commands = [
                        ["npm", "test"],
                        ["python", "-m", "pytest"],
                        ["python", "-m", "unittest", "discover"],
                        ["mvn", "test"]
                    ]
                    
                    for cmd in test_commands:
                        try:
                            result = subprocess.run(cmd, cwd=project_path, 
                                                  capture_output=True, text=True, timeout=30)
                            if result.returncode == 0:
                                print(f"✅ Tests passed for {project_path.name}")
                                break
                            else:
                                print(f"❌ Tests failed for {project_path.name}: {result.stderr}")
                        except subprocess.TimeoutExpired:
                            print(f"⏰ Tests timed out for {project_path.name}")
                        except:
                            continue
                except Exception as e:
                    print(f"Error running tests for {project_path.name}: {e}")
        
        self.status_var.set("✅ Test run complete")
    
    def build_project(self):
        """Build selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🏗️ Building projects...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Try different build commands
                    import subprocess
                    build_commands = [
                        ["npm", "run", "build"],
                        ["npm", "build"],
                        ["python", "setup.py", "build"],
                        ["mvn", "compile"],
                        ["gradle", "build"]
                    ]
                    
                    for cmd in build_commands:
                        try:
                            result = subprocess.run(cmd, cwd=project_path, 
                                                  capture_output=True, text=True, timeout=60)
                            if result.returncode == 0:
                                print(f"✅ Build successful for {project_path.name}")
                                break
                            else:
                                print(f"❌ Build failed for {project_path.name}: {result.stderr}")
                        except subprocess.TimeoutExpired:
                            print(f"⏰ Build timed out for {project_path.name}")
                        except:
                            continue
                except Exception as e:
                    print(f"Error building {project_path.name}: {e}")
        
        self.status_var.set("✅ Build complete")
    
    # === ADVANCED FEATURES ===
    
    def code_quality_analysis(self):
        """Perform code quality analysis"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🔍 Analyzing code quality...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Basic code quality analysis
                    quality_score = self._analyze_code_quality(project_path)
                    print(f"Code quality for {project_path.name}: {quality_score}")
                except Exception as e:
                    print(f"Error analyzing code quality: {e}")
        
        self.status_var.set("✅ Code quality analysis complete")
    
    def _analyze_code_quality(self, project_path):
        """Analyze code quality"""
        try:
            # Simple quality metrics
            total_files = len(list(project_path.rglob("*.py"))) + len(list(project_path.rglob("*.js")))
            if total_files == 0:
                return "No code files found"
            
            # Check for common quality indicators
            has_tests = len(list(project_path.rglob("*test*"))) > 0
            has_docs = (project_path / "README.md").exists()
            has_git = (project_path / ".git").exists()
            
            score = 0
            if has_tests:
                score += 30
            if has_docs:
                score += 30
            if has_git:
                score += 20
            
            if score >= 80:
                return "Excellent"
            elif score >= 60:
                return "Good"
            elif score >= 40:
                return "Fair"
            else:
                return "Poor"
        except:
            return "Unknown"
    
    def performance_profiling(self):
        """Perform performance profiling"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("📈 Performing performance profiling...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Basic performance profiling
                    size = self._get_directory_size(project_path)
                    file_count = len(list(project_path.rglob("*")))
                    
                    print(f"Performance profile for {project_path.name}:")
                    print(f"  Size: {size}")
                    print(f"  Files: {file_count}")
                    print(f"  Average file size: {size / max(file_count, 1)} bytes")
                except Exception as e:
                    print(f"Error in performance profiling: {e}")
        
        self.status_var.set("✅ Performance profiling complete")
    
    def security_audit(self):
        """Perform security audit"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🔒 Performing security audit...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Basic security audit
                    security_score = self._perform_security_audit(project_path)
                    print(f"Security audit for {project_path.name}: {security_score}")
                except Exception as e:
                    print(f"Error in security audit: {e}")
        
        self.status_var.set("✅ Security audit complete")
    
    def _perform_security_audit(self, project_path):
        """Perform security audit"""
        try:
            issues = []
            
            # Check for common security issues
            if (project_path / ".env").exists():
                issues.append("Environment file found")
            
            # Check for hardcoded secrets
            for file_path in project_path.rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'password' in content.lower() and '=' in content:
                            issues.append(f"Potential hardcoded password in {file_path.name}")
                except:
                    continue
            
            if not issues:
                return "No security issues found"
            else:
                return f"Found {len(issues)} potential issues"
        except:
            return "Audit failed"
    
    def bundle_analysis(self):
        """Perform bundle analysis"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("📊 Performing bundle analysis...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Basic bundle analysis
                    if (project_path / "package.json").exists():
                        bundle_size = self._analyze_bundle_size(project_path)
                        print(f"Bundle analysis for {project_path.name}: {bundle_size}")
                    else:
                        print(f"No package.json found for {project_path.name}")
                except Exception as e:
                    print(f"Error in bundle analysis: {e}")
        
        self.status_var.set("✅ Bundle analysis complete")
    
    def _analyze_bundle_size(self, project_path):
        """Analyze bundle size"""
        try:
            # Check for common bundle files
            bundle_files = ["dist", "build", "bundle"]
            total_size = 0
            
            for bundle_dir in bundle_files:
                bundle_path = project_path / bundle_dir
                if bundle_path.exists():
                    total_size += self._get_directory_size(bundle_path)
            
            if total_size > 0:
                return f"Bundle size: {self._format_size(total_size)}"
            else:
                return "No bundle files found"
        except:
            return "Analysis failed"
    
    def generate_api_docs(self):
        """Generate API documentation"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        self.status_var.set("🌐 Generating API documentation...")
        self.root.update()
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Generate basic API docs
                    self._generate_api_documentation(project_path)
                    print(f"✅ Generated API docs for {project_path.name}")
                except Exception as e:
                    print(f"Error generating API docs for {project_path.name}: {e}")
        
        self.status_var.set("✅ API documentation complete")
    
    def _generate_api_documentation(self, project_path):
        """Generate API documentation"""
        try:
            # Look for API files
            api_files = list(project_path.rglob("*api*")) + list(project_path.rglob("*route*"))
            if api_files:
                # Generate basic API documentation
                api_doc_path = project_path / "API.md"
                with open(api_doc_path, 'w', encoding='utf-8') as f:
                    f.write(f"# API Documentation for {project_path.name}\n\n")
                    f.write("## Endpoints\n\n")
                    f.write("Add your API endpoints here.\n\n")
                    f.write("## Authentication\n\n")
                    f.write("Add authentication details here.\n")
                print(f"Generated API documentation at {api_doc_path}")
            else:
                print(f"No API files found in {project_path.name}")
        except Exception as e:
            print(f"Error generating API documentation: {e}")
    
    # === PROJECT SETTINGS ===
    
    def project_settings(self):
        """Open project settings dialog"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Create settings dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("⚙️ Project Settings")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        # Settings interface
        ttk.Label(dialog, text="Project Settings", style='Title.TLabel').pack(pady=10)
        
        # Add settings controls here
        ttk.Label(dialog, text="Settings will be implemented here", 
                 style='TLabel').pack(pady=20)
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def add_project_tags(self):
        """Add tags to selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Get tags from user
        tags = tk.simpledialog.askstring("Add Tags", "Enter tags (comma-separated):")
        if not tags:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Add tags to project (implement tag storage)
                    print(f"Added tags '{tags}' to {project_path.name}")
                except Exception as e:
                    print(f"Error adding tags: {e}")
    
    def add_project_notes(self):
        """Add notes to selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Get notes from user
        notes = tk.simpledialog.askstring("Add Notes", "Enter notes:")
        if not notes:
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    # Add notes to project (implement note storage)
                    print(f"Added notes to {project_path.name}")
                except Exception as e:
                    print(f"Error adding notes: {e}")
    
    # === DANGER ZONE ===
    
    def delete_project(self):
        """Delete selected projects (with confirmation)"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Confirmation dialog
        if not tk.messagebox.askyesno("Delete Projects", 
                                     f"Are you sure you want to delete {len(selected_items)} project(s)?\n\nThis action cannot be undone!"):
            return
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import shutil
                    shutil.rmtree(project_path)
                    print(f"✅ Deleted {project_path.name}")
                except Exception as e:
                    print(f"Error deleting {project_path.name}: {e}")
        
        self.refresh_projects()
        self.status_var.set("✅ Projects deleted")
    
    def archive_project(self):
        """Archive selected projects"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Create archive directory
        archive_dir = Path.home() / "Desktop" / "ArchivedProjects"
        archive_dir.mkdir(exist_ok=True)
        
        for item in selected_items:
            project_path = self._get_project_path_from_item(item)
            if project_path and project_path.exists():
                try:
                    import shutil
                    archive_path = archive_dir / f"{project_path.name}_archived"
                    shutil.move(str(project_path), str(archive_path))
                    print(f"✅ Archived {project_path.name}")
                except Exception as e:
                    print(f"Error archiving {project_path.name}: {e}")
        
        self.refresh_projects()
        self.status_var.set("✅ Projects archived")
    
    # === UTILITY METHODS ===
    
    def _get_directory_size(self, path):
        """Get directory size in bytes"""
        try:
            total_size = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except:
            return 0
    
    def _format_size(self, size_bytes):
        """Format size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _show_report_dialog(self, report_data):
        """Show project report dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("📊 Project Report")
        dialog.geometry("800x600")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Report content
        report_text = tk.Text(dialog, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                            font=('Consolas', 10), wrap=tk.WORD)
        report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generate report content
        for project in report_data:
            report_text.insert(tk.END, f"Project: {project['name']}\n")
            report_text.insert(tk.END, f"Type: {project['type']}\n")
            report_text.insert(tk.END, f"Language: {project['language']}\n")
            report_text.insert(tk.END, f"Health: {project['health']}%\n")
            report_text.insert(tk.END, f"Size: {project['size']}\n")
            report_text.insert(tk.END, f"Modified: {project['modified']}\n")
            report_text.insert(tk.END, "-" * 50 + "\n")
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def _show_git_status_dialog(self, project_name, status_output):
        """Show Git status dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"📋 Git Status - {project_name}")
        dialog.geometry("600x400")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Status content
        status_text = tk.Text(dialog, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                             font=('Consolas', 10), wrap=tk.WORD)
        status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        status_text.insert(tk.END, status_output)
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def _show_git_log_dialog(self, project_name, log_output):
        """Show Git log dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"📊 Git Log - {project_name}")
        dialog.geometry("600x400")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Log content
        log_text = tk.Text(dialog, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                          font=('Consolas', 10), wrap=tk.WORD)
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        log_text.insert(tk.END, log_output)
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def _show_git_stats_dialog(self, project_name, stats_output):
        """Show Git statistics dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"📈 Git Statistics - {project_name}")
        dialog.geometry("600x400")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Stats content
        stats_text = tk.Text(dialog, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                            font=('Consolas', 10), wrap=tk.WORD)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        stats_text.insert(tk.END, stats_output)
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
        
        # Multi-language specific information
        multi_lang_info = ""
        if is_multi_language:
            integration_good = self._check_cross_language_integration(project_path, languages)
            primary_lang = self._determine_primary_language(languages, project_path)
            
            # Categorize languages
            web_langs = [lang for lang in languages if lang in ['javascript', 'typescript', 'html', 'css', 'vue', 'react', 'angular', 'svelte']]
            backend_langs = [lang for lang in languages if lang in ['python', 'java', 'csharp', 'go', 'rust', 'php', 'ruby', 'nodejs']]
            mobile_langs = [lang for lang in languages if lang in ['swift', 'dart', 'kotlin', 'react-native', 'flutter']]
            system_langs = [lang for lang in languages if lang in ['c', 'cpp', 'assembly', 'rust']]
            script_langs = [lang for lang in languages if lang in ['bash', 'powershell', 'lua', 'perl', 'python']]
            doc_langs = [lang for lang in languages if lang in ['markdown', 'text', 'log', 'json', 'yaml', 'xml', 'ini', 'config']]
            
            multi_lang_info = f"""
Multi-Language Project ({len(languages)} languages):
• All Languages: {', '.join(languages)}
• Primary Language: {primary_lang}
• Web Technologies: {', '.join(web_langs) if web_langs else 'None'}
• Backend Languages: {', '.join(backend_langs) if backend_langs else 'None'}
• Mobile Technologies: {', '.join(mobile_langs) if mobile_langs else 'None'}
• System Languages: {', '.join(system_langs) if system_langs else 'None'}
• Scripting Languages: {', '.join(script_langs) if script_langs else 'None'}
• Documentation/Config: {', '.join(doc_langs) if doc_langs else 'None'}

Integration Analysis:
• Cross-Language Integration: {'✅ Excellent' if integration_good else '❌ Needs Improvement'}
• Build Coordination: {'✅' if any((project_path / build_file).exists() for build_file in ['Makefile', 'build.sh', 'build.py', 'build.js']) else '❌'} Build scripts
• Containerization: {'✅' if any((project_path / docker_file).exists() for docker_file in ['Dockerfile', 'docker-compose.yml']) else '❌'} Docker setup
• CI/CD Pipeline: {'✅' if any((project_path / ci_dir).exists() for ci_dir in ['.github', '.gitlab-ci', '.circleci']) else '❌'} Multi-language CI/CD
"""
        
        # JavaScript Framework information
        js_framework_info = ""
        if project_info.get('frameworks'):
            frameworks = project_info['frameworks']
            js_framework_info = f"""
JavaScript Frameworks Detected:
• Frameworks: {', '.join(frameworks)}
• Primary Framework: {frameworks[0] if frameworks else 'None'}
• Framework Count: {len(frameworks)}
"""
        
        # Hierarchical information
        hierarchical_info = ""
        if project_info.get('parent'):
            hierarchical_info = f"""
Hierarchical Structure:
• Parent Project: {Path(project_info['parent']).name}
• Project Depth: Level {project_info.get('depth', 0)}
• Relative Path: {project_info.get('relative_path', 'N/A')}
"""
        
        # Check for sub-projects
        sub_projects = [p for p in self.projects if p.get('parent') == project_info.get('path')]
        if sub_projects:
            sub_project_names = [p['name'] for p in sub_projects]
            hierarchical_info += f"• Sub-Projects: {', '.join(sub_project_names)}\n"
        
        details = f"""Project: {project_info['name']}
Path: {project_info['path']}
Type: {project_info['type']}
Language: {project_info['language']}
Framework: {project_info['framework']}
Status: {project_info['status']}
Health Score: {health_score}% {health_status}
Size: {project_info['size']}
Last Modified: {project_info['modified']}
{hierarchical_info}{js_framework_info}{multi_lang_info}
Health Analysis:
• Documentation: {'✅' if (Path(project_info['path']) / 'README.md').exists() else '❌'} README.md
• Version Control: {'✅' if (Path(project_info['path']) / '.git').exists() else '❌'} Git repository
• Testing: {'✅' if any((Path(project_info['path']) / test_dir).exists() for test_dir in ['tests', 'test', '__tests__', 'spec']) else '❌'} Test structure
• Security: {'✅' if any((Path(project_info['path']) / sec_file).exists() for sec_file in ['.env.example', 'security.md', 'SECURITY.md']) else '❌'} Security files
• Dependencies: {'✅' if self._has_dependency_files(Path(project_info['path']), project_info['language']) else '❌'} Dependency management
• CI/CD: {'✅' if any((Path(project_info['path']) / ci_dir).exists() for ci_dir in ['.github', '.gitlab-ci', '.circleci']) else '❌'} Continuous Integration
• Configuration: {'✅' if any((Path(project_info['path']) / config_file).exists() for config_file in ['.editorconfig', '.gitattributes', 'docker-compose.yml']) else '❌'} Configuration files

Recommendations:
{self._get_health_recommendations(Path(project_info['path']), health_score)}
"""
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
    
    def create_new_project(self):
        """Create a new project"""
        name = self.project_name_var.get()
        language = self.language_var.get()
        framework = self.framework_var.get()
        description = self.description_var.get()
        
        if not name:
            messagebox.showerror("Error", "Please enter a project name")
            return
        
        try:
            # Create project directory
            project_path = Path(self.config["projects_dir"]) / name
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize git
            subprocess.run(['git', 'init'], cwd=project_path, check=True)
            
            # Create basic files
            self.create_basic_files(project_path, name, language, description)
            
            messagebox.showinfo("Success", f"Project '{name}' created successfully!")
            
            # Refresh projects
            self.load_projects()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create project: {e}")
    
    def create_basic_files(self, project_path: Path, name: str, language: str, description: str):
        """Create basic project files"""
        # Create README.md
        readme_content = f"""# {name}

## Description
{description or f"{name} project"}

## Setup
```bash
# Install dependencies
# Add setup instructions here

# Run the project
# Add run instructions here
```

## Development
```bash
# Development commands
# Add development instructions here
```
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
        elif language == 'bash':
            self.create_bash_project(project_path, name)
    
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
    
    def _check_cross_language_integration(self, project_path: Path, languages: list) -> bool:
        """Check for good cross-language integration in multi-language projects"""
        integration_score = 0
        
        # Check for build scripts that handle multiple languages
        build_files = ['Makefile', 'build.sh', 'build.py', 'build.js', 'build.ps1']
        has_build_script = any((project_path / build_file).exists() for build_file in build_files)
        if has_build_script:
            integration_score += 1
        
        # Check for Docker/containerization (good for multi-language)
        docker_files = ['Dockerfile', 'docker-compose.yml', '.dockerignore']
        has_docker = any((project_path / docker_file).exists() for docker_file in docker_files)
        if has_docker:
            integration_score += 1
        
        # Check for CI/CD configuration
        ci_files = ['.github/workflows', '.gitlab-ci.yml', 'azure-pipelines.yml', 'Jenkinsfile']
        has_ci = any((project_path / ci_file).exists() for ci_file in ci_files)
        if has_ci:
            integration_score += 1
        
        # Check for documentation explaining multi-language setup
        readme_content = ""
        if (project_path / 'README.md').exists():
            try:
                with open(project_path / 'README.md', 'r', encoding='utf-8', errors='ignore') as f:
                    readme_content = f.read().lower()
            except:
                pass
        
        # Look for multi-language documentation keywords
        multi_lang_keywords = ['multi-language', 'polyglot', 'mixed', 'integration', 'cross-language']
        has_multi_lang_docs = any(keyword in readme_content for keyword in multi_lang_keywords)
        if has_multi_lang_docs:
            integration_score += 1
        
        # Check for language-specific directories (good organization)
        lang_dirs = ['src', 'lib', 'app', 'frontend', 'backend', 'api', 'scripts']
        has_organized_dirs = any((project_path / lang_dir).exists() for lang_dir in lang_dirs)
        if has_organized_dirs:
            integration_score += 1
        
        # Check for configuration files that might coordinate languages
        config_files = ['config.json', 'config.yaml', 'config.yml', 'settings.json']
        has_config = any((project_path / config_file).exists() for config_file in config_files)
        if has_config:
            integration_score += 1
        
        # Good integration if score >= 3
        return integration_score >= 3

    def create_bash_project(self, project_path: Path, name: str):
        """Create Bash project structure"""
        # Create main shell script
        main_sh = f"""#!/usr/bin/env bash
# {name} - Main script
# Description: {name} automation script
# Author: Your Name
# Version: 1.0.0

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/{name}.log"

# Logging function
log() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}}

# Error handling
error_exit() {{
    log "ERROR: $1"
    exit 1
}}

# Main function
main() {{
    log "Starting {name} script"
    
    # Add your script logic here
    echo "Hello from {name}!"
    
    log "Script completed successfully"
}}

# Run main function
main "$@"
"""
        with open(project_path / f"{name}.sh", 'w') as f:
            f.write(main_sh)
        
        # Make it executable
        os.chmod(project_path / f"{name}.sh", 0o755)
        
        # Create logs directory
        logs_dir = project_path / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create install script
        install_sh = f"""#!/usr/bin/env bash
# Install script for {name}
# This script installs dependencies and sets up the environment

set -euo pipefail

echo "Installing {name} dependencies..."

# Add installation commands here
# Example:
# sudo apt-get update
# sudo apt-get install -y required-package

echo "Installation completed!"
"""
        with open(project_path / 'install.sh', 'w') as f:
            f.write(install_sh)
        os.chmod(project_path / 'install.sh', 0o755)
        
        # Create test script
        test_sh = f"""#!/usr/bin/env bash
# Test script for {name}
# This script runs tests for the project

set -euo pipefail

echo "Running tests for {name}..."

# Add test commands here
# Example:
# ./{name}.sh --test

echo "All tests passed!"
"""
        with open(project_path / 'test.sh', 'w') as f:
            f.write(test_sh)
        os.chmod(project_path / 'test.sh', 0o755)
        
        # Create configuration file
        config_sh = f"""#!/usr/bin/env bash
# Configuration file for {name}
# Source this file in your scripts: source config.sh

# Project configuration
PROJECT_NAME="{name}"
PROJECT_VERSION="1.0.0"
PROJECT_AUTHOR="Your Name"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
TEMP_DIR="$SCRIPT_DIR/temp"

# Create directories if they don't exist
mkdir -p "$LOG_DIR" "$TEMP_DIR"

# Export variables
export PROJECT_NAME PROJECT_VERSION PROJECT_AUTHOR
export SCRIPT_DIR LOG_DIR TEMP_DIR
"""
        with open(project_path / 'config.sh', 'w') as f:
            f.write(config_sh)
        
        # Create requirements file
        requirements_content = f"""# {name} Dependencies
# Add system dependencies and packages here

# System packages (for Ubuntu/Debian)
# sudo apt-get install -y package1 package2

# System packages (for CentOS/RHEL)
# sudo yum install -y package1 package2

# Python packages (if using Python in bash scripts)
# pip install package1 package2

# Node.js packages (if using Node.js in bash scripts)
# npm install package1 package2
"""
        with open(project_path / 'requirements.txt', 'w') as f:
            f.write(requirements_content)
    
    def load_templates(self):
        """Load project templates"""
        templates = [
            "Python Flask Web App",
            "Python Django Project",
            "Node.js Express API",
            "React Frontend",
            "Vue.js Application",
            "Rust CLI Tool",
            "Go Web Service",
            "Java Spring Boot",
            "C++ CMake Project",
            "Bash Automation Script",
            "Bash Deployment Script",
            "Bash System Administration"
        ]
        
        for template in templates:
            self.template_listbox.insert(tk.END, template)
    
    def backup_selected_project(self):
        """Backup selected project"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project to backup")
            return
        
        item = self.tree.item(selection[0])
        project_name = item['text']
        
        try:
            # Create backup directory
            backup_dir = Path(self.config["backup_dir"]) / f"{project_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy project
            project_path = Path(self.config["projects_dir"]) / project_name
            shutil.copytree(project_path, backup_dir / project_name)
            
            messagebox.showinfo("Success", f"Project '{project_name}' backed up to {backup_dir}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup project: {e}")
    
    def open_project_folder(self):
        """Open project folder in explorer"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project")
            return
        
        item = self.tree.item(selection[0])
        project_name = item['text']
        
        project_path = Path(self.config["projects_dir"]) / project_name
        if project_path.exists():
            if os.name == 'nt':  # Windows
                os.startfile(project_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', project_path])
    
    def filter_projects(self, event):
        """Filter projects by health score"""
        # This would implement filtering logic
        pass
    
    def start_monitoring(self):
        """Start project monitoring"""
        if self.monitoring_running:
            return
        
        self.monitoring_running = True
        self.monitoring_status_var.set("Running")
        self.monitoring_thread = threading.Thread(target=self.monitor_projects)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop project monitoring"""
        self.monitoring_running = False
        self.monitoring_status_var.set("Stopped")
    
    def monitor_projects(self):
        """Monitor project health"""
        while self.monitoring_running:
            try:
                # Check project health
                issues = []
                for project in self.projects:
                    if project['health'] < self.health_threshold_var.get():
                        issues.append(f"{project['name']}: Health score {project['health']}%")
                
                # Update monitoring text
                if issues:
                    self.monitoring_text.delete(1.0, tk.END)
                    self.monitoring_text.insert(1.0, f"Monitoring Results - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    for issue in issues:
                        self.monitoring_text.insert(tk.END, f"⚠️ {issue}\n")
                else:
                    self.monitoring_text.delete(1.0, tk.END)
                    self.monitoring_text.insert(1.0, f"Monitoring Results - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    self.monitoring_text.insert(tk.END, "✅ All projects are healthy!\n")
                
                # Wait for next check
                time.sleep(self.config["monitoring"]["check_interval"])
                
            except Exception as e:
                print(f"Error in monitoring: {e}")
                break
    
    def browse_projects_dir(self):
        """Browse for projects directory"""
        directory = filedialog.askdirectory(title="Select Projects Directory")
        if directory:
            self.projects_dir_var.set(directory)
            # Optionally auto-refresh after directory selection
            # self.load_projects()
    
    def browse_backup_dir(self):
        """Browse for backup directory"""
        directory = filedialog.askdirectory(title="Select Backup Directory")
        if directory:
            self.backup_dir_var.set(directory)
    
    def save_settings(self):
        """Save settings"""
        try:
            old_projects_dir = self.config["projects_dir"]
            self.config["projects_dir"] = self.projects_dir_var.get()
            self.config["backup_dir"] = self.backup_dir_var.get()
            self.config["monitoring"]["enabled"] = self.monitoring_enabled_var.get()
            self.config["monitoring"]["check_interval"] = self.check_interval_var.get()
            
            self.save_config()
            
            # If projects directory changed, reload projects
            if old_projects_dir != self.config["projects_dir"]:
                self.load_projects()
                self.status_var.set(f"Projects directory changed to: {self.config['projects_dir']}")
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

def main():
    root = tk.Tk()
    app = ProjectManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
