"""体验环境免密进入：DEJIAN_OPEN_ACCESS 开启时一键以指定账号登录。"""
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods


def open_access_enabled():
    return bool(getattr(settings, 'DEJIAN_OPEN_ACCESS', False))


def open_access_username():
    return getattr(settings, 'DEJIAN_OPEN_ACCESS_USER', 'dj_boss') or 'dj_boss'


@require_http_methods(['GET', 'POST'])
def enter(request):
    """GET：已登录则进首页；开启免密时返回自动提交的 CSRF 表单。POST：免密登录。"""
    if not open_access_enabled():
        return redirect('login')

    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'GET':
        return render(request, 'registration/enter.html', {
            'enter_url': reverse('open_enter'),
            'next': request.GET.get('next') or settings.LOGIN_REDIRECT_URL,
        })

    User = get_user_model()
    username = open_access_username()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseForbidden(f'访客账号 {username} 不存在。')

    if not user.is_active:
        return HttpResponseForbidden('访客账号已停用。')

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    next_url = request.POST.get('next') or settings.LOGIN_REDIRECT_URL
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        next_url = settings.LOGIN_REDIRECT_URL
    return redirect(next_url)


class OpenAccessLoginView:
    """包装 LoginView：把 open_access 标志塞进模板上下文。"""

    @classmethod
    def as_view(cls, **initkwargs):
        from django.contrib.auth.views import LoginView

        class _View(LoginView):
            def get_context_data(self, **kwargs):
                ctx = super().get_context_data(**kwargs)
                ctx['open_access'] = open_access_enabled()
                ctx['open_enter_url'] = reverse('open_enter')
                return ctx

            def dispatch(self, request, *args, **kwargs):
                # 已登录直接进系统
                if request.user.is_authenticated:
                    return redirect(self.get_success_url())
                return super().dispatch(request, *args, **kwargs)

        return _View.as_view(**initkwargs)
