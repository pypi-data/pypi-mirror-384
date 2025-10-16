# Managing Widget State

Learn how to create stateful, interactive widgets that persist data across interactions.

## What is Widget State?

Widget state is data that:
- Persists across widget interactions
- Survives page refreshes
- Is stored in ChatGPT's conversation context
- Can be updated from your React component

## Basic State Management

### useWidgetState Hook

```jsx
import { useWidgetState } from 'fastapps';

export default function Counter() {
  const [state, setState] = useWidgetState({ count: 0 });
  
  const increment = () => {
    setState({ count: state.count + 1 });
  };
  
  return (
    <div>
      <p>Count: {state.count}</p>
      <button onClick={increment}>+1</button>
    </div>
  );
}
```

### API Signature

```typescript
function useWidgetState<T>(initialState: T): [T, (newState: T) => void]
```

- **Parameter**: `initialState` - Initial state object
- **Returns**: `[state, setState]` tuple (like React's useState)

## Common Patterns

### Counter

```jsx
const [state, setState] = useWidgetState({ count: 0 });

const increment = () => setState({ count: state.count + 1 });
const decrement = () => setState({ count: state.count - 1 });
const reset = () => setState({ count: 0 });
```

### Todo List

```jsx
const [state, setState] = useWidgetState({
  todos: [],
  nextId: 1
});

const addTodo = (text) => {
  setState({
    todos: [...state.todos, { id: state.nextId, text, done: false }],
    nextId: state.nextId + 1
  });
};

const toggleTodo = (id) => {
  setState({
    ...state,
    todos: state.todos.map(todo =>
      todo.id === id ? { ...todo, done: !todo.done } : todo
    )
  });
};

const deleteTodo = (id) => {
  setState({
    ...state,
    todos: state.todos.filter(todo => todo.id !== id)
  });
};
```

### Form Data

```jsx
const [state, setState] = useWidgetState({
  name: '',
  email: '',
  submitted: false
});

const handleSubmit = () => {
  if (state.name && state.email) {
    setState({ ...state, submitted: true });
  }
};

const handleChange = (field, value) => {
  setState({ ...state, [field]: value });
};

return (
  <div>
    {!state.submitted ? (
      <form>
        <input
          value={state.name}
          onChange={(e) => handleChange('name', e.target.value)}
          placeholder="Name"
        />
        <input
          value={state.email}
          onChange={(e) => handleChange('email', e.target.value)}
          placeholder="Email"
        />
        <button onClick={handleSubmit}>Submit</button>
      </form>
    ) : (
      <div>[OK] Submitted: {state.name} ({state.email})</div>
    )}
  </div>
);
```

### Pagination

```jsx
export default function PaginatedList() {
  const props = useWidgetProps();
  const [state, setState] = useWidgetState({
    currentPage: 1,
    itemsPerPage: 10
  });
  
  const totalPages = Math.ceil(props.items.length / state.itemsPerPage);
  const startIndex = (state.currentPage - 1) * state.itemsPerPage;
  const currentItems = props.items.slice(
    startIndex,
    startIndex + state.itemsPerPage
  );
  
  const nextPage = () => {
    if (state.currentPage < totalPages) {
      setState({ ...state, currentPage: state.currentPage + 1 });
    }
  };
  
  const prevPage = () => {
    if (state.currentPage > 1) {
      setState({ ...state, currentPage: state.currentPage - 1 });
    }
  };
  
  return (
    <div>
      {currentItems.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
      
      <div>
        <button onClick={prevPage} disabled={state.currentPage === 1}>
          Previous
        </button>
        <span>Page {state.currentPage} of {totalPages}</span>
        <button onClick={nextPage} disabled={state.currentPage === totalPages}>
          Next
        </button>
      </div>
    </div>
  );
}
```

### Filters and Sorting

```jsx
const [state, setState] = useWidgetState({
  filter: 'all',
  sortBy: 'name',
  sortOrder: 'asc'
});

const filteredItems = props.items
  .filter(item => {
    if (state.filter === 'all') return true;
    return item.status === state.filter;
  })
  .sort((a, b) => {
    const modifier = state.sortOrder === 'asc' ? 1 : -1;
    return a[state.sortBy] > b[state.sortBy] ? modifier : -modifier;
  });

return (
  <div>
    <select onChange={(e) => setState({ ...state, filter: e.target.value })}>
      <option value="all">All</option>
      <option value="active">Active</option>
      <option value="done">Done</option>
    </select>
    
    <select onChange={(e) => setState({ ...state, sortBy: e.target.value })}>
      <option value="name">Name</option>
      <option value="date">Date</option>
      <option value="priority">Priority</option>
    </select>
    
    <button onClick={() => setState({
      ...state,
      sortOrder: state.sortOrder === 'asc' ? 'desc' : 'asc'
    })}>
      {state.sortOrder === 'asc' ? '↑' : '↓'}
    </button>
    
    {filteredItems.map(item => (
      <div key={item.id}>{item.name}</div>
    ))}
  </div>
);
```

## Initial State from Backend

### Pattern 1: Simple Default

```python
# Python
async def execute(self, input_data):
    return {
        "items": [...],
        "initialCount": 10
    }
```

```jsx
// React
const props = useWidgetProps();
const [state, setState] = useWidgetState({
  count: props.initialCount || 0
});
```

### Pattern 2: Complex Initial State

```python
# Python
async def execute(self, input_data):
    return {
        "data": [...],
        "initialState": {
            "view": "grid",
            "selectedId": None,
            "filters": {
                "category": "all",
                "status": "active"
            }
        }
    }
```

```jsx
// React
const props = useWidgetProps();
const [state, setState] = useWidgetState(
  props.initialState || {
    view: 'list',
    selectedId: null,
    filters: { category: 'all', status: 'active' }
  }
);
```

## State Persistence

### What Persists?

**Persists:**
- Data stored with `useWidgetState()`
- Across widget refreshes
- In the same conversation

**Doesn't Persist:**
- `React.useState()` - lost on rebuild
- Local variables - lost on re-render
- Browser localStorage - not accessible

### Example: Shopping Cart

```jsx
export default function ShoppingCart() {
  const props = useWidgetProps();
  const [state, setState] = useWidgetState({
    cart: []  // Persists across interactions!
  });
  
  const addToCart = (item) => {
    setState({
      cart: [...state.cart, item]
    });
  };
  
  const removeFromCart = (itemId) => {
    setState({
      cart: state.cart.filter(item => item.id !== itemId)
    });
  };
  
  return (
    <div>
      <h2>Products</h2>
      {props.products.map(product => (
        <div key={product.id}>
          <span>{product.name}</span>
          <button onClick={() => addToCart(product)}>
            Add to Cart
          </button>
        </div>
      ))}
      
      <h2>Cart ({state.cart.length})</h2>
      {state.cart.map(item => (
        <div key={item.id}>
          <span>{item.name}</span>
          <button onClick={() => removeFromCart(item.id)}>
            Remove
          </button>
        </div>
      ))}
    </div>
  );
}
```

## Performance Tips

### 1. Avoid Frequent Updates

```jsx
// Updates on every keystroke
<input onChange={(e) => setState({ text: e.target.value })} />

// Debounce or update on blur
const [text, setText] = React.useState('');

<input
  value={text}
  onChange={(e) => setText(e.target.value)}
  onBlur={() => setState({ text })}
/>
```

### 2. Batch Updates

```jsx
// Multiple state updates
const handleClick = () => {
  setState({ count: state.count + 1 });
  setState({ lastClicked: Date.now() });
  setState({ clicks: state.clicks + 1 });
};

// Single update
const handleClick = () => {
  setState({
    count: state.count + 1,
    lastClicked: Date.now(),
    clicks: state.clicks + 1
  });
};
```

### 3. Only Store What You Need

```jsx
// Storing derived data
const [state, setState] = useWidgetState({
  items: [...],
  filteredItems: [...],  // Can be computed!
  itemCount: 5           // Can be computed!
});

// Store minimal state
const [state, setState] = useWidgetState({
  items: [...],
  filter: 'all'
});

// Compute derived values
const filteredItems = state.items.filter(...);
const itemCount = filteredItems.length;
```

## Common Gotchas

### 1. State is Not Immediate

```jsx
const handleClick = () => {
  setState({ count: state.count + 1 });
  console.log(state.count);  // Still old value!
};

// Use React.useEffect to react to state changes
React.useEffect(() => {
  console.log('Count changed:', state.count);
}, [state.count]);
```

### 2. Object/Array Updates

```jsx
// Mutating state
state.items.push(newItem);  // Doesn't trigger update!

// Create new array
setState({ items: [...state.items, newItem] });

// Mutating object
state.user.name = "New Name";  // Doesn't work!

// Create new object
setState({ user: { ...state.user, name: "New Name" } });
```

### 3. State Initialization

```jsx
// State resets on every render
const props = useWidgetProps();
const [state, setState] = useWidgetState({ 
  count: props.initialCount  // Resets if props change!
});

// Initialize once
const props = useWidgetProps();
const [state, setState] = useWidgetState({ count: 0 });

React.useEffect(() => {
  if (props.initialCount && state.count === 0) {
    setState({ count: props.initialCount });
  }
}, [props.initialCount]);
```

## Advanced Patterns

### State Machine

```jsx
const [state, setState] = useWidgetState({
  status: 'idle'  // idle, loading, success, error
});

const fetchData = async () => {
  setState({ ...state, status: 'loading' });
  
  try {
    const data = await fetch('...');
    setState({ ...state, status: 'success', data });
  } catch (error) {
    setState({ ...state, status: 'error', error: error.message });
  }
};

// Render based on state
if (state.status === 'loading') return <div>Loading...</div>;
if (state.status === 'error') return <div>Error: {state.error}</div>;
if (state.status === 'success') return <div>{state.data}</div>;
return <button onClick={fetchData}>Load Data</button>;
```

### Undo/Redo

```jsx
const [state, setState] = useWidgetState({
  history: [{ count: 0 }],
  currentIndex: 0
});

const currentState = state.history[state.currentIndex];

const updateCount = (newCount) => {
  const newHistory = state.history.slice(0, state.currentIndex + 1);
  newHistory.push({ count: newCount });
  
  setState({
    history: newHistory,
    currentIndex: newHistory.length - 1
  });
};

const undo = () => {
  if (state.currentIndex > 0) {
    setState({ ...state, currentIndex: state.currentIndex - 1 });
  }
};

const redo = () => {
  if (state.currentIndex < state.history.length - 1) {
    setState({ ...state, currentIndex: state.currentIndex + 1 });
  }
};
```

## Best Practices

1. **Keep state minimal** - Store only what can't be computed
2. **Use descriptive names** - `isLoading` not `loading`
3. **Initialize properly** - Provide sensible defaults
4. **Avoid deep nesting** - Flatten state structure when possible
5. **Update immutably** - Always create new objects/arrays
6. **Test state changes** - Verify state updates work correctly

## Next Steps

- [Styling Widgets](./05-STYLING.md) - Advanced styling
- [API Integration](./06-API.md) - External data sources
- [Examples](../examples/) - Real-world stateful widgets

