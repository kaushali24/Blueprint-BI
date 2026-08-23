---
name: ChatInsights Intelligence
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#3d4947'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#6d7a77'
  outline-variant: '#bcc9c6'
  surface-tint: '#006a61'
  primary: '#00685f'
  on-primary: '#ffffff'
  primary-container: '#008378'
  on-primary-container: '#f4fffc'
  inverse-primary: '#6bd8cb'
  secondary: '#5a5f62'
  on-secondary: '#ffffff'
  secondary-container: '#dce0e4'
  on-secondary-container: '#5e6367'
  tertiary: '#8d4b00'
  on-tertiary: '#ffffff'
  tertiary-container: '#b15f00'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#dfe3e7'
  secondary-fixed-dim: '#c3c7cb'
  on-secondary-fixed: '#171c1f'
  on-secondary-fixed-variant: '#43474b'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  metric-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  metric-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  metadata:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-padding: 1rem
  stack-gap-sm: 0.5rem
  stack-gap-md: 1rem
  stack-gap-lg: 1.5rem
  card-padding: 1.25rem
---

## Brand & Style
The design system is built on a **Corporate / Modern** aesthetic with a strong emphasis on **Minimalism**. It is designed to feel intelligent yet approachable for small business owners who need clarity over complexity. The visual narrative centers on "Data Transparency"—using generous white space, a refined teal primary accent, and a rigorous hierarchy to transform dense chat logs into actionable business intelligence. The emotional goal is to move the user from the "chaos" of unorganized messages to the "calm" of structured growth.

## Colors
The palette is anchored by a sophisticated Emerald (#0D9488), intentionally leaning toward a professional teal to differentiate from consumer messaging apps. 

- **Primary**: Used for active navigation states, primary action buttons, and successful status indicators.
- **Surface**: Pure White (#FFFFFF) is the primary canvas to ensure maximum readability for data.
- **Neutrals**: A Slate-based scale is used for structural elements. #F8FAFC and #F1F5F9 serve as background fills to separate content zones without adding visual weight.
- **Semantic**: Amber (#D97706) is reserved for "Pending" states, and Crimson (#E11D48) is used strictly for "Critical" errors or deleted entries.

## Typography
The system utilizes **Inter** for its neutral, systematic character and exceptional legibility at small sizes. 

- **Metrics**: Financial values (Rs.) use `metric-lg` with a slight negative letter-spacing to appear more cohesive. If an amount is missing, use the phrase "Amount unavailable" in `metadata` style.
- **Labels**: Category titles and section headers use `label-caps` in a medium gray to create a clear "eyebrow" above the data they describe.
- **Evidence**: Snippets from WhatsApp conversations should be rendered in `body-md` but contained within specific UI containers to distinguish them from system-generated text.

## Layout & Spacing
This is a **mobile-first** design system utilizing a dynamic 4-column grid for mobile and a 12-column fluid grid for desktop. 

- **Margins**: A standard 16px (1rem) safe area is maintained on all mobile screens.
- **Rhythm**: Use an 8px base unit. Component internal padding is typically 20px (1.25rem) to give financial data room to breathe.
- **Navigation**: The bottom bar is fixed, housing 5 primary destinations: 'Overview', 'Imports', 'Orders', 'Inquiries', and 'Assistant'.

## Elevation & Depth
The system uses **Low-contrast outlines** to maintain a flat, modern business look. 
- **Cards**: Use a 1px solid border (#F1F5F9) instead of heavy shadows. 
- **Subtle Depth**: For the 'Assistant' view or 'AI Evidence' bubbles, a very soft, diffused shadow (Y: 2, Blur: 4, Opacity: 0.05, Color: #1E293B) may be used to indicate interactivity.
- **Overlays**: Modals use a semi-transparent Backdrop Blur (8px) to maintain context while focusing the user on the task.

## Shapes
A "Rounded" strategy (8px) is applied to maintain the "Friendly" brand pillar without appearing juvenile. 

- **Primary Components**: Buttons and Cards use 0.5rem (8px).
- **Secondary Components**: Chips and Badges use a full "Pill" radius for high contrast against the structured squareness of the data cards.
- **Input Fields**: Follow the 0.5rem standard for a consistent form-entry experience.

## Components
- **Metrics Cards**: The hero of the 'Overview'. Features a top-aligned `label-caps`, a center-aligned `metric-lg` (always prefixed with Rs.), and a bottom-aligned `metadata` trend line.
- **AI Evidence Bubbles**: Specialized containers for chat snippets. They use a slightly off-white background (#F8FAFC) and a left-aligned teal border (2px) to signify "extracted intelligence."
- **Status Badges**: Small, pill-shaped indicators. "Confirmed" uses a light teal background with dark teal text. "Pending" uses light amber/dark amber.
- **Action Buttons**: Primary buttons are solid teal (#0D9488) with white text. Secondary buttons are ghost-style with a #E2E8F0 border.
- **Navigation Bar**: High-contrast active icons in teal. Inactive icons in #94A3B8. Label text is always visible below the icon for accessibility.
- **Input Fields**: Minimalist 1px border. On focus, the border transitions to teal with a soft 2px outer glow.