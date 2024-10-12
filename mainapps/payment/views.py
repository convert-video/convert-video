# payment/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.hashers import make_password
from mainapps.accounts.models import User

@csrf_exempt
@require_POST  # Chỉ cho phép POST requests
def checkout_session_stripe(request):
    # Lấy thông tin từ request body (bao gồm cả các loại dữ liệu như JSON)
    try:
        payload = json.loads(request.body.decode('utf-8'))

    except UnicodeDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid encoding'}, status=400)

    user_email = payload['data']['object']['customer_details']['email']
    user_name = payload['data']['object']['customer_details']['name']

    try:
        user, created = User.objects.get_or_create(
            email=user_email,
            defaults={'username': user_email, 'first_name': user_name}
        )
        # print(f"User {user} created")
        if created:
            random_password = generate_random_password()
            hashed_password = make_password(random_password)
            user.password = hashed_password
            user.save()

            # Bạn có thể gửi mật khẩu qua email cho người dùng tại đây nếu cần
            print(f"New user created with email: {user_email} and password: {random_password}")

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # Trả về dữ liệu thô dưới dạng JSON
    return JsonResponse({
        'status': 'success',
        'raw_data': data
    })


def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + "!@#$%^&*()-_+="
    return ''.join(random.choice(characters) for _ in range(length))
