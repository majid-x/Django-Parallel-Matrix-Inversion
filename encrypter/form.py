from django import forms

class MatrixSizeForm(forms.Form):
    size = forms.IntegerField(
        min_value=1,
        label="Matrix Size",
        widget=forms.NumberInput(attrs={'placeholder': 'Enter matrix size'}),
    )
