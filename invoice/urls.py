from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:id>', views.view_invoice, name='view_invoice'),
    path('add/', views.add, name='add'),
    path('edit/<int:id>/', views.edit, name='edit'),
    path('delete/<int:id>/', views.delete, name='delete'),
    path('list_invoice/', views.list_invoice, name='list_invoice'),
    path('invoices/filter/', views.filter_invoices, name='filter_invoices'),
    path('upload-pdf/', views.upload_pdf_ajax_process, name='upload_pdf_ajax_process'),
]
