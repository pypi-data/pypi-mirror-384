# Flick

A zero-boilerplate framework for building interactive ChatGPT widgets.

## Features

- 🚀 Zero Configuration - Just create your widget and tool, everything else is automated
- 🔄 Auto-Discovery - Tools are automatically detected and registered  
- 📦 Auto-Build - Mounting logic injected at build time
- ⚡ Hot Reload - Changes detected and rebuilt automatically
- 🎨 React + Vite - Modern frontend development experience

## Installation

```bash
pip install flick
```

## Quick Start

```python
from flick import BaseWidget
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any

class MyWidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

class MyWidgetTool(BaseWidget):
    identifier = "my_widget"
    title = "My Widget"
    input_schema = MyWidgetInput
    
    async def execute(self, input_data: MyWidgetInput) -> Dict[str, Any]:
        return {"message": "Hello from Flick!"}
```

Create your React component in `widgets/my_widget/index.jsx`:

```jsx
import React from 'react';
import { useWidgetProps } from 'flick-react';

export default function MyWidget() {
  const { message } = useWidgetProps();
  return <h1>{message}</h1>;
}
```

That's it! No boilerplate files needed.

## Documentation

Visit [flick.dev/docs](https://flick.dev/docs) for full documentation.

## License

MIT

