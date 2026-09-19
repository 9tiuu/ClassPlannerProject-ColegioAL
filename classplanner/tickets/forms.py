from django import forms
from .models import Curso, PlanDeEstudio, Usuario, Rol
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

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nivel', 'letra', 'horas_plan_total', 'usuario_id']
        labels = {
            'nivel': 'Nivel del Curso',
            'letra': 'Letra del Curso',
            'horas_plan_total': 'Horas Planificadas',
            'usuario_id': 'Docente Jefe'
        }
        widgets = {
            'nivel': forms.Select(attrs={'class': 'form-control form-crud', 'required': ''}),
            'letra': forms.TextInput(attrs={'class': 'form-control form-crud', 'required': ''}),
            'horas_plan_total': forms.NumberInput(attrs={'class': 'form-control form-crud', 'min': 0, 'step': 0.5, 'required': ''}),
            'usuario_id': forms.Select(attrs={'class': 'form-control form-crud', 'required': ''}),
        }

class PlanDeEstudioCreateForm(forms.ModelForm):
    class Meta:
        model = PlanDeEstudio
        fields = ['hrs_asignatura', 'curso_id', 'asignatura_id']
        labels = {
            'hrs_asignatura': 'Horas de Asignatura',
            'curso_id': 'Curso',
            'asignatura_id': 'Asignaturas'
        }
        widgets = {
            'curso_id': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2', 'required': 'true'}),
            'hrs_asignatura': forms.NumberInput(attrs={'class': 'form-control form-crud', 'min': 0, 'max': 8, 'step': 0.5, 'required': ''})
        }

class PlanDeEstudioUpdateForm(forms.ModelForm):
    class Meta:
        model = PlanDeEstudio
        fields = ['hrs_asignatura', 'curso_id', 'asignatura_id']
        labels = {
            'hrs_asignatura': 'Horas de Asignatura',
            'curso_id': 'Curso',
            'asignatura_id': 'Asignaturas'
        }
        widgets = {
        }