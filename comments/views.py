from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from django.db import transaction
from django.utils import timezone

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from rest_framework import filters, generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment, CommentAttachment
from .serializers import CommentSerializer


class CommentPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = None


class CommentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Comment.objects.filter(parent__isnull=True)

    serializer_class = CommentSerializer
    pagination_class = CommentPagination

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['user_name', 'email', 'created_at']
    ordering = ['-created_at', '-id']

    def perform_create(self, serializer):
        captcha_key = serializer.validated_data.pop('captcha_key')
        captcha_value = serializer.validated_data.pop('captcha_value')

        with transaction.atomic():
            captcha = (
                CaptchaStore.objects
                .select_for_update()
                .filter(
                    hashkey=captcha_key,
                    expiration__gt=timezone.now()
                )
                .first()
            )

            if (
                not captcha
                or captcha.response.lower() != captcha_value.lower()
            ):
                raise ValidationError({
                    'captcha': (
                        'Невірна CAPTCHA або термін її дії закінчився. '
                        'Неверная CAPTCHA или срок её действия истёк. '
                        'Invalid or expired CAPTCHA.'
                    )
                })

            serializer.save()
            captcha.delete()


class CaptchaAPIView(APIView):
    def get(self, request):
        captcha_key = CaptchaStore.generate_key()
        image_url = captcha_image_url(captcha_key)

        return Response({
            'captcha_key': captcha_key,
            'captcha_image': request.build_absolute_uri(image_url),
        })


@require_GET
def view_txt_attachment(request, comment_id):
    attachment = get_object_or_404(
        CommentAttachment,
        comment_id=comment_id
    )

    if not attachment.file or not attachment.file.name.lower().endswith('.txt'):
        raise Http404('TXT attachment not found')

    with attachment.file.open('rb') as file:
        content = file.read(100 * 1024 + 1)

    if len(content) > 100 * 1024:
        return HttpResponse('TXT file too large', status=413)

    return HttpResponse(
        content,
        content_type='text/plain; charset=utf-8'
    )
