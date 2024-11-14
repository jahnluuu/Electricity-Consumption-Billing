from django.contrib import admin
from .models import Customer, Tariff, Consumption, Bill, BillingDetails, Payment

admin.site.register(Customer)
admin.site.register(Tariff)
admin.site.register(Consumption)
admin.site.register(Bill)
admin.site.register(BillingDetails)
admin.site.register(Payment)
