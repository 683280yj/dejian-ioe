"""官网预约入口；只接受带服务端密钥的官网代理请求。"""
import hmac
import json
import re
from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inventory.models import BookingLead


@csrf_exempt
@never_cache
@require_POST
def submit_booking(request):
    expected = settings.BOOKING_SUBMISSION_TOKEN
    supplied = request.headers.get('X-Booking-Token', '')
    if not expected or not hmac.compare_digest(supplied, expected):
        return JsonResponse({'message': '不可提交预约'}, status=403)
    if len(request.body) > 4096:
        return JsonResponse({'message': '提交内容过长'}, status=413)
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'message': '提交格式有误'}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({'message': '提交格式有误'}, status=400)
    if data.get('website'):
        return JsonResponse({'message': '预约已收到'})
    phone = str(data.get('phone', '')).strip()
    category = str(data.get('category', '')).strip()
    if not re.fullmatch(r'1[3-9]\d{9}', phone):
        return JsonResponse({'message': '请输入有效的手机号'}, status=400)
    if not 2 <= len(category) <= 80 or data.get('consent') is not True:
        return JsonResponse({'message': '请填写经营品类并同意预约联系'}, status=400)
    recent = timezone.now() - timedelta(minutes=5)
    if not BookingLead.objects.filter(phone=phone, created_at__gte=recent).exists():
        BookingLead.objects.create(phone=phone, category=category)
    return JsonResponse({'message': '预约已收到'})
