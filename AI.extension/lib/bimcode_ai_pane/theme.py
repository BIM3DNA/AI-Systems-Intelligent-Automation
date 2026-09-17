"""Presentation-only Revit theme reader and local Workbench-derived palette.

No Workbench import, persisted preference, theme setter, polling or model reads.
Revit 2025 UIApplication.ThemeChanged drives updates; construction/render also
resolve the theme for startup/show and runtimes without the event.
"""

PALETTES = {
    "light": {
        "PaneBackgroundBrush": "#eff6ff", "SurfaceBrush": "#ffffff",
        "BorderBrush": "#cbd5e1", "PrimaryTextBrush": "#1f2937",
        "SecondaryTextBrush": "#4b5563", "AccentBrush": "#0085ff",
        "SuccessBrush": "#047857", "WarningBrush": "#92400e",
        "ErrorBrush": "#b91c1c", "ButtonBackgroundBrush": "#f8fafd",
        "ButtonHoverBrush": "#dbeafe", "DisabledTextBrush": "#6b7280",
    },
    "dark": {
        "PaneBackgroundBrush": "#0f172a", "SurfaceBrush": "#111827",
        "BorderBrush": "#334155", "PrimaryTextBrush": "#f8fafc",
        "SecondaryTextBrush": "#cbd5e1", "AccentBrush": "#38bdf8",
        "SuccessBrush": "#34d399", "WarningBrush": "#fbbf24",
        "ErrorBrush": "#fca5a5", "ButtonBackgroundBrush": "#1f2937",
        "ButtonHoverBrush": "#243244", "DisabledTextBrush": "#94a3b8",
    },
}


def current_theme():
    try:
        from pyrevit import UI
        return "dark" if UI.UIThemeManager.CurrentTheme == UI.UITheme.Dark else "light"
    except Exception:
        return "light"  # Predictable readable fallback; never set Revit's theme.


def apply_resources(resources, name, brush_factory=None):
    if brush_factory is None:
        from System.Windows.Media import ColorConverter, SolidColorBrush

        def brush_factory(color):
            brush = SolidColorBrush(ColorConverter.ConvertFromString(color))
            brush.Freeze()
            return brush

    for key, color in PALETTES.get(name, PALETTES["light"]).items():
        resources[key] = brush_factory(color)
