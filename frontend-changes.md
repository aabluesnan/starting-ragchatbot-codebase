# Frontend Changes - Dark Mode Toggle Feature

## Overview
Added a dark/light mode toggle button to the Course Materials Assistant interface, allowing users to switch between dark and light themes with their preference persisted across sessions.

## Files Modified

### 1. `frontend/index.html`
**Changes:**
- Added theme toggle button in the header section (lines 17-32)
- Included SVG icons for sun (light mode) and moon (dark mode)
- Button positioned in top-right corner of header
- Added ARIA attributes for accessibility

**New Elements:**
```html
<button id="themeToggle" class="theme-toggle" aria-label="Toggle dark mode" title="Toggle theme">
  <!-- Sun and Moon SVG icons -->
</button>
```

### 2. `frontend/style.css`
**Changes:**

#### Light Mode Color Variables (lines 27-43)
Added `[data-theme="light"]` selector with light mode color palette:
- Background: `#f8fafc` (light gray-blue)
- Surface: `#ffffff` (white)
- Text primary: `#0f172a` (dark blue-gray)
- Text secondary: `#64748b` (medium gray)
- Border: `#e2e8f0` (light gray)
- Maintained same primary blue accent (`#2563eb`)

#### Header Visibility (lines 68-78)
- Changed header from `display: none` to `display: flex`
- Added positioning and styling for header bar
- Added smooth transitions for theme changes

#### Body Transitions (line 55)
- Added `transition: background-color 0.3s ease, color 0.3s ease` for smooth theme switching

#### Theme Toggle Button Styles (lines 808-868)
- Circular button (44x44px) positioned absolutely in top-right
- Hover effect: scales to 110% and changes to primary blue
- Focus state: blue ring for keyboard navigation
- Active state: scales down to 95%
- Icon rotation animation on toggle (360deg spin)
- Conditional icon visibility based on theme attribute

### 3. `frontend/script.js`
**Changes:**

#### DOM Element Addition (line 8)
- Added `themeToggle` to DOM elements list

#### Initialization (lines 19, 22)
- Added `themeToggle = document.getElementById('themeToggle')`
- Added `loadTheme()` call to load saved preference on page load

#### Event Listeners (lines 38-45)
- Click handler for theme toggle button
- Keyboard handler for Enter and Space keys (accessibility)

#### New Functions (lines 230-259)
1. **`loadTheme()`**:
   - Loads theme preference from localStorage
   - Defaults to 'dark' if no preference saved
   - Sets `data-theme` attribute on document root
   - Updates ARIA label

2. **`toggleTheme()`**:
   - Toggles between 'dark' and 'light' themes
   - Adds rotation animation class during transition
   - Saves preference to localStorage
   - Updates ARIA label for screen readers

3. **`updateThemeToggleAriaLabel(theme)`**:
   - Updates button ARIA label based on current theme
   - Improves screen reader accessibility

## Features Implemented

### Visual Design
- ✅ Icon-based design with sun/moon SVG icons
- ✅ Positioned in top-right corner of header
- ✅ Matches existing design aesthetic (primary blue: `#2563eb`)
- ✅ Smooth 300ms transitions for all theme changes
- ✅ 360-degree rotation animation when toggling
- ✅ Hover effect with scale and color change

### Accessibility
- ✅ Keyboard navigable (Tab to focus, Enter/Space to activate)
- ✅ ARIA labels that update based on current theme
- ✅ Focus ring indicator for keyboard users
- ✅ Tooltip on hover (title attribute)

### Functionality
- ✅ Persists user preference in localStorage
- ✅ Loads saved preference on page load
- ✅ Defaults to dark mode (original theme)
- ✅ Smooth transitions between themes
- ✅ All UI elements adapt to theme (sidebar, messages, inputs, buttons)

## Color Palettes

### Dark Mode (Default)
- Background: `#0f172a` (dark blue-gray)
- Surface: `#1e293b` (medium blue-gray)
- Text primary: `#f1f5f9` (off-white)
- Text secondary: `#94a3b8` (light gray)

### Light Mode
- Background: `#f8fafc` (light gray-blue)
- Surface: `#ffffff` (white)
- Text primary: `#0f172a` (dark blue-gray)
- Text secondary: `#64748b` (medium gray)

### Shared Across Themes
- Primary color: `#2563eb` (blue)
- Primary hover: `#1d4ed8` (darker blue)
- User message bubble: `#2563eb` (blue)

## Usage

### For Users
1. Click the sun/moon button in the top-right corner to toggle themes
2. Use keyboard: Tab to focus the button, then press Enter or Space
3. Your preference is automatically saved and restored on next visit

### For Developers
- Theme is controlled via `data-theme` attribute on `<html>` element
- Values: `"dark"` or `"light"`
- Preference stored in localStorage with key `"theme"`
- All colors use CSS variables that automatically adjust per theme

## Browser Compatibility
- Modern browsers with CSS custom properties support
- localStorage support required for persistence
- SVG support for icons
- Works on all screen sizes (responsive)

## Future Enhancements (Optional)
- System preference detection (`prefers-color-scheme` media query)
- Additional theme options (e.g., high contrast, sepia)
- Smooth gradient transitions
- Theme-specific message bubble styles
