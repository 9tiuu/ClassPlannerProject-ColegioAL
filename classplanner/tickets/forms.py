from django import forms
from .models import Usuario, Rol
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from django.contrib.auth.forms import AuthenticationForm

class UsuarioForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'name', 'last_name', 'rut', 'email', 'telefono', 'rol', 'avatar', 'password1', 'password2']

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['name', 'description']

class UserUpdateForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ['username', 'name', 'last_name', 'rut', 'email', 'telefono', 'rol', 'avatar']