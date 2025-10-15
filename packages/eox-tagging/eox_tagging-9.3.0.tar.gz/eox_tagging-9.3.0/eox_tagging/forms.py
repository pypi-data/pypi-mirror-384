"""Tag form used in admin."""
from django import forms


class TagForm(forms.ModelForm):
    """Form used to add extra field to admin."""
    opaque_key = forms.CharField(required=False)
