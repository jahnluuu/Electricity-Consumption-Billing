from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomerRegistrationForm, ProfileForm, CustomerPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import Bill, Profile

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
    bills = Bill.objects.filter(customer=request.user)
    return render(request, 'ECBApp/dashboard.html', {'bills': bills})

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
        password_form = CustomerPasswordChangeForm(user=customer, data=request.POST)

        if profile_form.is_valid():
            profile_form.save()  # Save profile details (including first name, last name, and email)
            
            if request.POST.get('new_password1') or request.POST.get('new_password2'):  # Check if password fields are filled
                if password_form.is_valid():
                    password_form.save()  # Save the updated password
                    update_session_auth_hash(request, customer)  # Keeps the user logged in after password change
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
        password_form = CustomerPasswordChangeForm(user=customer)

    return render(
        request,
        'ECBApp/update_profile.html',
        {
            'profile_form': profile_form,
            'password_form': password_form
        }
    )
