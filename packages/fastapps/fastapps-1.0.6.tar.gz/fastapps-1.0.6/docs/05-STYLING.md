# Styling Guide

Learn how to create beautiful, responsive widgets with great UX.

## Inline Styles (Recommended)

### Why Inline Styles?

**Advantages:**
- No build configuration needed
- Scoped to component automatically
- Dynamic based on props/state
- Works in all environments
- Simple and straightforward

**No need for:**
- CSS files
- CSS modules
- Styled-components
- Tailwind (in most cases)

### Basic Styling

```jsx
<div style={{
  padding: '20px',
  margin: '10px',
  background: '#4A90E2',
  color: 'white',
  borderRadius: '8px',
  fontSize: '16px',
  fontFamily: 'system-ui, -apple-system, sans-serif'
}}>
  Content
</div>
```

## Layout Patterns

### Flexbox Layout

```jsx
<div style={{
  display: 'flex',
  flexDirection: 'row',
  gap: '16px',
  alignItems: 'center',
  justifyContent: 'space-between'
}}>
  <div>Left</div>
  <div>Center</div>
  <div>Right</div>
</div>
```

### Grid Layout

```jsx
<div style={{
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
  gap: '16px',
  padding: '20px'
}}>
  {items.map(item => (
    <div key={item.id} style={{
      padding: '16px',
      background: 'white',
      borderRadius: '8px'
    }}>
      {item.name}
    </div>
  ))}
</div>
```

### Centered Content

```jsx
<div style={{
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '200px',
  padding: '20px'
}}>
  <div>Centered content</div>
</div>
```

## Color Schemes

### Gradients

```jsx
<div style={{
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  padding: '40px',
  borderRadius: '12px'
}}>
  Beautiful gradient background
</div>
```

### Shadows

```jsx
<div style={{
  padding: '20px',
  background: 'white',
  borderRadius: '12px',
  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
}}>
  Subtle elevation
</div>

<div style={{
  padding: '20px',
  background: 'white',
  borderRadius: '12px',
  boxShadow: '0 10px 25px rgba(0, 0, 0, 0.15)'
}}>
  Strong elevation
</div>
```

### Color Palettes

```jsx
const colors = {
  primary: '#3498db',
  secondary: '#2ecc71',
  danger: '#e74c3c',
  warning: '#f39c12',
  info: '#3498db',
  light: '#ecf0f1',
  dark: '#2c3e50'
};

<button style={{
  background: colors.primary,
  color: 'white'
}}>
  Primary Button
</button>
```

## Theme Support

### Light/Dark Mode

```jsx
import { useOpenAiGlobal } from 'chatjs-hooks';

export default function ThemedWidget() {
  const theme = useOpenAiGlobal('theme');
  const isDark = theme === 'dark';
  
  const styles = {
    container: {
      background: isDark ? '#1a1a1a' : '#ffffff',
      color: isDark ? '#ffffff' : '#000000',
      border: `1px solid ${isDark ? '#333' : '#ddd'}`,
      padding: '20px',
      borderRadius: '8px'
    },
    button: {
      background: isDark ? '#444' : '#f0f0f0',
      color: isDark ? '#fff' : '#000',
      border: 'none',
      padding: '8px 16px',
      borderRadius: '4px'
    }
  };
  
  return (
    <div style={styles.container}>
      <h1>Theme: {theme}</h1>
      <button style={styles.button}>Button</button>
    </div>
  );
}
```

### Theme Variables

```jsx
const theme = useOpenAiGlobal('theme');

const getThemeColors = (isDark) => ({
  background: isDark ? '#1a1a1a' : '#ffffff',
  text: isDark ? '#ffffff' : '#000000',
  border: isDark ? '#333333' : '#dddddd',
  accent: isDark ? '#667eea' : '#3498db',
  hover: isDark ? '#2a2a2a' : '#f5f5f5'
});

const colors = getThemeColors(theme === 'dark');

return (
  <div style={{ background: colors.background, color: colors.text }}>
    Content
  </div>
);
```

## Responsive Design

### Container Width

```jsx
<div style={{
  width: '100%',
  maxWidth: '800px',
  margin: '0 auto',
  padding: '20px'
}}>
  Responsive container
</div>
```

### Responsive Grid

```jsx
<div style={{
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
  gap: '16px'
}}>
  {/* Automatically adjusts columns based on screen size */}
</div>
```

### Mobile-Friendly Spacing

```jsx
<div style={{
  padding: '16px',      // Mobile
  '@media (min-width: 768px)': {
    padding: '32px'     // Desktop (note: media queries don't work in inline styles)
  }
}}>
  
// Better approach: Use appropriate base values
<div style={{
  padding: 'clamp(16px, 4vw, 32px)',  // Responsive padding
  fontSize: 'clamp(14px, 2vw, 18px)'  // Responsive font
}}>
```

## Common Components

### Button

```jsx
const buttonStyle = {
  padding: '12px 24px',
  fontSize: '16px',
  fontWeight: 'bold',
  color: 'white',
  background: '#3498db',
  border: 'none',
  borderRadius: '8px',
  cursor: 'pointer',
  transition: 'all 0.2s',
  ':hover': {
    background: '#2980b9'  // Note: pseudo-classes don't work in inline styles
  }
};

<button style={buttonStyle} onClick={handleClick}>
  Click Me
</button>

// For hover effects, use state:
const [isHovered, setIsHovered] = React.useState(false);

<button
  style={{
    ...buttonStyle,
    background: isHovered ? '#2980b9' : '#3498db'
  }}
  onMouseEnter={() => setIsHovered(true)}
  onMouseLeave={() => setIsHovered(false)}
>
  Click Me
</button>
```

### Card

```jsx
const cardStyle = {
  padding: '20px',
  background: 'white',
  borderRadius: '12px',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
  border: '1px solid #e0e0e0'
};

<div style={cardStyle}>
  <h3 style={{ margin: '0 0 10px 0' }}>Title</h3>
  <p style={{ margin: 0, color: '#666' }}>Description</p>
</div>
```

### Input

```jsx
const inputStyle = {
  width: '100%',
  padding: '12px',
  fontSize: '16px',
  border: '1px solid #ddd',
  borderRadius: '8px',
  outline: 'none'
};

<input
  type="text"
  placeholder="Enter text..."
  style={inputStyle}
  onFocus={(e) => e.target.style.borderColor = '#3498db'}
  onBlur={(e) => e.target.style.borderColor = '#ddd'}
/>
```

### Badge

```jsx
const badgeStyle = {
  display: 'inline-block',
  padding: '4px 12px',
  fontSize: '12px',
  fontWeight: 'bold',
  background: '#3498db',
  color: 'white',
  borderRadius: '12px'
};

<span style={badgeStyle}>New</span>
```

## Typography

### Headings

```jsx
const headingStyles = {
  h1: {
    fontSize: '32px',
    fontWeight: 'bold',
    margin: '0 0 16px 0',
    lineHeight: '1.2'
  },
  h2: {
    fontSize: '24px',
    fontWeight: '600',
    margin: '0 0 12px 0',
    lineHeight: '1.3'
  },
  h3: {
    fontSize: '18px',
    fontWeight: '600',
    margin: '0 0 8px 0',
    lineHeight: '1.4'
  }
};

<h1 style={headingStyles.h1}>Main Title</h1>
<h2 style={headingStyles.h2}>Subtitle</h2>
<h3 style={headingStyles.h3}>Section</h3>
```

### Body Text

```jsx
<p style={{
  fontSize: '16px',
  lineHeight: '1.6',
  color: '#333',
  margin: '0 0 16px 0'
}}>
  Body text with good readability
</p>
```

## Animations

### Simple Transitions

```jsx
const [isVisible, setIsVisible] = React.useState(false);

<div style={{
  opacity: isVisible ? 1 : 0,
  transform: isVisible ? 'translateY(0)' : 'translateY(-10px)',
  transition: 'all 0.3s ease'
}}>
  Content fades in
</div>
```

### Loading Spinner

```jsx
<div style={{
  width: '40px',
  height: '40px',
  border: '4px solid #f3f3f3',
  borderTop: '4px solid #3498db',
  borderRadius: '50%',
  animation: 'spin 1s linear infinite'
}}>
  {/* Note: @keyframes don't work in inline styles */}
  {/* Use CSS or animated SVG instead */}
</div>
```

## Accessibility

### Semantic HTML

```jsx
// Good
<button onClick={handleClick}>Click</button>
<input type="text" placeholder="Name" />
<label>Name: <input /></label>

// Avoid
<div onClick={handleClick}>Click</div>  // Not keyboard accessible
```

### ARIA Labels

```jsx
<button
  onClick={handleClick}
  aria-label="Close dialog"
  style={{ ... }}
>
  ×
</button>

<input
  type="text"
  aria-label="Search"
  placeholder="Search..."
/>
```

### Focus Styles

```jsx
<button
  style={buttonStyle}
  onFocus={(e) => e.target.style.outline = '2px solid #3498db'}
  onBlur={(e) => e.target.style.outline = 'none'}
>
  Accessible Button
</button>
```

## Design System Example

```jsx
// Define your design tokens
const theme = {
  colors: {
    primary: '#3498db',
    secondary: '#2ecc71',
    danger: '#e74c3c',
    text: '#2c3e50',
    textLight: '#7f8c8d',
    background: '#ffffff',
    border: '#ecf0f1'
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px'
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    full: '9999px'
  },
  shadows: {
    sm: '0 1px 3px rgba(0,0,0,0.1)',
    md: '0 4px 6px rgba(0,0,0,0.1)',
    lg: '0 10px 25px rgba(0,0,0,0.15)'
  }
};

// Use in components
<button style={{
  padding: `${theme.spacing.md} ${theme.spacing.lg}`,
  background: theme.colors.primary,
  color: 'white',
  border: 'none',
  borderRadius: theme.borderRadius.md,
  boxShadow: theme.shadows.md
}}>
  Styled with Design System
</button>
```

## Best Practices

1. **Use system fonts** - Faster loading, native feel
2. **Consistent spacing** - Use multiples of 4px or 8px
3. **Readable contrast** - Min 4.5:1 for text
4. **Touch targets** - Min 44x44px for buttons
5. **Visual hierarchy** - Size, weight, color for importance
6. **White space** - Don't cram content
7. **Consistent borders** - Same radius throughout
8. **Test both themes** - Light and dark modes

## Next Steps

- [API Integration](./06-API.md) - External data
- [Security](./07-SECURITY.md) - CSP and security
- [Examples](../examples/) - Styled widget examples

