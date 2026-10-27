from django import forms

from .models import Tenant


class BrandingForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'short_name', 'display_name', 'primary_color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：某某酒业'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }
