from django.contrib import admin
from .models import Comment

# Register your models here.


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_name',
        'email',
        'created_at',
        'parent',
    )
    list_filter = ('created_at',)
    search_fields = ('user_name', 'email', 'text')
    ordering = ('-created_at',)
    list_per_page = 25
