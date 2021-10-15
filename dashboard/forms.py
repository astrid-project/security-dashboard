from django import forms

class UploadFileForm(forms.Form):
    # title = forms.CharField(max_length=50)
    file = forms.FileField()


class CubebeatForm(forms.Form):
    enabled = forms.BooleanField(label='Enabled', help_text='Enable/disable the collection of synflood data')
    period = forms.CharField(label='Period', help_text='Period to collect the synflood data')
    service_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(widget=forms.HiddenInput())
    partner = forms.CharField(widget=forms.HiddenInput())


class AlgorithmForm(forms.Form):
    window = forms.CharField(label='Time window', help_text='Time window for batch processing')
    service_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(widget=forms.HiddenInput())
    partner = forms.CharField(widget=forms.HiddenInput())