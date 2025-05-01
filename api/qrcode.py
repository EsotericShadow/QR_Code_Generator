from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer, RoundedModuleDrawer, CircleModuleDrawer,
    VerticalBarsDrawer, HorizontalBarsDrawer
)
from qrcode.image.styles.colormasks import (
    SolidFillColorMask, RadialGradiantColorMask, SquareGradiantColorMask,
    HorizontalGradiantColorMask, VerticalGradiantColorMask
)
from PIL import Image, UnidentifiedImageError
import io, base64
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Helper to convert hex to RGB tuple
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    elif len(hex_color) == 3:
        return tuple(int(hex_color[i]*2, 16) for i in (0, 1, 2))
    return (0, 0, 0) # Default to black if invalid

@app.route("/api/qrcode", methods=["POST"])
def gen_qr():
    try:
        data = request.get_json()
        if not data:
            abort(400, description="Invalid JSON payload")

        url = data.get("url", "")
        if not url:
             abort(400, description="URL parameter is required")

        # Customization parameters
        module_shape = data.get("moduleShape", "square")
        color_mode = data.get("colorMode", "solid")
        back_color_hex = data.get("backColor", "#FFFFFF")
        logo_data = data.get("logo") # base64 data URL

        # Convert background color
        back_color_rgb = hex_to_rgb(back_color_hex)

        # Select Module Drawer
        if module_shape == "rounded":
            module_drawer = RoundedModuleDrawer()
        elif module_shape == "circle":
            module_drawer = CircleModuleDrawer()
        elif module_shape == "vertical":
            module_drawer = VerticalBarsDrawer()
        elif module_shape == "horizontal":
            module_drawer = HorizontalBarsDrawer()
        else: # Default to square
            module_drawer = SquareModuleDrawer()

        # Select Color Mask
        if color_mode == "gradient":
            gradient_type = data.get("gradientType", "radial")
            grad_color1_hex = data.get("gradientColor1", "#000000")
            grad_color2_hex = data.get("gradientColor2", "#FFFFFF")
            grad_color1_rgb = hex_to_rgb(grad_color1_hex)
            grad_color2_rgb = hex_to_rgb(grad_color2_hex)

            if gradient_type == "radial":
                color_mask = RadialGradiantColorMask(back_color=back_color_rgb, center_color=grad_color1_rgb, edge_color=grad_color2_rgb)
            elif gradient_type == "square":
                color_mask = SquareGradiantColorMask(back_color=back_color_rgb, center_color=grad_color1_rgb, edge_color=grad_color2_rgb)
            elif gradient_type == "horizontal":
                color_mask = HorizontalGradiantColorMask(back_color=back_color_rgb, left_color=grad_color1_rgb, right_color=grad_color2_rgb)
            elif gradient_type == "vertical":
                color_mask = VerticalGradiantColorMask(back_color=back_color_rgb, top_color=grad_color1_rgb, bottom_color=grad_color2_rgb)
            else: # Default to radial
                color_mask = RadialGradiantColorMask(back_color=back_color_rgb, center_color=grad_color1_rgb, edge_color=grad_color2_rgb)
        else: # Default to solid
            fill_color_hex = data.get("fillColor", "#000000")
            fill_color_rgb = hex_to_rgb(fill_color_hex)
            color_mask = SolidFillColorMask(back_color=back_color_rgb, front_color=fill_color_rgb)

        # 1) Generate base QR using StyledPilImage
        qr = qrcode.QRCode(
            # version=None, # Let library choose based on data
            error_correction=qrcode.constants.ERROR_CORRECT_H, # High error correction for styling
            box_size=10,
            border=4
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            color_mask=color_mask
            # eye_drawer can be added here later if needed
        ).convert("RGB") # Convert to RGB for consistency

        # 2) If there's a logo, decode & paste
        if logo_data and isinstance(logo_data, str) and logo_data.startswith("data:image"): # Basic validation
            try:
                header, b64 = logo_data.split(",", 1)
                logo_bytes = base64.b64decode(b64)
                logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

                # Scale logo (ensure high quality resampling)
                w, h = img.size
                logo_size = int(w * 0.25) # Adjust size as needed
                # Use Resampling.LANCZOS if available (Pillow >= 9.1.0), else ANTIALIAS
                resample_method = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS
                logo = logo.resize((logo_size, logo_size), resample_method)

                # Calculate position
                pos = ((w - logo_size) // 2, (h - logo_size) // 2)

                # Paste using logo's alpha channel as mask
                img.paste(logo, pos, logo)
            except (ValueError, base64.binascii.Error, UnidentifiedImageError) as e:
                print(f"Logo processing error: {e}") # Log error, but continue without logo
                pass # Optionally, could abort or return a warning

        # 3) Send back as base64 data URL
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode()
        return jsonify({"image": f"data:image/png;base64,{encoded}"})

    except Exception as e:
        print(f"Error generating QR code: {e}") # Log the exception
        # Return a generic error message
        return jsonify({"error": "An unexpected error occurred while generating the QR code."}), 500

# Error handler for bad requests
@app.errorhandler(400)
def handle_bad_request(e):
    response = e.get_response()
    response.data = jsonify({"error": e.description}).data
    response.content_type = "application/json"
    return response

# Note: For Vercel deployment, the Flask app object needs to be named 'app'.

