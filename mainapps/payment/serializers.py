from rest_framework import serializers
from .models import UserSubscription

class UserSubscriptionSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = ['id', 'name', 'subscription_type', 'amount_allowed_usage', 'amount_used_usage', 'total']

    def get_total(self, obj):
        return obj.amount_allowed_usage - obj.amount_used_usage
