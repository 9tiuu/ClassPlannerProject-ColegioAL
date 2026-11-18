from django import forms
from classplanner.models import Usuario
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField
import re

PATRON_NOMBRE = r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$'

def validar_rut(rut):
    rut = rut.replace(".", "").upper()
    if not re.match(r"^(\d{1,8})-([0-9K])$", rut):
        raise ValidationError("El RUT tiene un formato incorrecto.")
    return True

class ProfileForm(forms.ModelForm):
    password_actual = forms.CharField(required=False, strip=False, widget=forms.PasswordInput)
    password_nueva = forms.CharField(required=False, strip=False, widget=forms.PasswordInput)
    password_confirmacion = forms.CharField(required=False, strip=False, widget=forms.PasswordInput)
    telefono = PhoneNumberField()

    class Meta:
        model = Usuario
        fields = ['username', 'name', 'last_name', 'rut', 'email', 'telefono', 'avatar']

    def clean_username(self):
        username = self.cleaned_data['username']
        if not re.match(PATRON_NOMBRE, username):
            raise ValidationError('El nombre de usuario solo puede contener letras y espacios.')
        return username

    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.match(PATRON_NOMBRE, name):
            raise ValidationError('El nombre solo puede contener letras y espacios.')
        return name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not re.match(PATRON_NOMBRE, last_name):
            raise ValidationError('El apellido solo puede contener letras y espacios.')
        return last_name

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        validar_rut(rut)  # lanza ValidationError si el formato es incorrecto
        return rut

    def clean(self):
        cleaned = super().clean()
        actual = cleaned.get('password_actual')
        nueva = cleaned.get('password_nueva')
        confirmacion = cleaned.get('password_confirmacion')

        if not (actual or nueva or confirmacion):
            return cleaned  # no quiere cambiar la contraseña

        if not self.instance.check_password(actual or ''):
            self.add_error('password_actual', 'La contraseña actual es incorrecta.')

        if not nueva:
            self.add_error('password_nueva', 'Debe ingresar una nueva contraseña.')
        else:
            try:
                validate_password(nueva, user=self.instance)
            except ValidationError as e:
                self.add_error('password_nueva', e)

            if nueva != confirmacion:
                self.add_error('password_confirmacion', 'Las nuevas contraseñas no coinciden.')
        return cleaned

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

    def clean_password_nueva(self):
        password_nueva = self.cleaned_data.get('password_nueva')
        validate_password(password_nueva, user=self.usuario)
        return password_nueva

    def clean(self):
        cleaned_data = super().clean()
        password_nueva = cleaned_data.get("password_nueva")
        password_confirmacion = cleaned_data.get("password_confirmacion")

        if (password_nueva and password_confirmacion and password_nueva != password_confirmacion):
            # raise forms.ValidationError("Las contraseñas no coinciden.")
            self.add_error('password_confirmacion', 'Las contraseñas no coinciden.')
        return cleaned_data