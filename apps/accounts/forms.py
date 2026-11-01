from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

class SCALELoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'scale-input',
            'placeholder': 'Enter your username (e.g., hemanth.supervisor)',
            'autocomplete': 'username',
            'autofocus': True,
            'style': 'width: 100%; box-sizing: border-box;'
        }),
        label=_('Username')
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'scale-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'style': 'width: 100%; box-sizing: border-box;'
        }),
        label=_('Password')
    )
