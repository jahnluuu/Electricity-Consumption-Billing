from django.contrib import admin
from .models import Customer, Tariff, Consumption, Bill, BillingDetails, Payment, Profile

class ConsumptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'readingDateFrom', 'readingDateTo', 'totalConsumption')

class BillAdmin(admin.ModelAdmin):
    list_display = ('billID', 'customer', 'tariff', 'totalAmount', 'dueDate')
    search_fields = ['customer__username', 'billID']
    list_filter = ['billDate', 'dueDate', 'tariff']
    fields = ('customer', 'tariff', 'totalAmount', 'dueDate')  

admin.site.register(Customer)
admin.site.register(Profile)
admin.site.register(Tariff)
admin.site.register(Consumption, ConsumptionAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(BillingDetails)
admin.site.register(Payment)
