from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Comment


@receiver(post_save, sender=Comment)
def notify_comment_created(sender, instance, created, **kwargs):
    if not created:
        return

    comment_id = instance.id

    def send_notification():
        channel_layer = get_channel_layer()

        if channel_layer is None:
            return

        async_to_sync(channel_layer.group_send)(
            'comments_updates',
            {
                'type': 'comment_created',
                'comment_id': comment_id,
            },
        )

    transaction.on_commit(send_notification)
