import fitz  # PyMuPDF
from PIL import Image
import io

class PDFBackend:
    def __init__(self):
        self.doc = None
        self.page = None
        self.display_scale = 1.5 

    def load_pdf(self, path):
        self.doc = fitz.open(path)
        self.page = self.doc[0] 
        pix = self.page.get_pixmap(matrix=fitz.Matrix(self.display_scale, self.display_scale))
        mode = "RGBA" if pix.alpha else "RGB"
        return Image.frombytes(mode, [pix.width, pix.height], pix.samples)

    def load_image(self, path):
        return Image.open(path).convert("RGBA")

    def resize_image(self, pil_image, scale_factor):
        """Resizes a specific PIL image."""
        if not pil_image: return None
        w = int(pil_image.width * scale_factor)
        h = int(pil_image.height * scale_factor)
        try: resample = Image.Resampling.LANCZOS
        except AttributeError: resample = Image.LANCZOS
        return pil_image.resize((w, h), resample)

    def save_pdf(self, save_path, elements):
        """
        elements: List of dicts.
        Each dict has: type, x, y, and specific data (scale/image OR content/font/color)
        """
        if not self.doc: return False

        for el in elements:
            # Convert Screen Coords -> PDF Points
            # We add logic to flip Y if needed, but usually PDF (0,0) is top-left in PyMuPDF
            pdf_x = el['x'] / self.display_scale
            pdf_y = el['y'] / self.display_scale

            if el['type'] == 'image':
                # Re-calculate size from original for high quality
                original = el['original_pil']
                scale = el['scale']
                
                screen_w = int(original.width * scale)
                screen_h = int(original.height * scale)
                pdf_w = screen_w / self.display_scale
                pdf_h = screen_h / self.display_scale
                
                rect = fitz.Rect(pdf_x, pdf_y, pdf_x + pdf_w, pdf_y + pdf_h)
                
                # Get bytes
                try: resample = Image.Resampling.LANCZOS
                except AttributeError: resample = Image.LANCZOS
                resized = original.resize((screen_w, screen_h), resample)
                
                img_buffer = io.BytesIO()
                resized.save(img_buffer, format="PNG")
                self.page.insert_image(rect, stream=img_buffer.getvalue(), overlay=True)

            elif el['type'] == 'text':
                # Convert font size
                pdf_fontsize = el['fontsize'] # Approximation
                
                # Insert text
                self.page.insert_text(
                    (pdf_x, pdf_y), 
                    el['content'], 
                    fontsize=pdf_fontsize, 
                    fontname="helv", # Standard Helvetica
                    color=el['color']
                )

        self.doc.save(save_path)
        return True