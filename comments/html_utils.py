from urllib.parse import urlsplit
from xml.etree.ElementTree import ParseError

from defusedxml import ElementTree


ALLOWED_TAGS = {'a', 'code', 'i', 'strong'}
ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title'},
    'code': set(),
    'i': set(),
    'strong': set(),
}


def validate_comment_html(text):
    try:
        root = ElementTree.fromstring(
            f'<root>{text}</root>'
        )
    except (ParseError, ValueError) as exc:
        raise ValueError(
            'Некорректный HTML или незакрытые теги. '
            'Invalid HTML or unclosed tags.'
        ) from exc

    for element in root.iter():
        if element is root:
            continue

        if element.tag not in ALLOWED_TAGS:
            raise ValueError(
                'Недопустимый HTML-тег. '
                'HTML tag is not allowed.'
            )

        allowed_attrs = ALLOWED_ATTRIBUTES[element.tag]

        for attr in element.attrib:
            if attr not in allowed_attrs:
                raise ValueError(
                    'Недопустимый HTML-атрибут. '
                    'HTML attribute is not allowed.'
                )

        if element.tag == 'a':
            href = element.get('href', '')
            parsed_url = urlsplit(href)

            if (
                parsed_url.scheme.lower() not in {'http', 'https'}
                or not parsed_url.netloc
            ):
                raise ValueError(
                    'Разрешены только HTTP и HTTPS ссылки. '
                    'Only HTTP and HTTPS links are allowed.'
                )

    return text
