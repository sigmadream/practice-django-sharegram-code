from django import forms
from .models import Link

class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['url']
        widgets = {'url': forms.URLInput(attrs={'placeholder': 'https://example.com', 'class': 'form-control'})}