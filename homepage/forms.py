from django import forms

class ChannelIDForm(forms.Form):
    channel_id = forms.CharField(label='channel_id', max_length=250)
    # channel_name = forms.CharField(max_length=250, )
    widget ={
        'channel_id': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Type your YouTube channel ID'})
    }
    
