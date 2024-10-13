from django.db import models
from mainapps.accounts.models import User


# class UserPayment(models.Model):
#     app_user = models.ForeignKey(User, on_delete=models.CASCADE)
#     payment_bool = models.BooleanField(default=False)
#     stripe_checkout_id = models.CharField(max_length=500)


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ("COMPLETED", "COMPLETED"),
        ("INACTIVE", "INACTIVE"),
        ("ACTIVE", "ACTIVE"),
        ("CANCELED", "CANCELED"),
        ("TRIAL", "TRIAL"),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    expiration_at = models.DateTimeField()
    subscription_id = models.CharField(max_length=36)
    subscription_type = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    payment_info = models.TextField(null=True, blank=True)
    amount_allowed_usage = models.IntegerField()
    amount_used_usage = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_subscriptions"
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"

    def __str__(self):
        return self.name
