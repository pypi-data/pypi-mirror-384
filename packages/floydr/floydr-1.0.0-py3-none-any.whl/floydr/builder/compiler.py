import subprocess
import re
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Dict


@dataclass
class WidgetBuildResult:
    """Result of building a widget."""
    name: str
    hash: str
    html: str


class WidgetBuilder:
    """
    Widget builder for Flick framework.
    
    Discovers widgets, builds them with Vite, and parses the results.
    """
    
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root
        self.assets_dir = self.project_root / "assets"
        self.widgets_dir = self.project_root / "widgets"
        self.framework_dir = Path(__file__).parent
    
    def build_all(self) -> Dict[str, WidgetBuildResult]:
        """
        Build all widgets in the project.
        
        Returns:
            Dictionary mapping widget names to build results.
        """
        # 1. Auto-discover widgets
        self._discover_widgets()
        
        # 2. Copy framework's build script to project (if not exists)
        self._ensure_build_script()
        
        # 3. Run build
        subprocess.run(["npx", "tsx", "build-all.mts"], cwd=self.project_root, check=True)
        
        # 4. Parse results
        return self._parse_build_results()
    
    def _ensure_build_script(self):
        """
        Ensure build script exists.
        
        The build script is provided by flick-react NPM package.
        Users should have 'flick-react' installed as a devDependency.
        """
        project_build_script = self.project_root / "build-all.mts"
        
        # Check if flick-react is installed in node_modules
        flick_react_build_script = self.project_root / "node_modules" / "flick-react" / "build-all.mts"
        
        if not project_build_script.exists():
            if flick_react_build_script.exists():
                # Copy from node_modules
                shutil.copy(flick_react_build_script, project_build_script)
                print(f"✓ Copied build script from flick-react package")
            else:
                raise FileNotFoundError(
                    "build-all.mts not found. Please install flick-react: npm install --save-dev flick-react"
                )
    
    def _discover_widgets(self):
        """
        Discover widgets in the widgets directory.
        
        Mounting logic is automatically injected during build,
        so each widget only needs an index.jsx file!
        """
        widget_count = 0
        for widget_dir in self.widgets_dir.iterdir():
            if not widget_dir.is_dir() or widget_dir.name.startswith('.'):
                continue
            
            widget_name = widget_dir.name
            index_file = widget_dir / "index.jsx"
            
            if index_file.exists():
                widget_count += 1
                print(f"✓ Found widget: {widget_name}")
        
        if widget_count > 0:
            print(f"\n📦 Ready to build {widget_count} widget(s)")
    
    def _parse_build_results(self) -> Dict[str, WidgetBuildResult]:
        """Parse built widget HTML files."""
        results = {}
        for html_file in self.assets_dir.glob("*-*.html"):
            match = re.match(r"(.+)-([0-9a-f]{4})\.html$", html_file.name)
            if match:
                name, hash_val = match.groups()
                results[name] = WidgetBuildResult(
                    name=name,
                    hash=hash_val,
                    html=html_file.read_text()
                )
        return results

