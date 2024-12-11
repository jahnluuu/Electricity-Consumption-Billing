from django.urls import path
from . import views
from .views import initiate_payment, payment_success, payment_failed, view_billing_details
urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),

    path('view-bill/payment/<int:bill_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/<int:bill_id>/', payment_success, name='payment_success'),
    path('payment-failed/', payment_failed, name='payment_failed'),
    path('view-bill/', views.view_bill, name='view_bill'),
    path('view-billing-details/', views.view_billing_details, name='view_billing_details'),  
]
