from pathlib import Path

from cloudinary_storage.storage import MediaCloudinaryStorage


class CommentCloudinaryStorage(MediaCloudinaryStorage):
    """
    Хранение вложений комментариев в Cloudinary.

    JPG, PNG, GIF -> image
    TXT           -> raw
    """

    def _get_resource_type(self, name):
        extension = Path(name).suffix.lower()

        if extension == '.txt':
            return 'raw'

        return 'image'
