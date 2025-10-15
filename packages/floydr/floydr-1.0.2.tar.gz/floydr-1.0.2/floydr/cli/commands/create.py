"""Create widget command."""

from pathlib import Path
from rich.console import Console

console = Console()

TOOL_TEMPLATE = '''from floydr import BaseWidget, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any


class {ClassName}Input(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class {ClassName}Tool(BaseWidget):
    identifier = "{identifier}"
    title = "{title}"
    input_schema = {ClassName}Input
    invoking = "Loading widget..."
    invoked = "Widget ready!"
    
    widget_csp = {{
        "connect_domains": [],
        "resource_domains": []
    }}
    
    async def execute(self, input_data: {ClassName}Input) -> Dict[str, Any]:
        return {{
            "message": "Welcome to Floydr"
        }}
'''

WIDGET_TEMPLATE = '''import React from 'react';
import {{ useWidgetProps }} from 'floydr';

export default function {ClassName}() {{
  const props = useWidgetProps();
  
  return (
    <div style={{{{
      background: '#000',
      color: '#fff',
      padding: '40px',
      textAlign: 'center',
      borderRadius: '8px',
      fontFamily: 'monospace'
    }}}}>
      <h1>{{props.message || 'Welcome to Floydr'}}</h1>
    </div>
  );
}}
'''


def create_widget(name: str):
    """Create a new widget with tool and component files."""
    
    # Convert name to proper formats
    identifier = name.lower().replace('-', '_').replace(' ', '_')
    class_name = ''.join(word.capitalize() for word in identifier.split('_'))
    title = ' '.join(word.capitalize() for word in identifier.split('_'))
    
    # Paths
    tool_dir = Path("server/tools")
    widget_dir = Path("widgets") / identifier
    
    tool_file = tool_dir / f"{identifier}_tool.py"
    widget_file = widget_dir / "index.jsx"
    
    # Check if already exists
    if tool_file.exists():
        console.print(f"[yellow]⚠ Tool already exists: {tool_file}[/yellow]")
        return False
    
    if widget_file.exists():
        console.print(f"[yellow]⚠ Widget already exists: {widget_file}[/yellow]")
        return False
    
    # Create directories
    tool_dir.mkdir(parents=True, exist_ok=True)
    widget_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate files
    tool_content = TOOL_TEMPLATE.format(
        ClassName=class_name,
        identifier=identifier,
        title=title
    )
    
    widget_content = WIDGET_TEMPLATE.format(
        ClassName=class_name
    )
    
    # Write files
    tool_file.write_text(tool_content)
    widget_file.write_text(widget_content)
    
    console.print(f"\n[green]✅ Widget created successfully![/green]")
    console.print(f"\n[cyan]Created files:[/cyan]")
    console.print(f"  📄 {tool_file}")
    console.print(f"  📄 {widget_file}")
    console.print(f"\n[yellow]Next steps:[/yellow]")
    console.print(f"  1. npm run build")
    console.print(f"  2. python server/main.py")
    console.print(f"\n[green]Your widget will be automatically discovered by Floydr![/green]\n")
    
    return True

