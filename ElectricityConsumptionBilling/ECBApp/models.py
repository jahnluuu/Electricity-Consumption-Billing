from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

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

@receiver(post_save, sender=Customer)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

class Tariff(models.Model):
    tariffID = models.AutoField(primary_key=True)
    effectiveDate = models.DateField()
    ratePerKwh = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Tariff {self.tariffID} - Rate: {self.ratePerKwh}"

class Consumption(models.Model):
    consumptionID = models.AutoField(primary_key=True)
    readingDateFrom = models.DateField()
    readingDateTo = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    totalConsumption = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class Bill(models.Model):
    billID = models.AutoField(primary_key=True)
    billDate = models.DateField()
    totalAmount = models.DecimalField(max_digits=10, decimal_places=2)
    dueDate = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE)

class BillingDetails(models.Model):
    consumption = models.ForeignKey(Consumption, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)

class Payment(models.Model):
    paymentID = models.AutoField(primary_key=True)
    paymentDate = models.DateField()
    amountPaid = models.DecimalField(max_digits=10, decimal_places=2)
    paymentMethod = models.CharField(max_length=50)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
