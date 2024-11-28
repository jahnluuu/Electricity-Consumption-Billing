from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .forms import CustomerRegistrationForm, ProfileForm, CustomerPasswordUpdateForm
from .models import Customer, Profile, Tariff, Consumption, Bill, Payment, BillingDetails
from decimal import Decimal
from datetime import date
import json
import stripe

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

@login_required
def dashboard(request):

    return render(request, 'ECBApp/dashboard.html')

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

# @login_required
# def payment_history(request):
#     payments = Payment.objects.filter(bill__customer=request.user)
#     context = {'payments': payments}
#     return render(request, 'payment_history.html', context)

# @login_required
# def usage_history(request):
#     bills = Bill.objects.filter(customer=request.user).order_by('-billDate')
#     month = request.GET.get('month')
#     year = request.GET.get('year')

#     if month and year:
#         bills = bills.filter(billDate__year=year, billDate__month=month)
#     elif year:
#         bills = bills.filter(billDate__year=year)

#     return render(request, 'ECBApp/usage_history.html', {'bills': bills})

@login_required
def initiate_payment(request, bill_id):
    bill = get_object_or_404(Bill, billID=bill_id, customer=request.user)

    if bill.status == 'Paid':
        messages.error(request, 'This bill is already paid.')
        return redirect('view_bill')

    if request.method == 'POST':
        amount_paid = Decimal(request.POST.get('amount_paid', '0.0'))
        payment_method = request.POST.get('payment_method', '')
        payment_note = request.POST.get('payment_note', '')

        if amount_paid <= 0 or amount_paid > (bill.totalAmount - bill.get_paid_amount()):
            messages.error(request, 'Invalid payment amount.')
            return render(request, 'ECBApp/initiate_payment.html', {'bill': bill})

        Payment.objects.create(
            bill=bill,
            amountPaid=amount_paid,
            paymentDate=date.today(),
            paymentMethod=payment_method,
            **({'note': payment_note} if hasattr(Payment, 'note') else {})
        )

        total_paid = Payment.objects.filter(bill=bill).aggregate(total=Sum('amountPaid'))['total'] or Decimal('0.0')
        if total_paid >= bill.totalAmount:
            bill.status = 'Paid'
        else:
            bill.status = 'Pending'
        bill.save()

        messages.success(request, 'Payment successful!')
        return redirect('view_bill')

    return render(request, 'ECBApp/initiate_payment.html', {'bill': bill})


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
        bill.status = 'Paid'  
        bill.save()

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
    bills = Bill.objects.filter(customer=request.user)
    payments = Payment.objects.filter(bill__customer=request.user)

    pending_and_overdue_bills = bills.filter(status__in=['Pending', 'Overdue'])
    total_pending = pending_and_overdue_bills.aggregate(total=Sum('totalAmount'))['total'] or Decimal('0.0')

    total_paid = payments.aggregate(total=Sum('amountPaid'))['total'] or Decimal('0.0')
    overdue_bills = bills.filter(dueDate__lt=date.today(), status="Overdue").count()

    monthly_payments = payments.annotate(month=TruncMonth('paymentDate')).values('month').annotate(
        total=Sum('amountPaid')
    ).order_by('month')

    months = [entry['month'].strftime('%b %Y') for entry in monthly_payments]
    payment_totals = [float(entry['total']) for entry in monthly_payments]

    payment_analysis = {
        'done': float(total_paid),  
        'pending': float(total_pending),
    }

    return render(request, 'ECBApp/view_bill.html', {
        'bills': bills,
        'total_due': total_pending,
        'total_paid': total_paid,
        'overdue_bills': overdue_bills,
        'payment_analysis': json.dumps(payment_analysis),
        'months': months,
        'payment_totals': payment_totals,
    })