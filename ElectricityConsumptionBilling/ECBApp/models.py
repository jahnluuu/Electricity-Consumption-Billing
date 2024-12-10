from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, datetime, timedelta
from django.db.models import Sum
import datetime

class Customer(AbstractUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Profile(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Tariff(models.Model):
    tariffID = models.AutoField(primary_key=True)
    effectiveDate = models.DateField()
    ratePerKwh = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        for bill in Bill.objects.all():
            if bill.tariff == self:
                total_consumption = Consumption.objects.filter(customer=bill.customer).aggregate(
                    total=models.Sum('totalConsumption'))['total']
                if total_consumption:
                    bill.totalAmount = total_consumption * self.ratePerKwh
                    bill.save()

    def __str__(self):
        return f"Tariff {self.tariffID} - Rate: {self.ratePerKwh}"


class Consumption(models.Model):
    consumptionID = models.AutoField(primary_key=True)
    readingDateFrom = models.DateField()
    readingDateTo = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    totalConsumption = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Save the Consumption first
        super().save(*args, **kwargs)
       

    def __str__(self):
        return f"Consumption {self.consumptionID} for {self.customer.first_name} {self.customer.last_name}"

class Bill(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
    ]

    billID = models.AutoField(primary_key=True)
    billDate = models.DateField()
    totalAmount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dueDate = models.DateField(default=date.today)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    
    def get_paid_amount(self):
        total_paid = self.payment_set.aggregate(Sum('amountPaid'))['amountPaid__sum'] or 0
        
        return total_paid
    
    def save(self, *args, **kwargs):
        if self.totalAmount == 0:
            self.status = 'Paid'
        elif self.dueDate < date.today():
            self.status = 'Overdue'
        else:
            self.status = 'Pending'
        super().save(*args, **kwargs)
    
class BillingDetails(models.Model):
    consumption = models.ForeignKey(Consumption, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    billDate = models.DateField(default=datetime.date.today)
    totalAmount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dueDate = models.DateField(default=date.today)
    tariffRatePerKwh = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=Bill.STATUS_CHOICES, default='Pending')
    readingDateFrom = models.DateField(default=datetime.date.today)
    readingDateTo = models.DateField(default=datetime.date.today)
    totalConsumption = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"BillingDetails for {self.bill.customer.first_name} {self.bill.customer.last_name} - {self.billDate}"

class Payment(models.Model):
    paymentID = models.AutoField(primary_key=True)
    paymentDate = models.DateField()
    amountPaid = models.DecimalField(max_digits=10, decimal_places=2)
    paymentMethod = models.CharField(max_length=50)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    note = models.TextField(blank=True, null=True)

@receiver(post_save, sender=Customer)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

@receiver(post_save, sender=Consumption)
def create_or_update_bill(sender, instance, created, **kwargs):
    if created:
        tariff = Tariff.objects.latest('effectiveDate') 
        total_amount = instance.totalConsumption * tariff.ratePerKwh

        bill = Bill.objects.create(
            customer=instance.customer,
            billDate=instance.readingDateTo, 
            totalAmount=total_amount, 
            dueDate=instance.readingDateTo + timedelta(days=30), 
            tariff=tariff  
        )

        BillingDetails.objects.create(
            consumption=instance,
            bill=bill,
            billDate=bill.billDate,
            totalAmount=bill.totalAmount,
            dueDate=bill.dueDate,
            tariffRatePerKwh=tariff.ratePerKwh,
            status=bill.status,
            readingDateFrom=instance.readingDateFrom,
            readingDateTo=instance.readingDateTo,
            totalConsumption=instance.totalConsumption
        )

        print(f"Created Bill with due date: {bill.dueDate}")
        print(f"Created BillingDetails for {bill.customer.first_name} {bill.customer.last_name}")

    else:
        print(f"Updating an existing bill for {instance.customer}")
        try:
            bill = Bill.objects.get(customer=instance.customer, billDate=instance.readingDateTo)
            tariff = bill.tariff 
            total_amount = instance.totalConsumption * tariff.ratePerKwh 
            print(f"Updated Total Amount: {total_amount}")
            bill.totalAmount = total_amount
            bill.save()  

            billing_details = BillingDetails.objects.get(bill=bill)
            billing_details.totalAmount = bill.totalAmount
            billing_details.tariffRatePerKwh = tariff.ratePerKwh
            billing_details.totalConsumption = instance.totalConsumption
            billing_details.save()

        except Bill.DoesNotExist:
            print("No Bill found, creating a new one")
            tariff = Tariff.objects.latest('effectiveDate') 
            total_amount = instance.totalConsumption * tariff.ratePerKwh
            bill = Bill.objects.create(
                customer=instance.customer,
                billDate=instance.readingDateTo,
                totalAmount=total_amount,
                dueDate=instance.readingDateTo + timedelta(days=30), 
                tariff=tariff
            )

            BillingDetails.objects.create(
                consumption=instance,
                bill=bill,
                billDate=bill.billDate,
                totalAmount=bill.totalAmount,
                dueDate=bill.dueDate,
                tariffRatePerKwh=tariff.ratePerKwh,
                status=bill.status,
                readingDateFrom=instance.readingDateFrom,
                readingDateTo=instance.readingDateTo,
                totalConsumption=instance.totalConsumption
            )
            print(f"Created Bill with due date: {bill.dueDate}")

@receiver(post_save, sender=Payment)
def update_bill_status_on_payment(sender, instance, **kwargs):
    bill = instance.bill
    total_paid = Payment.objects.filter(bill=bill).aggregate(total=Sum('amountPaid'))['total'] or 0

    if total_paid >= bill.totalAmount:  
        bill.status = 'Paid'
        bill.totalAmount = 0 
    else:
        bill.status = 'Pending'
    
    bill.save()
            
