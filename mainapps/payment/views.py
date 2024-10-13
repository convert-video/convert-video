# payment/views.py

from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from mainapps.accounts.models import User
from converterapp import settings

import json
import requests
import logging

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
@csrf_exempt
@require_POST
def checkout_session_stripe(request):
    payload = json.loads(request.body.decode("utf-8"))
    logging.debug(f"[COMMAND LOGGING DATA]: {payload}")
    
    redirect_url = settings.REDIRECT_URL
    default_password = settings.USER_DEFAULT_PASSWORD

    if (
        payload.get("type") == "checkout.session.completed"
        and payload["data"]["object"].get("status") == "complete"
    ):
        user_email = payload["data"]["object"]["customer_details"]["email"]
        user_name = payload["data"]["object"]["customer_details"]["name"]

        try:
            hashed_password = make_password(default_password)

            user, created = User.objects.get_or_create(
                email=user_email,
                defaults={
                    "username": user_email,
                    "first_name": user_name,
                    "email": user_email,
                    "password": hashed_password,
                    "is_superuser": 0,
                },
            )
            if created:
                user.password = hashed_password
                user.save()
                
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "success"})

