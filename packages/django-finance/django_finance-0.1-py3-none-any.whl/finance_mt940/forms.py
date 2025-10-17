from django import forms


class UploadMt940FileForm(forms.Form):
    mt940_file = forms.FileField(required=True, allow_empty_file=False)
