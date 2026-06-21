The `sage-faculty-twin` frontend employs a **vanilla CSS** architecture, avoiding external UI frameworks (like Tailwind, Bootstrap, or React) in favor of a custom, hand-crafted design system. The UI is characterized by a **glassmorphic aesthetic** with soft shadows, rounded corners, and backdrop blurs, creating a modern, layered interface.

### 1. Styling Architecture
- **Methodology**: Custom CSS variables (CSS Custom Properties) are used extensively for theming, spacing, and typography. The stylesheet (`styles.css`) is monolithic (~5,800 lines) but organized into logical sections (e.g., "Sidebar Redesign", "Token Usage", "Workflow Shell").
- **No Preprocessors**: The project uses raw CSS without Sass/Less, relying on native CSS features like `calc()`, `clamp()`, and custom properties for dynamic values.
- **Component Library**: None. UI components (buttons, cards, modals, inputs) are implemented as semantic HTML elements styled directly via CSS classes.

### 2. Design Tokens & Theme
- **Color Palette**: Defined in `:root` within `styles.css`.
  - **Backgrounds**: `--bg` (#f7f7f8), `--surface` (#ffffff), `--surface-soft` (#f2f2f4).
  - **Typography**: `--ink` (#202123) for primary text, `--muted` (#6e6e80) for secondary text.
  - **Accents**: `--accent` (#2f6fed) for primary actions, `--accent-deep` (#1f5bd8) for hover states.
  - **Status**: `--success` (#eff7ef), `--error` (#fff1ef).
- **Typography**: 
  - Primary Font: `IBM Plex Sans` (sans-serif).
  - Display/Heading Font: `Space Grotesk` (used for brand elements and large numbers).
  - Fonts are loaded from Google Fonts in `index.html`.
- **Spacing & Radius**:
  - Radii: `--radius-xl` (20px), `--radius-lg` (16px), `--radius-md` (14px).
  - Shadows: Soft, diffuse shadows (`--shadow`, `--shadow-strong`) using low-opacity rgba values.

### 3. Responsive Strategy
- **Breakpoints**: Primarily uses `@media (max-width: 720px)` for mobile adaptations and `@media (max-width: 920px)` for tablet/narrow desktop layouts.
- **Layout**: 
  - Uses CSS Grid for the main chat layout (`.chat-layout`).
  - Flexbox is used for component internals (topbar, buttons, cards).
  - Mobile-specific adjustments include hiding the sidebar, collapsing the topbar, and enabling touch-friendly targets.
- **Accessibility**: Includes `prefers-reduced-motion` media query to disable animations for users who prefer it. Uses `.sr-only` class for screen-reader-only text.

### 4. Key Files
- `src/sage_faculty_twin/web/styles.css`: The single source of truth for all visual styles. Contains ~5,800 lines of CSS.
- `src/sage_faculty_twin/web/index.html`: The shell HTML, importing fonts and the stylesheet. Uses semantic HTML5 tags (`header`, `main`, `aside`, `section`).
- `src/sage_faculty_twin/web/app.js`: Vanilla JavaScript handling DOM manipulation, state management, and API interactions. No framework (React/Vue/Angular) is used.

### 5. Developer Conventions
- **Class Naming**: Uses descriptive, kebab-case class names (e.g., `.topbar-user-badge`, `.chat-stream`, `.workflow-shell`). No strict BEM methodology is enforced, but naming is generally consistent.
- **State Management**: UI state (e.g., modal visibility, drawer open/close) is managed via JS toggling CSS classes (e.g., `body.drawer-pinned`, `.hidden`).
- **Icons**: Inline SVGs are used for icons, allowing for easy styling via `currentColor` and avoiding external icon font dependencies.
- **Animations**: Subtle transitions (`transition: background 120ms ease`) are applied to interactive elements. Backdrop filters (`backdrop-filter: blur(16px)`) are used for glassmorphic effects on modals and panels.