from django.contrib import admin

from mainapps.payment.models import UserSubscription

# Register your models here.
from .models import UserSubscription

class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'expiration_at', 'amount_allowed_usage', 'amount_used_usage', 'created_at', 'updated_at')
    search_fields = ('user__username', 'subscription_id', 'name')
    list_filter = ('status', 'subscription_type')

admin.site.register(UserSubscription, UserSubscriptionAdmin)