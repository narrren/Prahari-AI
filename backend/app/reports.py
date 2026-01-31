import io
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

def generate_efir_pdf(incident_data):
    """
    incident_data: {tourist_id, permit_id, lat, lng, risk_score, factors, blockchain_txid}
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    header_style = ParagraphStyle('Header', fontSize=18, leading=22, alignment=1, textColor=colors.navy)
    sub_header_style = ParagraphStyle('SubHeader', fontSize=12, alignment=1, spaceAfter=20)
    
    story = []

    # 1. Header (MoDoNER / Sentinel Logo)
    story.append(Paragraph("<b>GOVERNMENT OF INDIA</b>", header_style))
    story.append(Paragraph("Ministry of Development of North Eastern Region (MoDoNER)", sub_header_style))
    story.append(Paragraph("SENTINEL INCIDENT RESPONSE SYSTEM - E-FIR COPY", styles['Heading2']))
    story.append(Spacer(1, 12))

    # 2. Blockchain Trust Anchor (Crucial for Production)
    story.append(Paragraph(f"<b>Blockchain Proof (TXID):</b> <font color='blue'>{incident_data.get('blockchain_txid', 'PENDING')}</font>", styles['Normal']))
    story.append(Spacer(1, 12))

    # 3. Primary Incident Data Table
    data = [
        ["Field", "Details"],
        ["Tourist DID", incident_data.get('did', incident_data.get('tourist_id', 'Unknown'))],
        ["Permit Reference", incident_data.get('permit_id', 'N/A')],
        ["Last Known Lat", str(incident_data.get('location', {}).get('lat', 'N/A'))],
        ["Last Known Lng", str(incident_data.get('location', {}).get('lng', 'N/A'))],
        ["AI Risk Score", f"{incident_data.get('risk_score', 'N/A')}/100"],
        ["Incident Reason", ", ".join(incident_data.get('factors', []))],
    ]
    
    t = Table(data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # 4. QR Code for Field Verification
    # Logic: QR contains a link to the blockchain explorer or the permit status page
    qr_data = f"https://sentinel.ner.gov.in/verify/{incident_data.get('blockchain_txid', 'null')}"
    qr = qrcode.make(qr_data)
    qr_img_buffer = io.BytesIO()
    qr.save(qr_img_buffer, format='PNG')
    qr_img_buffer.seek(0)
    
    story.append(Paragraph("<b>Scan for Real-time Verification:</b>", styles['Normal']))
    story.append(Image(qr_img_buffer, width=100, height=100))
    story.append(Spacer(1, 20))

    # 4. INCIDENT CHRONOLOGY (LEGAL TIMELINE)
    story.append(Paragraph("<b>4. INCIDENT CHRONOLOGY (LEGAL TIMELINE)</b>", styles['Heading3']))
    story.append(Spacer(1, 6))
    
    import time # Ensure import inside or top, here relying on top scope if possible or re-import
    
    t_data = [["Time (UTC)", "Event", "Actor", "Details"]]
    timeline = incident_data.get('timeline', [])
    
    for item in timeline:
        ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(item.get('time', 0)))
        t_data.append([
            ts_str,
            item.get('event', '-'),
            item.get('actor', '-'),
            Paragraph(item.get('details', '-'), styles['Normal']) # Wrap text
        ])
    
    if len(timeline) == 0:
        t_data.append(["-", "NO EVENTS RECORDED", "-", "-"])
        
    tl_table = Table(t_data, colWidths=[100, 120, 100, 160])
    tl_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(tl_table)

    # 5. Footer & Legal Disclaimer
    story.append(Spacer(1, 40))
    disclaimer = ("This is an automatically generated incident report by PRAHARI-AI. "
                  "The data contained herein is cryptographically hashed and stored on the "
                  "decentralized Sentinel ledger for legal evidentiary purposes.")
    story.append(Paragraph(f"<font size='8'>{disclaimer}</font>", styles['Italic']))

    doc.build(story)
    buffer.seek(0)
    return buffer
