from django.contrib import admin
from .models import Customer, Tariff, Consumption, Bill, BillingDetails, Payment, Profile

admin.site.site_header = "Electricity Consumption Billing Admin"
admin.site.site_title = "Electricity Consumption Billing Admin"
admin.site.index_title = "Welcome to the Electricity Consumption Billing System"

class ConsumptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'readingDateFrom', 'readingDateTo', 'totalConsumption')

class BillingDetailsInline(admin.TabularInline):
    model = BillingDetails
    extra = 1  # Number of empty rows to display
    fields = ('detailDescription', 'amount')

class BillAdmin(admin.ModelAdmin):
    list_display = ('billID', 'customer', 'tariff', 'totalAmount', 'dueDate')
    search_fields = ['customer__username', 'billID']
    list_filter = ['billDate', 'dueDate', 'tariff']
    fields = ('customer', 'tariff', 'totalAmount', 'dueDate') 
    inlines = [BillingDetailsInline]
    readonly_fields = ('billID',)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('bill', 'amountPaid', 'paymentDate', 'paymentMethod')
    search_fields = ['bill__billID', 'bill__customer__username']
    list_filter = ['paymentDate', 'paymentMethod']
    fields = ('bill', 'amountPaid', 'paymentDate', 'paymentMethod')
    ordering = ['-paymentDate']
    list_per_page = 20

admin.site.register(Customer)
admin.site.register(Profile)
admin.site.register(Tariff)
admin.site.register(Consumption, ConsumptionAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(BillingDetails)
admin.site.register(Payment, PaymentAdmin)

