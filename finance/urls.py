from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.finance_dashboard, name='finance_dashboard'),
    path('admin/transactions/', views.finance_transactions, name='finance_transactions'),
    path('admin/credit/', views.finance_credit_account, name='finance_credit_account'),
    path('admin/credit/<int:user_id>/', views.finance_credit_account, name='finance_credit_account_user'),
    path('admin/pilot/<int:user_id>/', views.finance_pilot_detail, name='finance_pilot_detail'),
]
