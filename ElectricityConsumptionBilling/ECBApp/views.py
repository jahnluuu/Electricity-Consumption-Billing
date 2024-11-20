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

@login_required
def dashboard(request):
    # Fetch Bills and Payments for the logged-in user
    bills = Bill.objects.filter(customer=request.user)
    payments = Payment.objects.filter(bill__customer=request.user)

    # Aggregate total consumption and total amount
    billing_details = BillingDetails.objects.filter(consumption__customer=request.user)
    total_consumption = billing_details.aggregate(
        total_consumption=Sum('consumption__totalConsumption')
    )['total_consumption']
    total_amount = bills.aggregate(total_amount=Sum('totalAmount'))['total_amount'] or 0

    # Monthly Payment Data for Line Graph
    monthly_payments = (
        payments.annotate(month=TruncMonth('paymentDate'))
        .values('month')
        .annotate(total=Sum('amountPaid'))
        .order_by('month')
    )

    # Prepare data for the graph
    months = [entry['month'].strftime('%b %Y') for entry in monthly_payments]
    
    # Convert Decimal to float in payment_totals to avoid JSON serialization issues
    payment_totals = [float(entry['total']) for entry in monthly_payments]

    # Payment Analysis for Pie Chart
    payment_analysis = {
        "done": float(payments.aggregate(done=Sum('amountPaid'))['done'] or 0),
        "pending": float(bills.aggregate(pending=Sum('totalAmount'))['pending'] or 0),
    }

    # Pass data to the template
    context = {
        'bills': bills,
        'payments': payments,
        'total_consumption': total_consumption,
        'total_amount': total_amount,
        'months': json.dumps(months),
        'payment_totals': json.dumps(payment_totals),  # This will now be serializable
        'payment_analysis': json.dumps(payment_analysis),  # This will now be serializable
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