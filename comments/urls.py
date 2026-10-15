from django.urls import path
from .views import CommentListCreateAPIView, CaptchaAPIView

app_name = 'comments'

urlpatterns = [
    path('', CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('captcha/', CaptchaAPIView.as_view(), name='captcha'),
]
