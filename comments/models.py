from django.db import models

# Create your models here.


class Comment(models.Model):
    user_name = models.CharField(max_length=100)
    email = models.EmailField()
    home_page = models.URLField(blank=True)
    text = models.TextField()
    # По умолчанию новые комментарии должны отображаться первыми — LIFO (Last In, First Out)
    created_at = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Комментарий (Comment)'
        verbose_name_plural = 'Комментарии (Comments)'

    def __str__(self):
        return f'{self.user_name}: {self.text[:50]}'


class CommentAttachment(models.Model):
    comment = models.OneToOneField(
        Comment,
        on_delete=models.CASCADE,
        related_name='attachment'
    )

    file = models.FileField(
        upload_to='comment_attachments/'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Вложение (Attachment)'
        verbose_name_plural = 'Вложения (Attachments)'

    def __str__(self):
        return f'Attachment for comment {self.comment_id}'
