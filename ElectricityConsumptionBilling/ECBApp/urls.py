from django.urls import path
from . import views
from .views import usage_history, initiate_payment, payment_success, payment_failed, view_bill
urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('usage-history/', usage_history, name='usage_history'),
    path('payment/<int:bill_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/<int:bill_id>/', payment_success, name='payment_success'),
    path('payment-failed/', payment_failed, name='payment_failed'),
    path('view-bill/', views.view_bill, name='view_bill'),
]
