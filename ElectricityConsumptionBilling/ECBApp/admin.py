from django.contrib import admin
from .models import Customer, Tariff, Consumption, Bill, BillingDetails, Payment, Profile

admin.site.index_title = "Welcome to the Electricity Consumption Billing Admin"

class ConsumptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'readingDateFrom', 'readingDateTo', 'totalConsumption')
    
class BillAdmin(admin.ModelAdmin):
    list_display = ('billID', 'customer', 'tariff', 'totalAmount', 'dueDate')
    search_fields = ['customer__username', 'billID']
    list_filter = ['billDate', 'dueDate', 'tariff']
    fields = ('customer', 'tariff', 'totalAmount', 'dueDate')  

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('bill', 'amountPaid', 'paymentDate', 'paymentMethod')
    search_fields = ['bill__billID', 'bill__customer__username']
    list_filter = ['paymentDate', 'paymentMethod']
    fields = ('bill', 'amountPaid', 'paymentDate', 'paymentMethod')
    ordering = ['-paymentDate']

class BillingDetailsAdmin(admin.ModelAdmin):
    list_display = ['bill', 'billID', 'totalAmount', 'dueDate', 'status', 'readingDateFrom', 'readingDateTo', 'totalConsumption']

    def billID(self, obj):
        return obj.bill.billID 

admin.site.register(Customer)
admin.site.register(Profile)
admin.site.register(Tariff)
admin.site.register(Consumption, ConsumptionAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(BillingDetails, BillingDetailsAdmin)
admin.site.register(Payment, PaymentAdmin)

