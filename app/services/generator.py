import os
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Circle, Rect, Group

class CertificateGenerator:
    """
    Renders high-quality, professional vector PDF certificates using ReportLab.
    Standardized on A4 Landscape with an elegant border, gold seal, and clear typography.
    """

    @staticmethod
    def generate_pdf(
        output_path: Path,
        recipient_name: str,
        event_name: str,
        certificate_title: str,
        issuer_name: str,
        issue_date: str,
        certificate_number: str
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # A4 Landscape: width 841.89 pt, height 595.27 pt
        width, height = landscape(A4)
        
        c = canvas.Canvas(str(output_path), pagesize=landscape(A4))
        c.setTitle(f"{certificate_title} - {recipient_name}")
        c.setAuthor(issuer_name)
        c.setSubject(event_name)

        # -------------------------------------------------------------
        # 1. Background & Decorative Borders
        # -------------------------------------------------------------
        # Soft off-white / parchment background
        c.setFillColor(colors.HexColor("#FCFDFD"))
        c.rect(0, 0, width, height, fill=1, stroke=0)

        # Outer navy border
        c.setStrokeColor(colors.HexColor("#0F2942"))
        c.setLineWidth(5)
        c.rect(20, 20, width - 40, height - 40, fill=0, stroke=1)

        # Inner thin gold border
        c.setStrokeColor(colors.HexColor("#D4AF37"))  # Gold
        c.setLineWidth(1.5)
        c.rect(28, 28, width - 56, height - 56, fill=0, stroke=1)

        # Subtle secondary frame
        c.setStrokeColor(colors.HexColor("#E2D3A8"))
        c.setLineWidth(0.75)
        c.rect(32, 32, width - 64, height - 64, fill=0, stroke=1)

        # Decorative Corner Accents (Gold geometric triangles)
        c.setFillColor(colors.HexColor("#D4AF37"))
        # Top-left corner
        p = c.beginPath()
        p.moveTo(28, height - 28)
        p.lineTo(48, height - 28)
        p.lineTo(28, height - 48)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # Top-right corner
        p = c.beginPath()
        p.moveTo(width - 28, height - 28)
        p.lineTo(width - 48, height - 28)
        p.lineTo(width - 28, height - 48)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # Bottom-left corner
        p = c.beginPath()
        p.moveTo(28, 28)
        p.lineTo(48, 28)
        p.lineTo(28, 48)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # Bottom-right corner
        p = c.beginPath()
        p.moveTo(width - 28, 28)
        p.lineTo(width - 48, 28)
        p.lineTo(width - 28, 48)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # -------------------------------------------------------------
        # 2. Header & Organization
        # -------------------------------------------------------------
        center_x = width / 2.0

        # Issuing Organization Header
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(colors.HexColor("#556B82"))
        c.drawCentredString(center_x, height - 85, issuer_name.upper())

        # Thin accent line below issuer
        c.setStrokeColor(colors.HexColor("#D4AF37"))
        c.setLineWidth(1)
        c.line(center_x - 70, height - 95, center_x + 70, height - 95)

        # -------------------------------------------------------------
        # 3. Certificate Title
        # -------------------------------------------------------------
        c.setFont("Times-Bold", 28)
        c.setFillColor(colors.HexColor("#0F2942"))
        c.drawCentredString(center_x, height - 145, certificate_title.upper())

        # "THIS IS PROUDLY PRESENTED TO"
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawCentredString(center_x, height - 180, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

        # -------------------------------------------------------------
        # 4. Recipient Name
        # -------------------------------------------------------------
        c.setFont("Times-BoldItalic", 34)
        c.setFillColor(colors.HexColor("#1A365D"))
        c.drawCentredString(center_x, height - 235, recipient_name)

        # Recipient Name underline
        name_width = min(c.stringWidth(recipient_name, "Times-BoldItalic", 34) + 40, width - 180)
        c.setStrokeColor(colors.HexColor("#D4AF37"))
        c.setLineWidth(1.5)
        c.line(center_x - (name_width / 2.0), height - 247, center_x + (name_width / 2.0), height - 247)

        # -------------------------------------------------------------
        # 5. Course / Event Description
        # -------------------------------------------------------------
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor("#475569"))
        c.drawCentredString(center_x, height - 285, "for successfully completing and demonstrating excellence in")

        # Event Name in bold
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor("#0F2942"))
        c.drawCentredString(center_x, height - 320, event_name)

        # -------------------------------------------------------------
        # 6. Decorative Gold Seal Badge (Left-Center)
        # -------------------------------------------------------------
        seal_x = 135
        seal_y = 115
        
        # Outer scalloped / gold circle
        c.setFillColor(colors.HexColor("#D4AF37"))
        c.circle(seal_x, seal_y, 36, fill=1, stroke=0)
        # Inner dark navy circle
        c.setFillColor(colors.HexColor("#0F2942"))
        c.circle(seal_x, seal_y, 30, fill=1, stroke=0)
        # Inner gold ring
        c.setStrokeColor(colors.HexColor("#F6E05E"))
        c.setLineWidth(1)
        c.circle(seal_x, seal_y, 27, fill=0, stroke=1)
        # Star or Seal text
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.HexColor("#FFFFFF"))
        c.drawCentredString(seal_x, seal_y + 4, "OFFICIAL")
        c.drawCentredString(seal_x, seal_y - 6, "SEAL")

        # -------------------------------------------------------------
        # 7. Date & Signature Lines
        # -------------------------------------------------------------
        # Date block (Center-Right)
        date_x = center_x
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor("#1E293B"))
        c.drawCentredString(date_x, 120, str(issue_date))
        c.setStrokeColor(colors.HexColor("#94A3B8"))
        c.setLineWidth(1)
        c.line(date_x - 65, 110, date_x + 65, 110)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawCentredString(date_x, 95, "DATE OF ISSUANCE")

        # Authorized Signatory (Right)
        sig_x = width - 150
        c.setFont("Times-Italic", 15)
        c.setFillColor(colors.HexColor("#0F2942"))
        c.drawCentredString(sig_x, 122, issuer_name)
        c.setStrokeColor(colors.HexColor("#94A3B8"))
        c.setLineWidth(1)
        c.line(sig_x - 75, 110, sig_x + 75, 110)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawCentredString(sig_x, 95, "AUTHORIZED SIGNATURE")

        # -------------------------------------------------------------
        # 8. Certificate ID / Verification Footer
        # -------------------------------------------------------------
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#94A3B8"))
        c.drawString(45, 42, f"Certificate ID: {certificate_number}")
        c.drawRightString(width - 45, 42, "Authenticity verified by issuer")

        # Save & finalize PDF
        c.showPage()
        c.save()
        
        return output_path
