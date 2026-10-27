from django.urls import path

from . import views

app_name = 'b2b'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/new/', views.customer_form, name='customer_create'),
    path('customers/<int:pk>/edit/', views.customer_form, name='customer_edit'),
    path('purchase-orders/', views.po_list, name='po_list'),
    path('purchase-orders/new/', views.po_create, name='po_create'),
    path('purchase-orders/<int:pk>/', views.po_detail, name='po_detail'),
    path('purchase-orders/<int:pk>/<slug:action>/', views.po_transition, name='po_transition'),
    path('wholesale-orders/', views.so_list, name='so_list'),
    path('wholesale-orders/new/', views.so_create, name='so_create'),
    path('wholesale-orders/<int:pk>/', views.so_detail, name='so_detail'),
    path('wholesale-orders/<int:pk>/<slug:action>/', views.so_transition, name='so_transition'),
    path('statements/', views.statement_list, name='statement_list'),
    path('statements/new/', views.statement_create, name='statement_create'),
    path('statements/<int:pk>/', views.statement_detail, name='statement_detail'),
    path('statements/<int:pk>/<slug:decision>/', views.statement_decide, name='statement_decide'),
    path('payables/', views.payable_list, name='payable_list'),
    path('payables/<int:pk>/pay/', views.payable_pay, name='payable_pay'),
    path('receivables/', views.receivable_list, name='receivable_list'),
    path('receivables/<int:pk>/collect/', views.receivable_collect, name='receivable_collect'),
]
