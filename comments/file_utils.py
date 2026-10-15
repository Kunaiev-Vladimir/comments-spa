from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError


MAX_IMAGE_SIZE = (320, 240)
MAX_TXT_SIZE = 100 * 1024
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

ALLOWED_IMAGES = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.gif': 'GIF',
}


def process_attachment(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()

    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            'Файл завеликий. Максимальний розмір — 10 МБ. '
            'Файл слишком большой. Максимальный размер — 10 МБ. '
            'File is too large. Maximum size is 10 MB.'
        )

    if extension == '.txt':
        if uploaded_file.size > MAX_TXT_SIZE:
            raise ValidationError(
                'TXT-файл не може перевищувати 100 КБ. '
                'TXT-файл не должен превышать 100 КБ. '
                'TXT file must not exceed 100 KB.'
            )

        try:
            uploaded_file.seek(0)
            uploaded_file.read().decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValidationError(
                'TXT-файл повинен мати кодування UTF-8. '
                'TXT-файл должен иметь кодировку UTF-8. '
                'TXT file must use UTF-8 encoding.'
            ) from exc
        finally:
            uploaded_file.seek(0)

        return uploaded_file

    if extension not in ALLOWED_IMAGES:
        raise ValidationError(
            'Дозволені лише JPG, JPEG, PNG, GIF і TXT. '
            'Разрешены только JPG, JPEG, PNG, GIF и TXT. '
            'Only JPG, JPEG, PNG, GIF and TXT are allowed.'
        )

    try:
        uploaded_file.seek(0)

        with Image.open(uploaded_file) as image:
            image.verify()

        uploaded_file.seek(0)

        with Image.open(uploaded_file) as image:
            if image.format != ALLOWED_IMAGES[extension]:
                raise ValidationError(
                    'Формат зображення не відповідає розширенню. '
                    'Формат изображения не соответствует расширению. '
                    'Image format does not match its extension.'
                )

            if image.format == 'GIF':
                if image.width <= 320 and image.height <= 240:
                    uploaded_file.seek(0)
                    return uploaded_file

                frames = []
                durations = []

                for frame in ImageSequence.Iterator(image):
                    resized = frame.convert('RGBA')
                    resized.thumbnail(
                        MAX_IMAGE_SIZE,
                        Image.Resampling.LANCZOS
                    )

                    frames.append(resized)
                    durations.append(frame.info.get('duration', 100))

                output = BytesIO()

                frames[0].save(
                    output,
                    format='GIF',
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=image.info.get('loop', 0),
                    disposal=2,
                    optimize=False,
                )

                return ContentFile(
                    output.getvalue(),
                    name=uploaded_file.name,
                )

            image = ImageOps.exif_transpose(image)

            if image.width <= 320 and image.height <= 240:
                uploaded_file.seek(0)
                return uploaded_file

            image.thumbnail(
                MAX_IMAGE_SIZE,
                Image.Resampling.LANCZOS
            )

            if image.format == 'JPEG':
                image = image.convert('RGB')

            output = BytesIO()

            image.save(
                output,
                format=ALLOWED_IMAGES[extension],
            )

            return ContentFile(
                output.getvalue(),
                name=uploaded_file.name,
            )

    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError(
            'Некоректний файл зображення. '
            'Некорректный файл изображения. '
            'Invalid image file.'
        ) from exc

    finally:
        uploaded_file.seek(0)
