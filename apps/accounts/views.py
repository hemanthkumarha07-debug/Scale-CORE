import logging
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings

from .forms import SCALELoginForm
from .models import SCALEUser
from .middleware import get_client_ip
from apps.audit.models import AuditLog

logger = logging.getLogger('scale_core.security')


class SCALELoginView(View):
    """
    Enterprise Authentication View for SCALE.Core.
    Implements rate-limiting awareness, failed login tracking, and
    append-only cryptographic audit logging.
    """
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(request.GET.get('next') or 'overview')
        form = SCALELoginForm()
        return render(request, self.template_name, {
            'form': form,
            'next': request.GET.get('next', ''),
            'logged_out': request.GET.get('logged_out') == '1'
        })

    def post(self, request):
        if request.user.is_authenticated:
            return redirect(request.GET.get('next') or 'overview')

        form = SCALELoginForm(request, data=request.POST)
        ip = get_client_ip(request)
        next_url = request.POST.get('next') or request.GET.get('next') or 'overview'

        if form.is_valid():
            user = form.get_user()
            # Reset failed login attempts on successful authentication
            if user.failed_login_attempts > 0:
                user.failed_login_attempts = 0
            user.last_login_ip = ip
            user.save(update_fields=['failed_login_attempts', 'last_login_ip'])

            # Log into session
            login(request, user)

            # Record cryptographic audit log entry
            AuditLog.record_event(
                event_type='USER_AUTHENTICATION_SUCCESS',
                entity_type='SCALEUser',
                entity_id=str(user.id),
                actor=user,
                source_ip=ip,
                state_after={
                    'username': user.username,
                    'role': user.role,
                    'department': user.department
                }
            )

            # Ensure safe redirection
            if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                next_url = 'overview'

            messages.success(request, f"Welcome back, {user.get_full_name() or user.username} ({user.get_role_display()}).")
            return redirect(next_url)
        else:
            username = request.POST.get('username', '').strip()
            # Track failed attempt on user if account exists
            if username:
                try:
                    user_target = SCALEUser.objects.get(username=username)
                    user_target.failed_login_attempts += 1
                    user_target.save(update_fields=['failed_login_attempts'])
                except SCALEUser.DoesNotExist:
                    pass

            AuditLog.record_event(
                event_type='USER_AUTHENTICATION_FAILURE',
                entity_type='SCALEUser',
                entity_id=username or 'UNKNOWN',
                actor=None,
                source_ip=ip,
                state_after={'attempted_username': username}
            )

            messages.error(request, "Invalid username or password. Please verify your credentials and try again.")
            return render(request, self.template_name, {
                'form': form,
                'next': next_url
            })


class SCALELogoutView(View):
    """
    Terminates the active session and logs the audit event.
    Supports both GET and POST for seamless UI navigation.
    """
    def get(self, request):
        return self._do_logout(request)

    def post(self, request):
        return self._do_logout(request)

    def _do_logout(self, request):
        if request.user.is_authenticated:
            user = request.user
            ip = get_client_ip(request)
            AuditLog.record_event(
                event_type='USER_LOGOUT',
                entity_type='SCALEUser',
                entity_id=str(user.id),
                actor=user,
                source_ip=ip
            )
            logout(request)
        return redirect('/accounts/login/?logged_out=1')
