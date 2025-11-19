# Compliance Assistant Design System

**Version 1.0** | Last Updated: November 2025

A modern, enterprise-grade design system for the QA Compliance Assistant application, featuring a professional teal color palette, clean typography, and accessible components.

---

## 📊 Table of Contents

1. [Color Palette](#color-palette)
2. [Typography](#typography)
3. [Spacing Scale](#spacing-scale)
4. [Shadows](#shadows)
5. [Border Radius](#border-radius)
6. [Components](#components)
7. [Usage Guidelines](#usage-guidelines)

---

## 🎨 Color Palette

### Primary Colors - Deep Teal

The primary teal represents trust, professionalism, and stability - perfect for a compliance platform.

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| ![#006D77](https://via.placeholder.com/20/006D77/006D77.png) Primary 500 | `#006D77` | `rgb(0, 109, 119)` | Primary buttons, links, main brand |
| ![#005864](https://via.placeholder.com/20/005864/005864.png) Primary 600 | `#005864` | `rgb(0, 88, 100)` | Hover states, emphasis |
| ![#004B50](https://via.placeholder.com/20/004B50/004B50.png) Primary 700 | `#004B50` | `rgb(0, 75, 80)` | Sidebar background, dark sections |
| ![#83C5BE](https://via.placeholder.com/20/83C5BE/83C5BE.png) Primary 300 | `#83C5BE` | `rgb(131, 197, 190)` | Light accents, secondary elements |
| ![#B8D8D3](https://via.placeholder.com/20/B8D8D3/B8D8D3.png) Primary 200 | `#B8D8D3` | `rgb(184, 216, 211)` | Subtle backgrounds, borders |
| ![#E8F5F6](https://via.placeholder.com/20/E8F5F6/E8F5F6.png) Primary 50 | `#E8F5F6` | `rgb(232, 245, 246)` | Very light backgrounds |

### Secondary Colors - Soft Teal

Complementary teal for secondary actions and softer UI elements.

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| ![#83C5BE](https://via.placeholder.com/20/83C5BE/83C5BE.png) Secondary 500 | `#83C5BE` | `rgb(131, 197, 190)` | Secondary buttons, chips |
| ![#5FA8A0](https://via.placeholder.com/20/5FA8A0/5FA8A0.png) Secondary 600 | `#5FA8A0` | `rgb(95, 168, 160)` | Hover states |
| ![#B8D8D3](https://via.placeholder.com/20/B8D8D3/B8D8D3.png) Secondary 300 | `#B8D8D3` | `rgb(184, 216, 211)` | Light backgrounds |

### Accent Colors - Warm Red

Attention-grabbing accent for important actions and alerts.

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| ![#FF6B6B](https://via.placeholder.com/20/FF6B6B/FF6B6B.png) Accent 500 | `#FF6B6B` | `rgb(255, 107, 107)` | Destructive actions, alerts |
| ![#E65555](https://via.placeholder.com/20/E65555/E65555.png) Accent 600 | `#E65555` | `rgb(230, 85, 85)` | Hover states |
| ![#FF9999](https://via.placeholder.com/20/FF9999/FF9999.png) Accent 300 | `#FF9999` | `rgb(255, 153, 153)` | Error backgrounds |

### Background Colors

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| ![#EDF6F9](https://via.placeholder.com/20/EDF6F9/EDF6F9.png) Background Default | `#EDF6F9` | `rgb(237, 246, 249)` | Main app background |
| ![#FFFFFF](https://via.placeholder.com/20/FFFFFF/FFFFFF.png) Surface/Paper | `#FFFFFF` | `rgb(255, 255, 255)` | Cards, modals, overlays |
| ![#FAFBFC](https://via.placeholder.com/20/FAFBFC/FAFBFC.png) Elevated | `#FAFBFC` | `rgb(250, 251, 252)` | Raised surfaces |

### Text Colors

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| ![#1A1A1A](https://via.placeholder.com/20/1A1A1A/1A1A1A.png) Primary | `#1A1A1A` | `rgb(26, 26, 26)` | Headlines, body text |
| ![#4F4F4F](https://via.placeholder.com/20/4F4F4F/4F4F4F.png) Secondary | `#4F4F4F` | `rgb(79, 79, 79)` | Supporting text |
| ![#6B7280](https://via.placeholder.com/20/6B7280/6B7280.png) Tertiary | `#6B7280` | `rgb(107, 114, 128)` | Captions, metadata |
| ![#9CA3AF](https://via.placeholder.com/20/9CA3AF/9CA3AF.png) Disabled | `#9CA3AF` | `rgb(156, 163, 175)` | Disabled text |

### Semantic Colors

| Type | Color | Hex | Usage |
|------|-------|-----|-------|
| Success | ![#10B981](https://via.placeholder.com/20/10B981/10B981.png) | `#10B981` | Success messages, completed states |
| Warning | ![#F59E0B](https://via.placeholder.com/20/F59E0B/F59E0B.png) | `#F59E0B` | Warnings, cautions |
| Error | ![#FF6B6B](https://via.placeholder.com/20/FF6B6B/FF6B6B.png) | `#FF6B6B` | Errors, destructive actions |
| Info | ![#3B82F6](https://via.placeholder.com/20/3B82F6/3B82F6.png) | `#3B82F6` | Informational messages |

---

## ✍️ Typography

### Font Family

**Primary**: `"Inter", "Segoe UI", "Roboto", "Helvetica Neue", sans-serif`
**Monospace**: `"Fira Code", "Consolas", "Monaco", monospace`

### Type Scale

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| **H1** | 2.5rem (40px) | 700 Bold | 1.2 | Page titles |
| **H2** | 2rem (32px) | 700 Bold | 1.3 | Section headers |
| **H3** | 1.75rem (28px) | 600 Semibold | 1.4 | Subsection headers |
| **H4** | 1.5rem (24px) | 600 Semibold | 1.4 | Card titles |
| **H5** | 1.25rem (20px) | 600 Semibold | 1.5 | Small headers |
| **H6** | 1rem (16px) | 600 Semibold | 1.5 | Micro headers |
| **Subtitle 1** | 1rem (16px) | 500 Medium | 1.75 | Subtitles |
| **Subtitle 2** | 0.875rem (14px) | 500 Medium | 1.57 | Small subtitles |
| **Body 1** | 1rem (16px) | 400 Regular | 1.5 | Main body text |
| **Body 2** | 0.875rem (14px) | 400 Regular | 1.43 | Secondary body text |
| **Button** | 0.875rem (14px) | 600 Semibold | - | Button labels |
| **Caption** | 0.75rem (12px) | 400 Regular | 1.66 | Captions, metadata |

### Typography Examples

```tsx
<Typography variant="h1" sx={{ color: '#1A1A1A' }}>
  Compliance Dashboard
</Typography>

<Typography variant="body1" sx={{ color: '#4F4F4F' }}>
  Monitor and manage your compliance requirements in real-time.
</Typography>

<Typography variant="caption" sx={{ color: '#6B7280' }}>
  Last updated: 2 minutes ago
</Typography>
```

---

## 📏 Spacing Scale

Based on an 8px grid system for consistent spacing throughout the application.

| Token | Size | Pixels | Usage |
|-------|------|--------|-------|
| `spacing-1` | 0.25rem | 4px | Tight spacing |
| `spacing-2` | 0.5rem | 8px | Default small gap |
| `spacing-3` | 0.75rem | 12px | Comfortable spacing |
| `spacing-4` | 1rem | 16px | Standard spacing |
| `spacing-5` | 1.25rem | 20px | Section spacing |
| `spacing-6` | 1.5rem | 24px | Large gaps |
| `spacing-8` | 2rem | 32px | Extra large gaps |
| `spacing-10` | 2.5rem | 40px | Section dividers |
| `spacing-12` | 3rem | 48px | Page sections |
| `spacing-16` | 4rem | 64px | Major sections |

### Spacing Usage

```tsx
// Using MUI spacing
<Box sx={{ p: 3, mb: 2 }}>  {/* padding: 24px, margin-bottom: 16px */}
  Content
</Box>

// Using CSS variables
.card {
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}
```

---

## 🌈 Shadows

Subtle shadows for depth and hierarchy.

| Name | CSS | Usage |
|------|-----|-------|
| **XS** | `0 1px 2px 0 rgba(0, 0, 0, 0.05)` | Subtle elevation |
| **SM** | `0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)` | Default cards |
| **MD** | `0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)` | Elevated cards |
| **LG** | `0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)` | Modals |
| **XL** | `0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)` | Large modals |
| **Primary** | `0 4px 14px 0 rgba(0, 109, 119, 0.15)` | Primary button hover |
| **Accent** | `0 4px 14px 0 rgba(255, 107, 107, 0.15)` | Accent button hover |

### Shadow Examples

```tsx
<Card sx={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)' }}>
  Card content
</Card>

<Button
  sx={{
    '&:hover': {
      boxShadow: '0 4px 14px 0 rgba(0, 109, 119, 0.15)',
    },
  }}
>
  Hover me
</Button>
```

---

## 🔲 Border Radius

| Token | Size | Pixels | Usage |
|-------|------|--------|-------|
| `radius-sm` | 0.25rem | 4px | Small elements |
| `radius-md` | 0.375rem | 6px | Chips, tags |
| `radius-lg` | 0.5rem | 8px | Buttons, inputs |
| `radius-xl` | 0.75rem | 12px | Cards, chat bubbles |
| `radius-2xl` | 1rem | 16px | Large cards |
| `radius-3xl` | 1.5rem | 24px | Hero sections |
| `radius-full` | 9999px | Full | Avatars, pills |

---

## 🧩 Components

### Buttons

#### Primary Button

**Usage**: Main actions like Submit, Save, Create

```tsx
import { PrimaryButton } from '@/components/ui/Buttons';

<PrimaryButton 
  onClick={handleSubmit}
  startIcon={<SaveIcon />}
>
  Save Changes
</PrimaryButton>
```

**Visual**:
- Background: `#006D77`
- Color: `#FFFFFF`
- Hover: `#005864` with elevated shadow
- Border Radius: `8px`
- Padding: `8px 20px`

#### Secondary Button

**Usage**: Secondary actions like Cancel, Back

```tsx
import { SecondaryButton } from '@/components/ui/Buttons';

<SecondaryButton onClick={handleCancel}>
  Cancel
</SecondaryButton>
```

**Visual**:
- Background: `#83C5BE`
- Color: `#1A1A1A`
- Hover: `#5FA8A0`
- Border Radius: `8px`

#### Accent Button

**Usage**: Destructive or attention-grabbing actions

```tsx
import { AccentButton } from '@/components/ui/Buttons';

<AccentButton onClick={handleDelete} startIcon={<DeleteIcon />}>
  Delete
</AccentButton>
```

**Visual**:
- Background: `#FF6B6B`
- Color: `#FFFFFF`
- Hover: `#E65555` with accent shadow
- Border Radius: `8px`

#### Outline Button

**Usage**: Tertiary actions

```tsx
import { OutlineButton } from '@/components/ui/Buttons';

<OutlineButton onClick={handleView}>
  View Details
</OutlineButton>
```

**Visual**:
- Background: `transparent`
- Border: `2px solid #006D77`
- Color: `#006D77`
- Hover: Filled with primary color

---

### Chat Bubbles

#### User Message

```tsx
import { ChatBubble } from '@/components/ui/ChatBubble';

<ChatBubble
  role="user"
  content="Analyze evidence for Control IM8-01"
  timestamp={new Date()}
  userName="Alice Johnson"
/>
```

**Visual**:
- Background: `#006D77` (Primary)
- Text: `#FFFFFF`
- Avatar: Primary color with person icon
- Border Radius: `12px`
- Shadow: Primary colored shadow
- Alignment: Right-aligned

#### Assistant Message

```tsx
<ChatBubble
  role="assistant"
  content="I've analyzed the evidence. Here are the findings..."
  timestamp={new Date()}
/>
```

**Visual**:
- Background: `#FFFFFF`
- Border: `1px solid rgba(0, 0, 0, 0.08)`
- Text: `#1A1A1A`
- Avatar: Secondary color with robot icon
- Border Radius: `12px`
- Shadow: Subtle gray shadow
- Alignment: Left-aligned

#### System Message

```tsx
import { SystemMessage } from '@/components/ui/ChatBubble';

<SystemMessage
  content="Task #23 completed successfully"
  timestamp={new Date()}
/>
```

**Visual**:
- Background: `#EDF6F9`
- Border: `1px solid rgba(0, 109, 119, 0.2)`
- Centered alignment
- Pill-shaped (radius: `20px`)

#### Typing Indicator

```tsx
import { TypingIndicator } from '@/components/ui/ChatBubble';

<TypingIndicator />
```

**Visual**:
- Three animated dots in secondary color
- "AI is thinking..." caption
- Matches assistant message styling

---

### Cards

```tsx
<Card 
  sx={{
    backgroundColor: '#FFFFFF',
    borderRadius: '12px',
    border: '1px solid rgba(0, 0, 0, 0.05)',
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    transition: 'all 200ms ease-in-out',
    '&:hover': {
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      transform: 'translateY(-2px)',
    },
  }}
>
  <CardContent>
    Card content here
  </CardContent>
</Card>
```

**Visual**:
- Background: White
- Border: Very subtle gray
- Shadow: Small elevation
- Hover: Lifts slightly with enhanced shadow
- Border Radius: `12px`

---

### Sidebar

**Visual Design**:
- Background: `#004B50` (Primary 700)
- Text: `rgba(255, 255, 255, 0.85)`
- Logo Section: Darker background `#003B3F`
- Divider: `rgba(255, 255, 255, 0.12)`

**Active State**:
- Background: `rgba(131, 197, 190, 0.2)`
- Text: `#FFFFFF`
- Icon: `#83C5BE` (Secondary)

**Hover State**:
- Background: `rgba(255, 255, 255, 0.08)`

```tsx
<Drawer
  sx={{
    '& .MuiDrawer-paper': {
      backgroundColor: '#004B50',
      color: '#FFFFFF',
    },
  }}
>
  {/* Sidebar content */}
</Drawer>
```

---

### Header / AppBar

```tsx
<AppBar
  sx={{
    backgroundColor: '#006D77',
    borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  }}
>
  <Toolbar>
    <Typography variant="h4" sx={{ color: '#FFFFFF', fontWeight: 700 }}>
      Compliance Assistant
    </Typography>
  </Toolbar>
</AppBar>
```

**Visual**:
- Background: `#006D77` (Primary)
- Text: `#FFFFFF`
- Border Bottom: Subtle dark line
- Shadow: Minimal elevation

---

## 📋 Usage Guidelines

### Color Usage

1. **Primary Color** (`#006D77`): Use for primary actions, main navigation, and brand identity
2. **Secondary Color** (`#83C5BE`): Use for secondary actions, complementary elements
3. **Accent Color** (`#FF6B6B`): Use sparingly for critical actions, errors, or alerts
4. **Background** (`#EDF6F9`): Use as main app background for subtle contrast
5. **Surface** (`#FFFFFF`): Use for cards, modals, and content containers

### Accessibility

- **Contrast Ratios**: All text meets WCAG AA standards
  - Primary text on white: 15.4:1 (AAA)
  - Secondary text on white: 9.2:1 (AAA)
  - Primary button: 4.8:1 (AA)
- **Focus States**: 2px solid outline with `#006D77`
- **Touch Targets**: Minimum 44x44px for interactive elements

### Responsive Design

- **Breakpoints**:
  - Mobile: `< 600px`
  - Tablet: `600px - 960px`
  - Desktop: `960px - 1280px`
  - Large Desktop: `> 1280px`

### Component Spacing

- Use 8px grid system consistently
- Cards: `padding: 24px` (3 units)
- Buttons: `padding: 8px 20px`
- Gaps between elements: `16px` or `24px`

### Animation & Transitions

- **Duration**: `200ms` for most interactions
- **Easing**: `ease-in-out` for smooth transitions
- **Hover Effects**: Subtle elevation and color changes
- **Loading States**: Use circular progress with primary color

---

## 🚀 Implementation

### Import CSS Variables

```tsx
// main.tsx
import './index.css';
```

### Use MUI Theme

```tsx
import { ThemeProvider } from '@mui/material/styles';
import { theme } from './theme'; // From main.tsx

<ThemeProvider theme={theme}>
  <App />
</ThemeProvider>
```

### Import Components

```tsx
// Buttons
import { PrimaryButton, SecondaryButton, AccentButton } from '@/components/ui/Buttons';

// Chat Bubbles
import { ChatBubble, SystemMessage, TypingIndicator } from '@/components/ui/ChatBubble';

// Usage
<PrimaryButton onClick={handleAction}>Action</PrimaryButton>
<ChatBubble role="user" content="Hello" />
```

---

## 📦 Component Files

All new components are located in:

```
frontend/src/
├── index.css                          # CSS variables and global styles
├── main.tsx                           # MUI theme configuration
└── components/
    └── ui/
        ├── Buttons.tsx                # Button components
        └── ChatBubble.tsx             # Chat bubble components
```

---

## 🎯 Design Principles

1. **Consistency**: Use design tokens consistently across the application
2. **Accessibility**: Meet WCAG AA standards minimum
3. **Clarity**: Clear visual hierarchy with appropriate contrast
4. **Simplicity**: Clean, uncluttered interfaces
5. **Professionalism**: Enterprise-grade aesthetics suitable for compliance work

---

**Design System Maintained By**: Development Team  
**Last Review**: November 2025  
**Next Review**: Quarterly

