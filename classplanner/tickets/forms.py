from django import forms
from .models import Usuario, Rol
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.forms import AuthenticationForm

class UsuarioForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'name', 'last_name', 'rut', 'email', 'telefono', 'rol', 'avatar', 'password1', 'password2']
        labels = {
            'username': 'Nombre de Usuario',
            'name': 'Nombre',
            'last_name': 'Apellido',
            'rut': 'RUT',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'rol': 'Rol de Usuario',
            'avatar':'Foto de Usuario',
            'password1':'Contraseña',
            'password2':'Confirmar Contraseña'
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':2, 'required': ''}),
            'name': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':2, 'required': ''}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':2, 'required': ''}),
            'rut': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':9, 'maxlength':10, 'required': ''}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-crud'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':9, 'maxlength':10, 'required': ''}),
            'rol': forms.Select(attrs={'class': 'form-control form-crud'}),
            'avatar':forms.ClearableFileInput(attrs={'class': 'form-control form-crud'}),
            'password1':forms.PasswordInput(attrs={'class': 'form-control form-crud'}),
            'password2':forms.PasswordInput(attrs={'class': 'form-control form-crud'})
        }

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['name', 'description']
        labels = {
            'name': 'Nombre del Rol',
            'description': 'Descripción'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control mt-2', 'minlength':2, 'maxlength':45, 'required': ''}),
            'description': forms.Textarea(attrs={'class': 'form-control mt-2', 'rows': 3, 'minlength':2, 'required': ''}),
        }

class UserUpdateForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ['username', 'name', 'last_name', 'rut', 'email', 'telefono', 'rol', 'avatar']
        labels = {
            'username': 'Nombre de Usuario',
            'name': 'Nombre',
            'last_name': 'Apellido',
            'rut': 'RUT',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'rol': 'Rol de Usuario',
            'avatar':'Foto de Usuario'
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':2, 'maxlength':45, 'required': ''}),
            'name': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':2, 'maxlength':45, 'required': ''}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':2, 'maxlength':45, 'required': ''}),
            'rut': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':9, 'maxlength':10, 'required': ''}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-crud', 'minlength':2, 'maxlength':45, 'required': ''}),
            'telefono': forms.TextInput(attrs={'class': 'form-control form-crud', 'minlength':9, 'maxlength':10, 'required': ''}),
            'rol': forms.Select(attrs={'class': 'form-control form-crud'}),
            'avatar':forms.ClearableFileInput(attrs={'class': 'form-control form-crud'})
        }

