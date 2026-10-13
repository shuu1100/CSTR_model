/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Scientific Workstation Light Canvas & Structure
        "canvas-bg": "#F0F5FA",
        "sidebar-bg": "#E2ECF5",
        "sidebar-header": "#DAE8F4",
        "surface-white": "#FFFFFF",
        "surface-panel-soft": "#F4F8FC",
        "border-grid": "#CBD9E8",
        "border-subtle": "#D5E1EE",
        "text-primary": "#0F1E2E",
        "text-secondary": "#4E657E",

        // Primary & Engineering Accents
        "primary": "#006194",
        "primary-container": "#007bb9",
        "primary-fixed": "#cce5ff",
        "primary-fixed-dim": "#93ccff",
        "secondary": "#0051d5",
        "secondary-container": "#316bf3",
        "tertiary": "#00685f",
        "tertiary-container": "#008378",

        // Semantic Status
        "status-success": "#059669",
        "status-warning": "#D97706",
        "status-critical": "#DC2626",

        // Tonal containers
        "surface-container": "#e4efff",
        "surface-container-high": "#daeaff",
        "surface-container-highest": "#cfe5ff",
        "surface-container-low": "#eef4ff",
        "surface-container-lowest": "#ffffff",
        "surface-variant": "#cfe5ff",
        "on-surface": "#021d33",
        "on-surface-variant": "#4E657E",
        "outline": "#707881",
        "outline-variant": "#cbd9e8",
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        "data-display-lg": ["JetBrains Mono", "monospace"],
        "data-display-md": ["JetBrains Mono", "monospace"],
        "data-mono-sm": ["JetBrains Mono", "monospace"],
        "unit-label": ["JetBrains Mono", "monospace"],
        "headline-xl": ["Inter", "sans-serif"],
        "headline-lg": ["Inter", "sans-serif"],
        "headline-md": ["Inter", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "body-sm": ["Inter", "sans-serif"],
        "label-caps": ["Inter", "sans-serif"],
      },
      boxShadow: {
        '2xs': '0 1px 2px rgba(15, 30, 46, 0.04)',
        'xs': '0 1px 3px rgba(15, 30, 46, 0.06)',
        'card': '0 1px 3px rgba(15, 30, 46, 0.05), 0 1px 2px rgba(15, 30, 46, 0.03)',
      }
    },
  },
  plugins: [],
}
