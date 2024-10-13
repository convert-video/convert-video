from django.contrib import admin
from .models import *
# Register your models here.
# admin.site.register(User)
admin.site.register(Credit)
admin.site.register(SubscriptionPlan)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [field.name for field in User._meta.fields]
    list_filter = ('is_active', 'is_staff')  # Example of filtering options
    search_fields = ('username', 'email')  # Add search functionality
    ordering = ('id',)
