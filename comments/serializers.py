import re

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .file_utils import process_attachment
from .html_utils import validate_comment_html
from .models import Comment, CommentAttachment


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    attachment = serializers.FileField(
        write_only=True,
        required=False,
        allow_null=True
    )

    attachment_url = serializers.SerializerMethodField()

    captcha_key = serializers.CharField(write_only=True)
    captcha_value = serializers.CharField(write_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'user_name',
            'email',
            'home_page',
            'text',
            'created_at',
            'parent',
            'replies',
            'attachment',
            'attachment_url',
            'captcha_key',
            'captcha_value',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_user_name(self, value):
        if not re.fullmatch(r'[A-Za-z0-9]+', value):
            raise serializers.ValidationError(
                'Ім’я користувача повинно містити лише латинські літери та цифри. '
                'Имя пользователя должно содержать только латинские буквы и цифры. '
                'Username must contain only Latin letters and numbers.'
            )
        return value

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                'Коментар не може бути порожнім. '
                'Комментарий не может быть пустым. '
                'Comment cannot be empty.'
            )

        try:
            return validate_comment_html(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_attachment(self, value):
        if value is None:
            return None

        try:
            return process_attachment(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def create(self, validated_data):
        attachment = validated_data.pop('attachment', None)

        comment = Comment.objects.create(**validated_data)

        if attachment is not None:
            CommentAttachment.objects.create(
                comment=comment,
                file=attachment
            )

        return comment

    def get_attachment_url(self, obj):
        try:
            attachment = obj.attachment
        except CommentAttachment.DoesNotExist:
            return None

        if not attachment.file:
            return None

        request = self.context.get('request')
        url = attachment.file.url

        if request:
            return request.build_absolute_uri(url)

        return url

    def get_replies(self, obj):
        children = obj.replies.all()

        return CommentSerializer(
            children,
            many=True,
            context=self.context
        ).data

    """перенесём проверку CAPTCHA в comments/views.py, 
    чтобы она выполнялась непосредственно перед сохранением
    комментария."""

    # def validate(self, attrs):
    #     if self.instance is not None:
    #         return attrs

    #     captcha_key = attrs.pop('captcha_key')
    #     captcha_value = attrs.pop('captcha_value')

    #     with transaction.atomic():
    #         captcha = (
    #             CaptchaStore.objects
    #             .select_for_update()
    #             .filter(
    #                 hashkey=captcha_key,
    #                 expiration__gt=timezone.now()
    #             )
    #             .first()
    #         )

    #         if not captcha or captcha.response.lower() != captcha_value.lower():
    #             raise serializers.ValidationError({
    #                 'captcha': (
    #                     'Неверная или просроченная CAPTCHA. '
    #                     'Invalid or expired CAPTCHA.'
    #                 )
    #             })

    #         captcha.delete()

    #     return attrs

    """ Убрал из класс при подключению файлов к загрузке комментариев, 
    так как проверка CAPTCHA теперь выполняется в comments/views.py. """

    # def validate(self, attrs):
    #     if self.instance is not None:
    #         return attrs

    #     return attrs
