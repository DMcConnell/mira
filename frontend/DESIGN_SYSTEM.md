# Mira Design System

Modern, flat, sleek design system for the Mira smart mirror frontend.

## Design Philosophy

- **Flat Design**: Minimal shadows, clean borders, simple layers
- **High Contrast**: Dark background with crisp text for readability
- **Consistent Spacing**: Using a systematic scale
- **Subtle Animations**: Fast transitions (150-200ms) for responsiveness
- **Typography**: System fonts with careful weight hierarchy

## Color Palette

### Background Colors

- **Primary Background**: `#0a0a0f` - Main app background
- **Surface Background**: `#111115` - Cards and elevated surfaces
- **Secondary Surface**: `#18181b` - Input fields, secondary elements

### Border Colors

- **Primary Border**: `#27272a` - Main borders
- **Secondary Border**: `#3f3f46` - Hover/focus borders

### Text Colors

- **Primary Text**: `#fafafa` - Headings, important text
- **Secondary Text**: `#e4e4e7` - Body text
- **Tertiary Text**: `#a1a1aa` - Labels, metadata
- **Quaternary Text**: `#71717a` - Placeholders, hints
- **Muted Text**: `#52525b` - Very subtle text

### Accent Colors

- **Primary Accent**: `#6366f1` - Indigo, main interactive elements
- **Success**: `#22c55e` - Green, success states
- **Error**: `#dc2626` - Red, error states
- **Warning**: `#fbbf24` - Amber, warning states

## Typography

### Font Family

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
  'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```

### Font Sizes

- **Extra Large**: `clamp(4rem, 12vw, 10rem)` - Ambient clock
- **Large**: `2.5rem` - Major headings
- **Medium**: `1.75rem - 2rem` - Section headings
- **Base**: `0.875rem` (14px) - Body text
- **Small**: `0.75rem` (12px) - Metadata
- **Extra Small**: `0.625rem` (10px) - Fine print

### Font Weights

- **Light**: `300` - Large displays
- **Regular**: `400` - Body text
- **Medium**: `500` - Important text
- **Semibold**: `600` - Headings

## Spacing Scale

- **0.5**: `0.125rem` (2px)
- **1**: `0.25rem` (4px)
- **1.5**: `0.375rem` (6px)
- **2**: `0.5rem` (8px)
- **3**: `0.75rem` (12px)
- **4**: `1rem` (16px)
- **5**: `1.25rem` (20px)
- **6**: `1.5rem` (24px)
- **8**: `2rem` (32px)

## Border Radius

- **Small**: `0.5rem` (8px) - Buttons, inputs
- **Medium**: `0.75rem` (12px) - Small cards
- **Large**: `1rem` (16px) - Large cards, panels

## Components

### Card

```css
background: #111115
border: 1px solid #27272a
border-radius: 0.75rem (12px)
padding: 1.25rem (20px)
```

### Button (Primary)

```css
background: #6366f1
color: white
border-radius: 0.5rem
padding: 0.5rem 1rem
font-size: 0.875rem
font-weight: 500
transition: all 0.15s ease
```

### Button (Secondary)

```css
background: transparent
border: 1px solid #27272a
color: #a1a1aa
hover:background: #18181b
hover:color: #e4e4e7
```

### Input Field

```css
background: #18181b
border: 1px solid #27272a
color: #e4e4e7
border-radius: 0.5rem
padding: 0.5rem 1rem
font-size: 0.875rem
focus:ring: 2px solid #6366f1
```

### Modal/Panel

```css
background: #111115 (or #0a0a0f for drawers)
border: 1px solid #27272a
border-radius: 0.75rem
backdrop: black/60 with blur
```

## Animation Guidelines

### Transitions

- **Fast**: `0.15s ease` - Hover effects, small interactions
- **Medium**: `0.2s ease-out` - Modal appearances, toasts
- **Slow**: `0.3s ease` - Large panels, drawers

### Spring Animations

```js
{ type: 'spring', damping: 30, stiffness: 300 }
```

## Layout

### Grid System

- **Mobile**: 1 column
- **Tablet**: 2 columns
- **Desktop**: 3 columns
- **Large Desktop**: 4 columns
- **Gap**: `1rem` (16px)

### Container

- **Max Width**: `1800px`
- **Padding**: `1.5rem` desktop, `1rem` mobile

## Accessibility

- **Focus States**: 2px solid `#6366f1` outline with 2px offset
- **Contrast Ratios**: All text meets WCAG AA standards
- **Interactive Elements**: Minimum 44x44px touch target
- **Keyboard Navigation**: Full keyboard support throughout

## States

### Hover

- Backgrounds: Lighten by one shade
- Text: Increase opacity or move to next tier
- Borders: Increase opacity

### Active/Selected

- Background: Primary accent color
- Text: White

### Disabled

- Opacity: 0.4
- Cursor: not-allowed

### Loading

- Skeleton: `#27272a` background
- Animation: Pulse

## Best Practices

1. **Use system colors**: Reference the color variables, not hex codes
2. **Consistent spacing**: Use the spacing scale
3. **Flat hierarchy**: Maximum 2-3 levels of visual depth
4. **Fast feedback**: All interactions should feel instant (< 200ms)
5. **Typography hierarchy**: Use size and weight, not color alone
6. **Semantic HTML**: Use appropriate tags for accessibility
7. **Mobile first**: Design for small screens, enhance for large

## Future Enhancements

- Light mode support
- Custom color themes
- Animation preferences (reduced motion)
- High contrast mode
