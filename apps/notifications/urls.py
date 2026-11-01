from django.urls import path
from .views import NotificationHubView, AcknowledgeNotificationView

app_name = 'notifications'

urlpatterns = [
    path('', NotificationHubView.as_view(), name='hub'),
    path('<uuid:pk>/ack/', AcknowledgeNotificationView.as_view(), name='ack'),
]
