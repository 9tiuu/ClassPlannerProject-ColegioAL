from django import forms
from tickets.models import Usuario
from django.contrib.auth import authenticate

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'name', 'last_name', 'rut', 'email', 'telefono', 'avatar']

class ChangePassowrdForm(forms.Form):
    password_actual = forms.CharField(label="Contraseña actual", widget=forms.PasswordInput)
    password_nueva = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput)
    password_confirmacion = forms.CharField(label="Confirmar nueva contraseña", widget=forms.PasswordInput)

    def __init__(self, usuario, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario

    def clean_password_actual(self):
        password_actual = self.cleaned_data.get("password_actual")

        if not authenticate(username=self.usuario.email, password=password_actual):
            raise forms.ValidationError("La contraseña actual es incorrecta.")

        return password_actual

    def clean(self):
        cleaned_data = super().clean()
        password_nueva = cleaned_data.get("password_nueva")
        password_confirmacion = cleaned_data.get("password_confirmacion")

        if ( password_nueva and password_confirmacion and password_nueva != password_confirmacion):
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return cleaned_data