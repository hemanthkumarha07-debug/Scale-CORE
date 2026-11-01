from django.urls import path
from .views import AIOperationsWorkspaceView, AIQueryAPIView

app_name = 'intelligence'

urlpatterns = [
    path('', AIOperationsWorkspaceView.as_view(), name='workspace'),
    path('api/query/', AIQueryAPIView.as_view(), name='api-query'),
]
