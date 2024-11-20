from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomerRegistrationForm, ProfileForm, CustomerPasswordUpdateForm
from django.contrib.auth import update_session_auth_hash
from .models import Customer, Profile, Tariff, Consumption, Bill, Payment, BillingDetails
from django.db.models import Sum
from django.db.models.functions import TruncMonth
import json
from decimal import Decimal
import stripe
from django.conf import settings
from datetime import date


stripe.api_key = settings.STRIPE_SECRET_KEY
def register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomerRegistrationForm()
    return render(request, 'ECBApp/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'ECBApp/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

import json
from decimal import Decimal

@login_required
def dashboard(request):
    bills = Bill.objects.filter(customer=request.user)
    payments = Payment.objects.filter(bill__customer=request.user)

    # Summaries
    total_consumption = bills.aggregate(total=Sum('totalAmount'))['total'] or Decimal('0.0')
    total_paid = payments.aggregate(total=Sum('amountPaid'))['total'] or Decimal('0.0')
    total_due = total_consumption - total_paid
    overdue_bills = bills.filter(dueDate__lt=date.today(), status="Overdue").count()

    # Data for Line Chart
    monthly_payments = payments.annotate(month=TruncMonth('paymentDate')).values('month').annotate(
        total=Sum('amountPaid')
    ).order_by('month')

    months = [entry['month'].strftime('%b %Y') for entry in monthly_payments]
    payment_totals = [float(entry['total']) for entry in monthly_payments]

    # Pie Chart Data (Convert Decimal to float)
    payment_analysis = {
        'done': float(total_paid),  # Convert to float
        'pending': float(total_due),  # Convert to float
    }

    context = {
        'bills': bills,
        'payments': payments,
        'total_due': float(total_due),  # Convert to float
        'total_paid': float(total_paid),  # Convert to float
        'overdue_bills': overdue_bills,
        'months': json.dumps(months),
        'payment_totals': json.dumps(payment_totals),
        'payment_analysis': json.dumps(payment_analysis),
    }
    return render(request, 'ECBApp/dashboard.html', context)

@login_required
def profile(request):
    customer = request.user
    profile, created = Profile.objects.get_or_create(user=customer)
    return render(request, 'ECBApp/profile.html', {'customer': customer, 'profile': profile})

@login_required
def update_profile(request):
    customer = request.user
    profile, created = Profile.objects.get_or_create(user=customer)

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=customer)
        password_form = CustomerPasswordUpdateForm(request.POST)  

        if profile_form.is_valid():
            profile_form.save()  

            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            if new_password1 or new_password2:
                if password_form.is_valid():
                    customer.set_password(password_form.cleaned_data['new_password1'])
                    customer.save()
                    update_session_auth_hash(request, customer) 
                    messages.success(request, "Profile and password updated successfully.")
                else:
                    messages.error(request, "Password update failed. Please check the fields.")
            else:
                messages.success(request, "Profile updated successfully without changing password.")

            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        profile_form = ProfileForm(instance=customer)
        password_form = CustomerPasswordUpdateForm() 

    return render(
        request,
        'ECBApp/update_profile.html',
        {
            'profile_form': profile_form,
            'password_form': password_form
        }
    )

@login_required
def payment_history(request):
    payments = Payment.objects.filter(bill__customer=request.user)
    context = {'payments': payments}
    return render(request, 'payment_history.html', context)

@login_required
def usage_history(request):
    bills = Bill.objects.filter(customer=request.user).order_by('-billDate')
    month = request.GET.get('month')
    year = request.GET.get('year')

    if month and year:
        bills = bills.filter(billDate__year=year, billDate__month=month)
    elif year:
        bills = bills.filter(billDate__year=year)

    return render(request, 'ECBApp/usage_history.html', {'bills': bills})

@login_required
def initiate_payment(request, bill_id):
    bill = Bill.objects.get(id=bill_id, customer=request.user)
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"Bill {bill.billDate}"
                },
                'unit_amount': int(bill.totalAmount * 100),  # Stripe requires cents
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f"{settings.SITE_URL}/payment_success/{bill.billID}",
        cancel_url=f"{settings.SITE_URL}/payment_failed/",
    )
    return redirect(session.url, code=303)

@login_required
def payment_success(request, bill_id):
    try:
        bill = Bill.objects.get(id=bill_id, customer=request.user)
        Payment.objects.create(
            bill=bill,
            paymentDate=date.today(),
            amountPaid=bill.totalAmount,
            paymentMethod="Stripe"
        )
        bill.totalAmount = 0  # Clear the amount due
        bill.status = 'Paid'  # Update the status
        bill.save()  # Save the changes

        messages.success(request, "Payment successful!")
    except Bill.DoesNotExist:
        messages.error(request, "The bill does not exist or is not associated with your account.")
    return redirect('dashboard')

@login_required
def payment_failed(request):
    messages.error(request, "Payment failed. Please try again.")
    return redirect('dashboard')
@login_required
def view_bill(request):
    print(request.user)  # Check if the user is correct
    user_consumption = Consumption.objects.filter(customer=request.user)
    print(user_consumption) 

    billing_details = BillingDetails.objects.select_related('bill', 'consumption').filter(consumption__customer=request.user)
    print(billing_details)

    context = {
        'bills_and_consumptions': billing_details
    }

    return render(request, 'ECBApp/view_bill.html', context)