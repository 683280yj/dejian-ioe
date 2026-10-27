from django.urls import path

from . import views

app_name = 'ai_assist'
urlpatterns = [
    path('restock/<int:pk>/adopt/', views.restock_adopt, name='restock_adopt'),
    path('suggestions/<int:pk>/adopt/', views.restock_adopt, name='suggestion_adopt'),  # lane-b 模板约定名
    path('restock/<int:pk>/dismiss/', views.restock_dismiss, name='restock_dismiss'),
    path('refresh/', views.refresh, name='refresh'),
    path('assistant/chat/', views.assistant_chat, name='assistant_chat'),
]
