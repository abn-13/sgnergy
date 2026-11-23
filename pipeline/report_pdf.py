"""Repository-written portable renderer, based on original reportlab approach.
Not an exact export of the original chart/styled renderer.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from xml.sax.saxutils import escape

def make_charts(df,cfg,outdir):
    return []

def render_pdf(content,chart_paths,outpath):
    styles = getSampleStyleSheet()
    story = [Paragraph('MONTHLY ENERGY AUDIT',styles['Title']),
             Paragraph(escape(content['client']+' / '+content['month']),styles['Normal']),
             Paragraph(escape(content['disclosure']),styles['Normal'])]
    for section in content['sections']:
        story.append(Paragraph(escape(section['heading']),styles['Heading2']))
        for text in section['paragraphs']:
            story.extend([Paragraph(escape(text),styles['Normal']),Spacer(1,6)])
    story.append(PageBreak())
    story.append(Paragraph('Claim register',styles['Heading1']))
    for c in content['claims']:
        story.append(Paragraph(escape(f"{c['id']}: {c['value']} [{c['label']}] / {c['source']}"),styles['Normal']))
    for e in content['engineer_items']:
        story.append(Paragraph(escape(e['item']+': '+e['flag']),styles['Normal']))
    SimpleDocTemplate(str(outpath),pagesize=A4).build(story)
