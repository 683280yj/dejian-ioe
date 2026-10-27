"""默认中文：忽略浏览器 Accept-Language，只有用户在界面上手动切换（会话/cookie）才改语言。"""


class IgnoreAcceptLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META.pop('HTTP_ACCEPT_LANGUAGE', None)
        return self.get_response(request)
