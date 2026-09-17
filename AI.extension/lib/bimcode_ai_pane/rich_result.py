"""Native read-only WPF rendering of bounded presentation blocks; no Revit API."""

from bimcode_ai_pane.result_find import fragments


def block_style(kind, in_details=False):
    """Spacing/separators are presentation only, adding no searchable text."""
    return dict(top=18 if kind == "heading" else 12 if kind in ("record", "subheading") else 0,
                bottom=8 if kind in ("heading", "record", "title") else 7,
                indent=12 if in_details and kind not in ("heading", "subheading", "record") else 0,
                separator=kind in ("heading", "record"))


def make_document(presentation, finder=None):
    from System.Windows import Thickness, FontWeights, FontStyles
    from System.Windows.Media import FontFamily
    from System.Windows.Documents import FlowDocument, Paragraph, Run, TextElement

    document = FlowDocument()
    document.FontFamily = FontFamily("Segoe UI")
    document.FontSize = 12
    document.PagePadding = Thickness(10)
    document.ColumnWidth = 1000000  # Single wrapping column, including narrow docks.
    document.SetResourceReference(TextElement.ForegroundProperty, "PrimaryTextBrush")
    by_block = {}
    if finder is not None:
        for number, (index, start, end) in enumerate(finder.matches):
            by_block.setdefault(index, []).append((number, start, end))
    in_details = False
    for index, block in enumerate(presentation["blocks"]):
        paragraph = Paragraph()
        kind = block["kind"]
        if kind == "heading" and block["text"] == "Details":
            in_details = True
        style = block_style(kind, in_details)
        paragraph.Margin = Thickness(style["indent"], style["top"], 0, style["bottom"])
        if style["separator"]:
            paragraph.BorderThickness = Thickness(0, 1, 0, 0)
            paragraph.Padding = Thickness(0, 8, 0, 0)
            paragraph.SetResourceReference(Paragraph.BorderBrushProperty, "BorderBrush")
        if kind in ("title", "heading", "subheading", "record", "status"):
            paragraph.FontWeight = FontWeights.SemiBold
            paragraph.FontSize = 17 if kind == "title" else 12
        if kind == "technical":
            paragraph.FontFamily = FontFamily("Consolas")
            paragraph.FontSize = 11
        if kind in ("note", "bullet"):
            paragraph.FontStyle = FontStyles.Italic if kind == "note" else FontStyles.Normal
        if kind == "bullet":
            paragraph.Margin = Thickness(10, 0, 0, 5)
        for is_label, text, offset in ((True, block["label"], 0),
                                       (False, block["text"], len(block["label"]))):
            for content, highlight in fragments(text, offset, by_block.get(index, []),
                                                finder.current if finder is not None else -1):
                # A wide existing label-space separates the two compact fact
                # columns without a rigid table or extra text/paragraph budget.
                gap = kind == "fact" and is_label and content.endswith(" ")
                run = Run(content[:-1] if gap else content)
                if is_label:
                    run.FontWeight = FontWeights.SemiBold
                    if kind == "fact":
                        run.SetResourceReference(TextElement.ForegroundProperty, "SecondaryTextBrush")
                elif kind == "fact":
                    run.FontWeight = FontWeights.SemiBold
                    run.SetResourceReference(TextElement.ForegroundProperty, "AccentBrush")
                if highlight:
                    run.SetResourceReference(TextElement.BackgroundProperty, highlight)
                    run.SetResourceReference(TextElement.ForegroundProperty,
                                             "SurfaceBrush" if highlight == "AccentBrush" else "PrimaryTextBrush")
                paragraph.Inlines.Add(run)
                if gap:
                    spacer = Run(" ")
                    spacer.FontSize = 32
                    if highlight:
                        spacer.SetResourceReference(TextElement.BackgroundProperty, highlight)
                    paragraph.Inlines.Add(spacer)
                if highlight == "AccentBrush" and document.Tag is None:
                    document.Tag = run
        paragraph.SetResourceReference(TextElement.ForegroundProperty, block["tone"])
        document.Blocks.Add(paragraph)
    return document
