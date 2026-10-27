from django.urls import path

from . import views

app_name = 'tenancy'
urlpatterns = [
    path('', views.overview, name='overview'),
    path('switch/', views.switch, name='switch'),
    path('branding/', views.branding, name='branding'),
    path('import/', views.data_import, name='import'),
    path('import/template/<str:kind>.<str:fmt>', views.import_template, name='import_template'),
    path('import/sample/<str:kind>.<str:fmt>', views.import_sample, name='import_sample'),
]
