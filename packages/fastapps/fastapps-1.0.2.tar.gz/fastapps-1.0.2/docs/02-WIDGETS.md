# Building Widgets (React Components)

Learn how to create beautiful, interactive React components for your ChatGPT widgets.

## What is a Widget?

A widget is a React component that:
- Lives in `widgets/<widget-name>/index.jsx`
- Receives props from your Python tool
- Renders in the ChatGPT interface
- Can be interactive and stateful

## Basic Widget Structure

```jsx
import React from 'react';
import { useWidgetProps } from 'chatjs-hooks';

export default function MyWidget() {
  // 1. Get data from Python backend
  const props = useWidgetProps();
  
  // 2. Render UI
  return (
    <div style={{ padding: '20px' }}>
      <h1>{props.message}</h1>
    </div>
  );
}
```

**That's it!** Every widget follows this pattern.

## Getting Data: useWidgetProps

### Basic Usage

```jsx
const props = useWidgetProps();
// props = whatever your Python execute() returned
```

### With TypeScript

```typescript
interface MyWidgetProps {
  message: string;
  count: number;
  items: string[];
}

export default function MyWidget() {
  const props = useWidgetProps<MyWidgetProps>();
  // props is now typed!
  
  return <div>{props.message}</div>;
}
```

### Handling Missing Props

```jsx
export default function MyWidget() {
  const props = useWidgetProps();
  
  // Use defaults
  const message = props.message || 'No message';
  
  // Or conditional rendering
  if (!props.data) {
    return <div>No data available</div>;
  }
  
  return <div>{props.data}</div>;
}
```

## Styling Widgets

### Inline Styles (Recommended)

```jsx
<div style={{
  padding: '20px',
  background: '#4A90E2',
  color: 'white',
  borderRadius: '12px',
  fontFamily: 'system-ui, -apple-system, sans-serif'
}}>
  Content
</div>
```

**Why inline styles?**
- ✅ No build configuration needed
- ✅ Scoped to component
- ✅ Dynamic based on props
- ✅ Works everywhere

### Responsive Design

```jsx
<div style={{
  padding: '20px',
  maxWidth: '600px',
  margin: '0 auto',
  width: '100%'
}}>
  Content
</div>
```

### Theme Support

```jsx
import { useOpenAiGlobal } from 'chatjs-hooks';

export default function ThemedWidget() {
  const theme = useOpenAiGlobal('theme');
  const isDark = theme === 'dark';
  
  return (
    <div style={{
      background: isDark ? '#1a1a1a' : '#ffffff',
      color: isDark ? '#ffffff' : '#000000',
      padding: '20px',
      borderRadius: '8px'
    }}>
      Content adapts to ChatGPT theme!
    </div>
  );
}
```

## Common Patterns

### Loading State

```jsx
export default function MyWidget() {
  const props = useWidgetProps();
  const [loading, setLoading] = React.useState(false);
  
  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        Loading...
      </div>
    );
  }
  
  return <div>{props.data}</div>;
}
```

### Error Handling

```jsx
export default function MyWidget() {
  const props = useWidgetProps();
  
  if (props.error) {
    return (
      <div style={{
        padding: '20px',
        background: '#fee',
        color: '#c00',
        borderRadius: '8px'
      }}>
        ⚠️ Error: {props.error}
      </div>
    );
  }
  
  return <div>{props.data}</div>;
}
```

### Lists and Tables

```jsx
export default function ListWidget() {
  const props = useWidgetProps();
  
  return (
    <div style={{ padding: '20px' }}>
      <h2>Items</h2>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {props.items.map((item, index) => (
          <li key={index} style={{
            padding: '10px',
            margin: '5px 0',
            background: '#f5f5f5',
            borderRadius: '4px'
          }}>
            {item.name}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Cards

```jsx
export default function CardWidget() {
  const props = useWidgetProps();
  
  return (
    <div style={{
      padding: '20px',
      background: 'white',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      <h2 style={{ margin: '0 0 10px 0' }}>{props.title}</h2>
      <p style={{ color: '#666' }}>{props.description}</p>
    </div>
  );
}
```

### Buttons

```jsx
export default function ButtonWidget() {
  const props = useWidgetProps();
  const [state, setState] = useWidgetState({ clicked: false });
  
  const handleClick = () => {
    setState({ clicked: true });
  };
  
  return (
    <button
      onClick={handleClick}
      style={{
        padding: '12px 24px',
        fontSize: '16px',
        background: state.clicked ? '#27ae60' : '#3498db',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        fontWeight: 'bold'
      }}
    >
      {state.clicked ? '✓ Clicked' : 'Click Me'}
    </button>
  );
}
```

### Grids

```jsx
export default function GridWidget() {
  const props = useWidgetProps();
  
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '16px',
      padding: '20px'
    }}>
      {props.items.map((item, i) => (
        <div key={i} style={{
          padding: '16px',
          background: '#f5f5f5',
          borderRadius: '8px'
        }}>
          <h3>{item.title}</h3>
          <p>{item.description}</p>
        </div>
      ))}
    </div>
  );
}
```

## Advanced Patterns

### Conditional Rendering

```jsx
export default function MyWidget() {
  const props = useWidgetProps();
  
  return (
    <div>
      {props.showHeader && (
        <header>
          <h1>{props.title}</h1>
        </header>
      )}
      
      {props.type === 'list' ? (
        <ul>
          {props.items.map(item => <li key={item.id}>{item.name}</li>)}
        </ul>
      ) : (
        <div>
          <p>{props.content}</p>
        </div>
      )}
      
      {props.showFooter && (
        <footer>
          <p>Footer content</p>
        </footer>
      )}
    </div>
  );
}
```

### Component Composition

```jsx
// Sub-components
function Header({ title }) {
  return <h1 style={{ margin: 0 }}>{title}</h1>;
}

function Card({ title, content }) {
  return (
    <div style={{
      padding: '16px',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h3>{title}</h3>
      <p>{content}</p>
    </div>
  );
}

// Main widget
export default function MyWidget() {
  const props = useWidgetProps();
  
  return (
    <div style={{ padding: '20px' }}>
      <Header title={props.title} />
      
      <div style={{ display: 'flex', gap: '16px', marginTop: '20px' }}>
        {props.cards.map(card => (
          <Card key={card.id} title={card.title} content={card.content} />
        ))}
      </div>
    </div>
  );
}
```

### Custom Hooks

```jsx
import { useWidgetProps } from 'chatjs-hooks';
import React from 'react';

// Custom hook for derived data
function useFilteredItems(items, filter) {
  return React.useMemo(() => {
    return items.filter(item => item.category === filter);
  }, [items, filter]);
}

export default function FilterWidget() {
  const props = useWidgetProps();
  const [filter, setFilter] = React.useState('all');
  
  const filteredItems = useFilteredItems(props.items, filter);
  
  return (
    <div>
      <select onChange={(e) => setFilter(e.target.value)}>
        <option value="all">All</option>
        <option value="active">Active</option>
        <option value="done">Done</option>
      </select>
      
      {filteredItems.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
}
```

## Performance Tips

### 1. Use React.memo for Expensive Components

```jsx
const ExpensiveCard = React.memo(({ data }) => {
  // Expensive rendering logic
  return <div>...</div>;
});

export default function MyWidget() {
  const props = useWidgetProps();
  
  return (
    <div>
      {props.items.map(item => (
        <ExpensiveCard key={item.id} data={item} />
      ))}
    </div>
  );
}
```

### 2. Avoid Inline Functions in Loops

```jsx
// ❌ Bad: Creates new function on every render
{items.map(item => (
  <button onClick={() => handleClick(item)}>...</button>
))}

// ✅ Good: Stable references
{items.map(item => (
  <button onClick={handleClick} data-id={item.id}>...</button>
))}
```

### 3. Use useMemo for Expensive Calculations

```jsx
import React from 'react';

export default function MyWidget() {
  const props = useWidgetProps();
  
  const sortedItems = React.useMemo(() => {
    return props.items.sort((a, b) => a.priority - b.priority);
  }, [props.items]);
  
  return <div>{/* render sortedItems */}</div>;
}
```

## Debugging

### Console Logging

```jsx
export default function MyWidget() {
  const props = useWidgetProps();
  
  // Debug props
  React.useEffect(() => {
    console.log('Widget props:', props);
  }, [props]);
  
  return <div>...</div>;
}
```

### Error Boundaries

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false };
  
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }
  
  render() {
    if (this.state.hasError) {
      return <div>Something went wrong</div>;
    }
    return this.props.children;
  }
}

export default function MyWidget() {
  return (
    <ErrorBoundary>
      {/* Your widget code */}
    </ErrorBoundary>
  );
}
```

## Best Practices

1. **Keep it simple** - One widget, one responsibility
2. **Use semantic HTML** - `<header>`, `<main>`, `<footer>`
3. **Provide feedback** - Loading states, error messages
4. **Be responsive** - Works on different screen sizes
5. **Handle edge cases** - Empty data, errors, loading
6. **Test with themes** - Light and dark modes
7. **Avoid external dependencies** - Use React built-ins
8. **Optimize images** - Use appropriate sizes

## Common Gotchas

### 1. Props Are Async

```jsx
// ❌ Props might be empty initially
const props = useWidgetProps();
console.log(props.data.value); // Error if data is undefined

// ✅ Always check
const value = props.data?.value || 'default';
```

### 2. State Doesn't Persist Across Rebuilds

```jsx
// ❌ useState is lost on rebuild
const [count, setCount] = React.useState(0);

// ✅ Use useWidgetState for persistence
const [state, setState] = useWidgetState({ count: 0 });
```

### 3. Styles Need Units

```jsx
// ❌ Missing units
<div style={{ padding: 20 }}>

// ✅ Include units
<div style={{ padding: '20px' }}>
```

## Next Steps

- [Building Tools](./03-TOOLS.md) - Python backend
- [Managing State](./04-STATE.md) - Persistent state
- [Styling Guide](./05-STYLING.md) - Advanced styling
- [Examples](../examples/) - Real-world widgets

