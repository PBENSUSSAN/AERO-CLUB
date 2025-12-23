from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('documents/', views.documents_view, name='documents'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    path('api/documents/', views.document_status_api, name='document_status_api'),
    # QR Code
    path('qrcode/', views.member_qrcode, name='member_qrcode'),
    path('card/', views.member_card, name='member_card'),
    path('api/scan/<int:member_id>/', views.scan_member, name='scan_member'),
]
