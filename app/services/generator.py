import os
import math
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import qrcode

from app.config import settings

# Color Palette (Elegant Academic/Executive)
NAVY_PRIMARY = (15, 23, 42)       # #0F172A
GOLD_ACCENT = (197, 160, 89)      # #C5A059
GOLD_LIGHT = (235, 214, 162)      # #EBD6A2
CHARCOAL_TEXT = (51, 65, 85)      # #334155
MUTED_TEXT = (100, 116, 139)      # #64748B
BG_IVORY = (252, 250, 247)        # #FCFAF7
WHITE = (255, 255, 255)
SEAL_RED = (180, 40, 40)


def _get_font(font_names: list, size: int) -> ImageFont.ImageFont:
    """Attempt to load one of the preferred fonts, falling back gracefully."""
    font_dirs = [
        "C:/Windows/Fonts",
        "/usr/share/fonts",
        "/usr/share/fonts/truetype",
        "/usr/local/share/fonts",
        "~/.fonts"
    ]
    for name in font_names:
        # Check standard paths
        for fdir in font_dirs:
            full_path = os.path.join(os.path.expanduser(fdir), name)
            if os.path.exists(full_path):
                try:
                    return ImageFont.truetype(full_path, size=size)
                except Exception:
                    pass
        # Try loading by raw name via PIL system search
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            pass
    # Fallback to default
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.ImageFont,
    color: tuple,
    canvas_width: int
) -> int:
    """Draw text centered horizontally and return the bottom y coordinate."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (canvas_width - text_width) // 2
    draw.text((x, y), text, font=font, fill=color)
    return y + text_height


def _fit_font_size(
    text: str,
    max_width: int,
    start_size: int,
    font_names: list,
    min_size: int = 24
) -> ImageFont.ImageFont:
    """Scale font down so text fits within max_width."""
    size = start_size
    temp_img = Image.new("RGBA", (10, 10))
    temp_draw = ImageDraw.Draw(temp_img)
    
    while size > min_size:
        font = _get_font(font_names, size)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            return font
        size -= 4
    return _get_font(font_names, min_size)


def _draw_ornate_borders(draw: ImageDraw.ImageDraw, width: int, height: int):
    """Draw decorative double border with corner accents."""
    # Outer dark border
    draw.rectangle([40, 40, width - 40, height - 40], outline=NAVY_PRIMARY, width=6)
    
    # Inner gold border
    draw.rectangle([55, 55, width - 55, height - 55], outline=GOLD_ACCENT, width=2)
    
    # Second inner subtle border
    draw.rectangle([65, 65, width - 65, height - 65], outline=GOLD_LIGHT, width=1)
    
    # Corner ornaments
    corner_size = 40
    corners = [
        (55, 55),
        (width - 55, 55),
        (55, height - 55),
        (width - 55, height - 55)
    ]
    for cx, cy in corners:
        # Draw small decorative squares in corners
        draw.rectangle([cx - 8, cy - 8, cx + 8, cy + 8], fill=GOLD_ACCENT, outline=NAVY_PRIMARY, width=2)


def _draw_gold_seal(img: Image.Image, center_x: int, center_y: int, radius: int = 70):
    """Draw an elegant official gold seal badge."""
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Starburst teeth around seal
    points = 32
    outer_r = radius + 12
    inner_r = radius
    pts = []
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else inner_r
        angle = i * (math.pi / points)
        px = center_x + int(r * math.cos(angle))
        py = center_y + int(r * math.sin(angle))
        pts.append((px, py))
    draw.polygon(pts, fill=GOLD_LIGHT, outline=GOLD_ACCENT)
    
    # Inner circles
    draw.ellipse([center_x - radius, center_y - radius, center_x + radius, center_y + radius], fill=GOLD_ACCENT)
    inner_circle_r = radius - 10
    draw.ellipse(
        [center_x - inner_circle_r, center_y - inner_circle_r, center_x + inner_circle_r, center_y + inner_circle_r],
        fill=BG_IVORY, outline=NAVY_PRIMARY, width=2
    )
    
    # Center text
    font_seal = _get_font(["arialbd.ttf", "arial.ttf"], 14)
    bbox = draw.textbbox((0, 0), "OFFICIAL", font=font_seal)
    draw.text((center_x - (bbox[2] - bbox[0]) // 2, center_y - 20), "OFFICIAL", font=font_seal, fill=NAVY_PRIMARY)
    
    bbox2 = draw.textbbox((0, 0), "VERIFIED", font=font_seal)
    draw.text((center_x - (bbox2[2] - bbox2[0]) // 2, center_y), "VERIFIED", font=font_seal, fill=NAVY_PRIMARY)
    
    bbox3 = draw.textbbox((0, 0), "SEAL", font=font_seal)
    draw.text((center_x - (bbox3[2] - bbox3[0]) // 2, center_y + 16), "SEAL", font=font_seal, fill=GOLD_ACCENT)

    # Composite onto main image
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))


def _generate_qr_code(data_url: str, size: int = 140) -> Image.Image:
    """Generate a clean QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=1,
    )
    qr.add_data(data_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=NAVY_PRIMARY, back_color=WHITE).convert("RGBA")
    return qr_img.resize((size, size), Image.Resampling.LANCZOS)


class CertificateGenerator:
    """High-resolution Certificate generation service."""

    WIDTH = 2000
    HEIGHT = 1414

    @classmethod
    def generate_certificate(
        cls,
        recipient_name: str,
        event_name: str,
        title: str = "Certificate of Achievement",
        issuer_name: str = "AEREO Engineering Team",
        issue_date: str = "",
        certificate_code: str = "",
        output_dir: Optional[Path] = None
    ) -> Tuple[str, str]:
        """
        Generates both PNG and PDF certificates.
        Returns (png_path, pdf_path).
        """
        if not output_dir:
            output_dir = settings.CERTIFICATES_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        if not issue_date:
            issue_date = datetime.utcnow().strftime("%B %d, %Y")
        else:
            try:
                dt = datetime.strptime(issue_date, "%Y-%m-%d")
                issue_date = dt.strftime("%B %d, %Y")
            except Exception:
                pass

        # Create canvas
        image = Image.new("RGB", (cls.WIDTH, cls.HEIGHT), BG_IVORY)
        draw = ImageDraw.Draw(image)

        # 1. Ornate Borders & Corners
        _draw_ornate_borders(draw, cls.WIDTH, cls.HEIGHT)

        # 2. Header banner / Issuer brand
        font_issuer_top = _get_font(["georgiab.ttf", "arialbd.ttf"], 26)
        _draw_centered_text(draw, issuer_name.upper(), 130, font_issuer_top, GOLD_ACCENT, cls.WIDTH)
        
        # Subtle horizontal divider line under issuer
        line_len = 300
        line_x1 = (cls.WIDTH - line_len) // 2
        line_x2 = line_x1 + line_len
        draw.line([line_x1, 175, line_x2, 175], fill=GOLD_ACCENT, width=2)

        # 3. Certificate Title
        font_title = _get_font(["georgiab.ttf", "timesbd.ttf", "arialbd.ttf"], 62)
        _draw_centered_text(draw, title.upper(), 220, font_title, NAVY_PRIMARY, cls.WIDTH)

        # 4. Presentation Subtitle
        font_subtitle = _get_font(["georgiai.ttf", "timesi.ttf"], 30)
        _draw_centered_text(draw, "THIS CERTIFICATE IS PROUDLY PRESENTED TO", 335, font_subtitle, MUTED_TEXT, cls.WIDTH)

        # 5. Recipient Name (Fitted to avoid overflow)
        font_name = _fit_font_size(
            recipient_name,
            max_width=cls.WIDTH - 400,
            start_size=78,
            font_names=["georgiab.ttf", "timesbd.ttf", "arialbd.ttf"]
        )
        name_bottom_y = _draw_centered_text(draw, recipient_name, 420, font_name, NAVY_PRIMARY, cls.WIDTH)

        # Decorative ribbon under recipient name
        underline_w = 700
        ux1 = (cls.WIDTH - underline_w) // 2
        ux2 = ux1 + underline_w
        draw.line([ux1, name_bottom_y + 25, ux2, name_bottom_y + 25], fill=GOLD_ACCENT, width=3)
        draw.ellipse([ux1 - 5, name_bottom_y + 22, ux1 + 5, name_bottom_y + 28], fill=GOLD_ACCENT)
        draw.ellipse([ux2 - 5, name_bottom_y + 22, ux2 + 5, name_bottom_y + 28], fill=GOLD_ACCENT)

        # 6. Description statement
        font_body = _get_font(["georgia.ttf", "times.ttf"], 28)
        _draw_centered_text(
            draw,
            "for successfully completing and demonstrating excellence in",
            name_bottom_y + 65,
            font_body,
            CHARCOAL_TEXT,
            cls.WIDTH
        )

        # 7. Event / Course Name
        font_event = _fit_font_size(
            event_name,
            max_width=cls.WIDTH - 500,
            start_size=48,
            font_names=["georgiab.ttf", "arialbd.ttf"]
        )
        _draw_centered_text(draw, event_name, name_bottom_y + 130, font_event, NAVY_PRIMARY, cls.WIDTH)

        # 8. Bottom Section (Date, Seal, Signature)
        # Left: Issue Date
        font_meta_label = _get_font(["arialbd.ttf", "georgiab.ttf"], 20)
        font_meta_value = _get_font(["georgia.ttf", "arial.ttf"], 22)
        
        date_x = 240
        date_y = cls.HEIGHT - 320
        draw.line([date_x - 50, date_y + 40, date_x + 250, date_y + 40], fill=CHARCOAL_TEXT, width=1)
        draw.text((date_x - 30, date_y + 10), issue_date, font=font_meta_value, fill=CHARCOAL_TEXT)
        draw.text((date_x + 30, date_y + 50), "DATE OF ISSUANCE", font=font_meta_label, fill=MUTED_TEXT)

        # Center: Official Seal Badge
        _draw_gold_seal(image, cls.WIDTH // 2, cls.HEIGHT - 280, radius=72)
        draw = ImageDraw.Draw(image)  # Re-acquire draw after seal composite

        # Right: Authorized Signature
        sig_line_w = 340
        sig_x2 = cls.WIDTH - 180
        sig_x1 = sig_x2 - sig_line_w
        sig_y = cls.HEIGHT - 320
        draw.line([sig_x1, sig_y + 40, sig_x2, sig_y + 40], fill=CHARCOAL_TEXT, width=1)
        
        # Center signature text over line
        font_signature = _get_font(["georgiai.ttf", "timesi.ttf"], 32)
        sig_bbox = draw.textbbox((0, 0), issuer_name, font=font_signature)
        sig_text_w = sig_bbox[2] - sig_bbox[0]
        sig_text_x = sig_x1 + (sig_line_w - sig_text_w) // 2
        draw.text((sig_text_x, sig_y + 0), issuer_name, font=font_signature, fill=NAVY_PRIMARY)
        
        lbl_bbox = draw.textbbox((0, 0), "AUTHORIZED SIGNATURE", font=font_meta_label)
        lbl_w = lbl_bbox[2] - lbl_bbox[0]
        lbl_x = sig_x1 + (sig_line_w - lbl_w) // 2
        draw.text((lbl_x, sig_y + 50), "AUTHORIZED SIGNATURE", font=font_meta_label, fill=MUTED_TEXT)

        # 9. Verification QR Code & Certificate ID in footer
        verification_url = f"{settings.BASE_URL}/api/v1/certificates/verify/{certificate_code}"
        qr_size = 110
        qr_img = _generate_qr_code(verification_url, size=qr_size)
        qr_pos = (cls.WIDTH - 190, cls.HEIGHT - 190)
        image.paste(qr_img, qr_pos)

        # Footer Text
        font_cert_id = _get_font(["arialbd.ttf"], 18)
        font_cert_sub = _get_font(["arial.ttf"], 14)
        footer_y = cls.HEIGHT - 120
        draw.text((100, footer_y), f"CERTIFICATE ID: {certificate_code}", font=font_cert_id, fill=NAVY_PRIMARY)
        draw.text((100, footer_y + 26), f"Verify Authenticity at: {verification_url}", font=font_cert_sub, fill=MUTED_TEXT)

        # Save files
        file_stem = f"{certificate_code}"
        png_path = output_dir / f"{file_stem}.png"
        pdf_path = output_dir / f"{file_stem}.pdf"

        # Save High-Res PNG
        image.save(str(png_path), "PNG", dpi=(300, 300))

        # Save PDF directly from image
        image.save(str(pdf_path), "PDF", resolution=300.0)

        return str(png_path), str(pdf_path)
