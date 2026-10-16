from django import forms
from .models import Curso, PlanDeEstudio, Usuario, Rol, Asignatura, PlanDiferencial, Estudiante
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

class EstudiantesCreateForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ['nombre', 'apellido_m', 'apellido_p', 'rut', 'curso_id']
        labels = {
            'nombre': 'Nombre',
            'apellido_m': 'Apellido Materno',
            'apellido_p': 'Apellido Paterno',
            'rut': 'RUN',
            'curso_id': 'Curso',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'required': 'true'}),
            'apellido_m': forms.TextInput(attrs={'required': 'true'}),
            'apellido_p': forms.TextInput(attrs={'required': 'true'}),
            'rut': forms.TextInput(attrs={'required': 'true'}),
            'curso_id': forms.Select(attrs={'required': 'true'}),
        }

class EstudiantesUpdateForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ['nombre', 'apellido_m', 'apellido_p', 'curso_id']
        labels = {
            'nombre': 'Nombre',
            'apellido_m': 'Apellido Materno',
            'apellido_p': 'Apellido Paterno',
            'curso_id': 'Curso',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'required': 'true'}),
            'apellido_m': forms.TextInput(attrs={'required': 'true'}),
            'apellido_p': forms.TextInput(attrs={'required': 'true'}),
            'curso_id': forms.Select(attrs={'required': 'true'}),
        }

# Para creación PDE
class CursoSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        curso = getattr(value, 'instance', None)
        if curso is not None:
            option['attrs']['data-horas-plan-total'] = curso.horas_plan_total
        return option

class PlanDeEstudioCreateForm(forms.ModelForm):
    error_class = "bg-red-100 dark:bg-red-900 p-4 mb-4 text-sm text-red-700 rounded-lg dark:text-red-300 transition duration-200"
    class Meta:
        model = PlanDeEstudio
        fields = ['hrs_asignatura', 'curso_id', 'asignatura_id']
        labels = {
            'hrs_asignatura': 'Horas',
            'curso_id': 'Curso',
            'asignatura_id': 'Asignatura(s)'
        }
        widgets = {
            'curso_id': CursoSelect(attrs={'class': 'w-full rounded border my-2 px-2 py-2 invalid:border-red-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-300 dark:bg-slate-800 dark:text-white dark:border-slate-600 dark:focus:ring-blue-300 dark:focus:border-blue-300', 'required': 'true'}),
            'hrs_asignatura': forms.NumberInput(attrs={'class': 'form-control form-crud', 'min': 0, 'max': 8, 'step': 0.5, 'required': 'true'})
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
        widgets = {}


class AsignaturasCreateForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['ident', 'nombre', 'descripcion', 'plan_diferencial_id']

class AsignaturaUpdateForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['ident', 'nombre', 'descripcion', 'plan_diferencial_id']

class PlanDiferencialCreateForm(forms.ModelForm):
    class Meta:
        model = PlanDiferencial
        fields = ['nombre']

class PlanDiferencialUpdateForm(forms.ModelForm):
    class Meta:
        model = PlanDiferencial
        fields = ['nombre']