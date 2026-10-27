"""只读访客：体验实例里指定账号只能查看，任何写操作都被拦下。

在 settings 里设 READONLY_USERNAMES = ['chouce_guest'] 并把本中间件放在
AuthenticationMiddleware 与 MessageMiddleware 之后即可启用；列表为空时不生效。
"""
import re

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

# 访客允许的 POST：登录/退出/一键进入/切换语言
_ALLOWED_POST = ('/accounts/login/', '/accounts/logout/', '/enter/', '/i18n/setlang/')
# 访客禁止的 GET：后台、系统维护（备份下载等），以及用 GET 触发状态变更的 IOE 原有链接
_BLOCKED_GET = re.compile(
    r'^/(admin|system)/'
    r'|/(delete|start|complete|approve|cancel|adopt|dismiss|clear|restore)/'
    r'|^/tenancy/import/'
)
MESSAGE = '访客账号仅可查看，不能修改数据。'


class ReadOnlyGuestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.usernames = set(getattr(settings, 'READONLY_USERNAMES', []) or [])

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if self.usernames and user is not None and user.is_authenticated and user.get_username() in self.usernames:
            path = request.path
            unsafe = request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE')
            if (unsafe and not path.startswith(_ALLOWED_POST)) or (not unsafe and _BLOCKED_GET.search(path)):
                return self._reject(request)
        return self.get_response(request)

    def _reject(self, request):
        wants_html = 'text/html' in request.headers.get('Accept', '') and \
            request.headers.get('X-Requested-With') != 'XMLHttpRequest'
        if not wants_html:
            return HttpResponseForbidden(MESSAGE)
        messages.warning(request, MESSAGE)
        back = request.headers.get('Referer') or '/'
        if not url_has_allowed_host_and_scheme(back, allowed_hosts={request.get_host()}) or (request.method == 'GET' and back.split('?')[0].endswith(request.path)):
            back = '/'
        return redirect(back)
