from io import BytesIO
from pathlib import Path

from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from django.db.models.fields.files import ImageFieldFile
from PIL import Image, UnidentifiedImageError


class BadFormatException(Exception):
    def __init__(self):
        message = "The format of the image is not accepted. You should upload a '.png', '.jpg', '.jpeg' or '.webp' image."
        super().__init__(message)


def process_image(
    image_source: Path | str | BytesIO | UploadedFile | ImageFieldFile,
    *,
    name: str,
    max_width: int | None = None,
    max_height: int | None = None,
) -> InMemoryUploadedFile:
    """feature
    :name: process_image
    :description: Ouvre une image depuis un fichier ou des bytes, la convertit en .webp, et optionnellement génère plusieurs tailles.
    :param image_source: Fichier (path-like, UploadedFile) ou bytes-like object.
    :param name: Nom de base du fichier sans extension (si None, dérivé du nom source).
    :param max_width: Largeur maximum, peut provoquer un downsize.
    :param max_height: Hauteur maximum, peut provoquer un downsize.
    :returns: InMemoryUploadedFile
    :raises: BadFormatException
    """
    try:
        if isinstance(image_source, (bytes, bytearray)):
            image = Image.open(BytesIO(image_source))
        elif isinstance(image_source, (UploadedFile, ImageFieldFile)):
            image = Image.open(image_source)
        elif hasattr(image_source, "read"):
            image = Image.open(image_source)
        elif isinstance(image_source, (str, Path)):
            path = Path(image_source)
            with path.open("rb") as f:
                image = Image.open(f)
        else:
            raise TypeError(f"Unsupported image_source type: {type(image_source)}")
    except UnidentifiedImageError:
        raise BadFormatException

    image_format = image.format.upper()

    if image_format not in ["PNG", "JPG", "JPEG", "WEBP"]:
        raise BadFormatException

    width, height = image.size
    scale = 1.0
    if max_width and width > max_width:
        scale = min(scale, max_width / width)
    if max_height and height > max_height:
        scale = min(scale, max_height / height)
    if scale < 1.0:
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    image_buffer = BytesIO()
    image.save(image_buffer, format="WEBP")
    image_buffer.seek(0)

    uploaded_file = InMemoryUploadedFile(
        image_buffer,
        None,
        f"{name}.webp",
        "image/webp",
        image_buffer.getbuffer().nbytes,
        None,
    )

    return uploaded_file
