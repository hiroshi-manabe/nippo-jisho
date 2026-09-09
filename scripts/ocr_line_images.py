"""Pixel preparation for already-isolated/rectified OCR lines."""
from PIL import Image, ImageOps


def prepare_rectified_line(image, *, height=48, max_width=4096):
    """Preserve the complete polygon extent; never trim from ink density.

    A dark-paper polygon surrounded by white pixels can exceed a rule detector's
    dark-pixel threshold across most columns. Treating those columns as rules
    silently drops text. Isolation already supplied the desired line extent.
    """
    line=ImageOps.autocontrast(image.convert('L'),cutoff=0.2)
    width=max(1,round(line.width*height/line.height))
    if max_width:
        width=min(max_width,width)
    return line.resize((width,height),Image.Resampling.LANCZOS)
