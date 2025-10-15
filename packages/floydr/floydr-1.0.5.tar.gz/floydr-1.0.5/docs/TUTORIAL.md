# Floydr Widget Tutorial

Learn to build ChatGPT widgets step by step.

## Tutorial 1: Hello World

### Goal
Create a simple greeting widget that displays a personalized message.

### Python Tool

Create `server/tools/greeting_tool.py`:

```python
from floydr import BaseWidget, Field, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any

class GreetingInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(default="World", description="Name to greet")

class GreetingTool(BaseWidget):
    identifier = "greeting"
    title = "Greeting Widget"
    input_schema = GreetingInput
    invoking = "Preparing greeting..."
    invoked = "Greeting ready!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: GreetingInput) -> Dict[str, Any]:
        return {
            "name": input_data.name,
            "message": f"Hello, {input_data.name}!",
            "emoji": "👋"
        }
```

### React Component

Create `widgets/greeting/index.jsx`:

```jsx
import React from 'react';
import { useWidgetProps } from 'chatjs-hooks';

export default function Greeting() {
  const props = useWidgetProps();
  
  return (
    <div style={{
      padding: '40px',
      textAlign: 'center',
      background: '#4A90E2',
      color: 'white',
      borderRadius: '12px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ fontSize: '48px', margin: 0 }}>
        {props.emoji} {props.message}
      </h1>
      <p style={{ fontSize: '18px', marginTop: '10px', opacity: 0.9 }}>
        Welcome, {props.name}!
      </p>
    </div>
  );
}
```

### Build and Test

```bash
npm run build
python server/main.py
```

---

## Tutorial 2: Weather Widget with API

### Goal
Fetch weather data from an external API and display it.

### Python Tool

```python
from floydr import BaseWidget, Field, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any
import httpx

class WeatherInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    city: str = Field(..., description="City name")

class WeatherTool(BaseWidget):
    identifier = "weather"
    title = "Weather Widget"
    input_schema = WeatherInput
    invoking = "Fetching weather..."
    invoked = "Weather ready!"
    
    widget_csp = {
        "connect_domains": ["https://api.openweathermap.org"],
        "resource_domains": []
    }
    
    async def execute(self, input_data: WeatherInput) -> Dict[str, Any]:
        # Example API call (replace with real API key)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": input_data.city,
                        "appid": "YOUR_API_KEY",
                        "units": "metric"
                    }
                )
                data = response.json()
                
                return {
                    "city": input_data.city,
                    "temperature": data["main"]["temp"],
                    "condition": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"]
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "city": input_data.city
                }
```

### React Component

```jsx
import React from 'react';
import { useWidgetProps } from 'chatjs-hooks';

export default function Weather() {
  const props = useWidgetProps();
  
  if (props.error) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        Error: {props.error}
      </div>
    );
  }
  
  return (
    <div style={{
      padding: '30px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      borderRadius: '16px',
      fontFamily: 'system-ui'
    }}>
      <h1 style={{ margin: '0 0 20px 0' }}>
        🌤️ Weather in {props.city}
      </h1>
      <div style={{ fontSize: '64px', margin: '20px 0' }}>
        {props.temperature}°C
      </div>
      <p style={{ fontSize: '24px', margin: '10px 0' }}>
        {props.condition}
      </p>
      <p style={{ fontSize: '16px', opacity: 0.8 }}>
        {props.description}
      </p>
      <p style={{ fontSize: '14px', marginTop: '20px' }}>
        💧 Humidity: {props.humidity}%
      </p>
    </div>
  );
}
```

---

## Tutorial 3: Interactive Counter with State

### Goal
Create a counter widget that persists state across interactions.

### Python Tool

```python
from floydr import BaseWidget, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any

class CounterInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

class CounterTool(BaseWidget):
    identifier = "counter"
    title = "Counter Widget"
    input_schema = CounterInput
    invoking = "Loading counter..."
    invoked = "Counter ready!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: CounterInput) -> Dict[str, Any]:
        return {
            "initialCount": 0
        }
```

### React Component

```jsx
import React from 'react';
import { useWidgetProps, useWidgetState } from 'chatjs-hooks';

export default function Counter() {
  const props = useWidgetProps();
  const [state, setState] = useWidgetState({ 
    count: props.initialCount || 0 
  });
  
  const increment = () => setState({ count: state.count + 1 });
  const decrement = () => setState({ count: state.count - 1 });
  const reset = () => setState({ count: 0 });
  
  return (
    <div style={{
      padding: '40px',
      textAlign: 'center',
      background: '#2c3e50',
      color: 'white',
      borderRadius: '12px'
    }}>
      <h1 style={{ margin: '0 0 30px 0' }}>Counter</h1>
      
      <div style={{
        fontSize: '72px',
        fontWeight: 'bold',
        margin: '20px 0',
        color: '#3498db'
      }}>
        {state.count}
      </div>
      
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
        <button 
          onClick={decrement}
          style={buttonStyle}
        >
          - Decrease
        </button>
        
        <button 
          onClick={reset}
          style={{ ...buttonStyle, background: '#e74c3c' }}
        >
          Reset
        </button>
        
        <button 
          onClick={increment}
          style={buttonStyle}
        >
          + Increase
        </button>
      </div>
    </div>
  );
}

const buttonStyle = {
  padding: '12px 24px',
  fontSize: '16px',
  background: '#3498db',
  color: 'white',
  border: 'none',
  borderRadius: '8px',
  cursor: 'pointer',
  fontWeight: 'bold'
};
```

---

## Tutorial 4: Theme-Aware Widget

### Goal
Create a widget that adapts to ChatGPT's dark/light theme.

### React Component

```jsx
import React from 'react';
import { useWidgetProps, useOpenAiGlobal } from 'chatjs-hooks';

export default function ThemedWidget() {
  const props = useWidgetProps();
  const theme = useOpenAiGlobal('theme');
  
  const isDark = theme === 'dark';
  
  return (
    <div style={{
      padding: '30px',
      background: isDark ? '#1a1a1a' : '#ffffff',
      color: isDark ? '#ffffff' : '#000000',
      borderRadius: '12px',
      border: `2px solid ${isDark ? '#333' : '#ddd'}`
    }}>
      <h1>Theme-Aware Widget</h1>
      <p>Current theme: {theme}</p>
      <p>This widget automatically adapts to your ChatGPT theme!</p>
    </div>
  );
}
```

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def execute(self, input_data):
    try:
        # Your logic
        return {"success": True, "data": data}
    except Exception as e:
        return {"error": str(e), "success": False}
```

### 2. Loading States

Show feedback while loading:

```jsx
const [loading, setLoading] = useState(false);

if (loading) {
  return <div>Loading...</div>;
}
```

### 3. Responsive Design

Make widgets work on different screen sizes:

```jsx
<div style={{
  padding: '20px',
  maxWidth: '600px',
  margin: '0 auto'
}}>
```

### 4. Input Validation

Validate inputs in Python:

```python
class MyInput(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=150)
```

---

## Next Steps

- [API Reference](./API.md)
- [Advanced Features](./ADVANCED.md)
- [Examples](../../examples/)

