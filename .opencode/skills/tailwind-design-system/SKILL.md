---
name: tailwind-design-system
description: "Build scalable design systems with Tailwind CSS, design tokens, component libraries, and responsive patterns. Use when creating component libraries, implementing design systems, or standardizing UI patterns. Cluster: JavaScript/TypeScript (SPLIT)"
---

# Scalable Design Systems with Tailwind CSS

Implement robust design systems using Tailwind CSS utility-first approach, focusing on tokenization, configuration, and responsive patterns.

## When to Use This Skill

- Setting up a new component library or UI framework
- Standardizing UI across multiple projects (design tokens)
- Implementing responsive layouts using Tailwind's utility classes
- Integrating Tailwind with component frameworks (React/Vue)
- Enforcing design constraints programmatically

## Core Concepts

### 1. Design Tokens via `tailwind.config.js`
Tailwind's configuration file is the central source of truth for tokens (color, spacing, typography).

-   **Extending Defaults:** Override or add new values rather than redefining core values.
-   **Using Arbitrary Values:** Use square brackets for one-off values (e.g., `text-[13px]`).

### 2. Responsive Design Strategy
-   **Mobile-First:** Design using small breakpoints first, then progressively enhance for larger screens (e.g., `sm:`, `lg:`).
-   **Custom Breakpoints:** Define custom breakpoints in `tailwind.config.js` for component-level responsiveness.

### 3. Component-Driven Design
-   **Composition:** Build complex components from simple, reusable utility classes.
-   **Reusability:** Abstract class names into reusable components in the framework (React, Vue).

## Key Patterns

### Pattern 1: Tokenization and Theming (Cluster: Frontend/UI)

Use Tailwind's theme extension to define design tokens.

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Custom Colors
        'primary': '#007bff',
        'brand-dark': 'hsl(220, 10%, 10%)',
        
        // Theme-specific color mapping (e.g., for dark mode integration)
        'bg-default': 'var(--color-bg-default)',
      },
      spacing: {
        '72': '18rem', // Custom spacing unit
      },
      fontSize: {
        'h1-mobile': '2rem',
        'h1-desktop': '3rem',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('./plugins/custom-plugin'), // For utility injection
  ],
  darkMode: 'class', // Use dark class strategy
}
```

### Pattern 2: Responsive Typography (Cluster: Frontend/UI)
Ensure typography scales appropriately across breakpoints.

```html
<!-- Example in a React component's className -->
<h1 className="text-h1-mobile lg:text-h1-desktop font-bold text-brand-dark lg:text-primary">
    Starship Operations
</h1>
```

### Pattern 3: Abstracting into Components (Cluster: Frontend/UI)
Move utility classes into framework components to keep the markup clean.

```jsx
// MyButton.jsx (React Component)
function MyButton({ children, variant = 'primary', ...props }) {
  const baseClasses = "font-bold py-2 px-4 rounded transition duration-150 shadow-md";
  
  const variantClasses = {
    primary: "bg-primary text-white hover:bg-primary-dark",
    secondary: "bg-gray-200 text-gray-800 hover:bg-gray-300",
  }[variant];

  return (
    <button className={`${baseClasses} ${variantClasses}`} {...props}>
      {children}
    </button>
  );
}
```

## Best Practices

-   **Avoid Overriding Core**: Only use `extend` in `tailwind.config.js`.
-   **Use Configuration**: Inject custom scales (spacing, colors) via config.
-   **Limit JIT**: Use the JIT engine for faster compilation.
-   **Accessibility**: Ensure color contrast meets WCAG standards.
-   **Use Plugins**: Leverage the Tailwind ecosystem for specialized utilities.

## References

-   [Tailwind CSS Documentation](references/tailwind-docs.html)
-   [Tailwind Configuration Guide](references/config-guide.html)
-   [Tailwind Responsive Design](references/responsive-design.html)
-   [Tailwind Plugins Ecosystem](references/plugins-ecosystem.html)

---

**Remember:** Tailwind is a utility-first framework. Use composition and configuration to build a consistent, scalable design system. (Cluster: JavaScript/TypeScript)
