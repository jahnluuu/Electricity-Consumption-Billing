from django.contrib import admin
from .models import Customer, Tariff, Consumption, Bill, BillingDetails, Payment, Profile

class BillAdmin(admin.ModelAdmin):
    search_fields = ['customer__username', 'billID']
    list_filter = ['billDate', 'dueDate']
    list_display = ('billID', 'customer', 'totalAmount', 'dueDate')

admin.site.register(Customer)
admin.site.register(Profile)
admin.site.register(Tariff)
admin.site.register(Consumption)
admin.site.register(Bill, BillAdmin)
admin.site.register(BillingDetails)
admin.site.register(Payment)
