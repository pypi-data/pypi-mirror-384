#!/usr/bin/env python3
"""
Generic project detection - works with ANY IDE/project type
Not RStudio-specific - detects R, Python, Node, Jupyter, etc.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import glob


class ProjectDetector:
    """Detects project type and provides context"""
    
    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = Path(working_dir or os.getcwd())
    
    def detect_project(self) -> Optional[Dict[str, Any]]:
        """
        Detect what kind of project user is working in
        Returns project info or None if not in a project
        """
        project_info = {
            "type": None,
            "name": None,
            "recent_files": [],
            "description": None
        }
        
        # Check for R project (.Rproj file OR 2+ .R files)
        rproj_files = list(self.working_dir.glob("*.Rproj"))
        r_files = list(self.working_dir.glob("*.R")) + list(self.working_dir.glob("*.Rmd"))
        
        if rproj_files:
            project_info["type"] = "R"
            project_info["name"] = rproj_files[0].stem
            project_info["recent_files"] = self._get_recent_files([".R", ".Rmd", ".qmd"])
            project_info["description"] = f"R/RStudio project: {project_info['name']}"
            return project_info
        elif len(r_files) >= 2:
            # R project without .Rproj file
            project_info["type"] = "R"
            project_info["name"] = self.working_dir.name
            project_info["recent_files"] = self._get_recent_files([".R", ".Rmd", ".qmd"])
            project_info["description"] = f"R project: {project_info['name']}"
            return project_info
        
        # Check for Python project
        if (self.working_dir / "pyproject.toml").exists() or \
           (self.working_dir / "setup.py").exists() or \
           (self.working_dir / "requirements.txt").exists():
            project_info["type"] = "Python"
            project_info["name"] = self.working_dir.name
            project_info["recent_files"] = self._get_recent_files([".py", ".ipynb"])
            project_info["description"] = f"Python project: {project_info['name']}"
            return project_info
        
        # Check for Node.js project
        if (self.working_dir / "package.json").exists():
            project_info["type"] = "Node"
            project_info["name"] = self.working_dir.name
            project_info["recent_files"] = self._get_recent_files([".js", ".ts", ".jsx", ".tsx"])
            project_info["description"] = f"Node.js project: {project_info['name']}"
            return project_info
        
        # Check for Jupyter/Data Science directory
        ipynb_files = list(self.working_dir.glob("*.ipynb"))
        if len(ipynb_files) >= 2:  # 2+ notebooks = likely data science project
            project_info["type"] = "Jupyter"
            project_info["name"] = self.working_dir.name
            project_info["recent_files"] = self._get_recent_files([".ipynb", ".py", ".csv"])
            project_info["description"] = f"Jupyter/Data Science project: {project_info['name']}"
            return project_info
        
        # Check for Git repository
        if (self.working_dir / ".git").exists():
            project_info["type"] = "Git"
            project_info["name"] = self.working_dir.name
            # Get recent files of any code type
            project_info["recent_files"] = self._get_recent_files([".py", ".js", ".R", ".java", ".cpp", ".rs"])
            project_info["description"] = f"Git repository: {project_info['name']}"
            return project_info
        
        # Not in a recognized project
        return None
    
    def _get_recent_files(self, extensions: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently modified files with given extensions"""
        files = []
        
        for ext in extensions:
            for filepath in self.working_dir.glob(f"**/*{ext}"):
                if filepath.is_file() and not any(part.startswith('.') for part in filepath.parts):
                    try:
                        mtime = filepath.stat().st_mtime
                        files.append({
                            "name": filepath.name,
                            "path": str(filepath),
                            "relative_path": str(filepath.relative_to(self.working_dir)),
                            "modified": mtime,
                            "extension": ext
                        })
                    except:
                        pass
        
        # Sort by modification time, newest first
        files.sort(key=lambda f: f["modified"], reverse=True)
        return files[:limit]
    
    def format_project_banner(self, project_info: Dict[str, Any]) -> str:
        """Format project info as a nice banner"""
        if not project_info or not project_info["type"]:
            return ""
        
        icon_map = {
            "R": "📊",
            "Python": "🐍",
            "Node": "📦",
            "Jupyter": "📓",
            "Git": "📂"
        }
        
        icon = icon_map.get(project_info["type"], "📁")
        
        banner = f"\n{icon} {project_info['description']}\n"
        
        if project_info["recent_files"]:
            banner += "📄 Recent files:\n"
            for f in project_info["recent_files"][:3]:
                banner += f"   • {f['relative_path']}\n"
        
        return banner
    
    def get_project_context_for_llm(self, project_info: Dict[str, Any]) -> str:
        """Get project context to add to LLM prompts"""
        if not project_info or not project_info["type"]:
            return ""
        
        context = f"User is working in a {project_info['type']} project: {project_info['name']}\n"
        
        if project_info["recent_files"]:
            context += "Recent files:\n"
            for f in project_info["recent_files"][:5]:
                context += f"- {f['relative_path']}\n"
        
        return context

