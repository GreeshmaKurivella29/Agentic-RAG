research_question = "article 21"
query_used = "Article 21 Constitution of India protection of life personal liberty"
badge_bg = "#d1fae5"
badge_color = "#065f46"
badge_text = "✓ Reformulated for Precision"
rationale_html = '<div style="margin-top:4px; font-size:0.75rem; color:#475569;"><em>Rationale:</em> Enriched query with statutory anchors.</div>'
retry_html = ""

query_box_html = f"""<div style="background:#f8f9fa; border:1px solid #c5c6ce; border-left:4px solid #735a3a; border-radius:4px; padding:0.85rem 1rem; margin-bottom:1rem;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
<span style="font-family:'Inter',sans-serif; font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#735a3a;">Stage 2 Search Query Transformation</span>
<span style="font-family:'Inter',sans-serif; font-size:0.65rem; font-weight:700; background:{badge_bg}; color:{badge_color}; padding:2px 8px; border-radius:3px;">{badge_text}</span>
</div>
<div style="font-family:'Inter',sans-serif; font-size:0.85rem; line-height:1.5; color:#1a1c1b;">
<div style="margin-bottom:0.35rem;"><span style="font-weight:600; color:#64748b; font-size:0.75rem; text-transform:uppercase;">Original Inquiry: </span><span style="color:#334155; font-style:italic;">"{research_question}"</span></div>
<div><span style="font-weight:700; color:#0c1b33; font-size:0.75rem; text-transform:uppercase;">Reformulated Search Query: </span><code style="background:#ffffff; border:1px solid #cbd5e1; color:#0c1b33; font-weight:600; font-size:0.83rem; padding:2px 8px; border-radius:3px;">{query_used}</code></div>
{rationale_html}
{retry_html}
</div>
</div>"""

lines = query_box_html.splitlines()
has_indent = any(l.startswith("    ") for l in lines)
print(f"Has 4+ space indentation on any line: {has_indent}")
print("Line prefixes:")
for i, l in enumerate(lines):
    print(f"Line {i}: {l[:15]!r}")
