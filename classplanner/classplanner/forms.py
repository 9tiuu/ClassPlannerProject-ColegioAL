from django import forms
from .models import Curso, PlanDeEstudio, Usuario, Rol, Asignatura, Estudiante, Aula
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
    letra = forms.ChoiceField(
        choices=[
            ('A', 'A'),
            ('B', 'B'),
        ],
        label='Letra del Curso',
        widget=forms.Select(attrs={
            'class': 'form-control form-crud',
            'required': ''
        })
    )
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        docentes = Usuario.objects.filter(
            rol__name__iexact='docente'
        )
        cursos_otros = Curso.objects.all()
        
        if self.instance.pk:
            print('self.instance.id: ', self.instance.pk)
            cursos_otros = cursos_otros.exclude(pk=self.instance.pk)

        docentes_asignados = cursos_otros.values_list(
            'usuario_id', flat=True
        )
        docentes_disponibles = docentes.exclude(pk__in=docentes_asignados)
        if self.instance.pk:
            docentes_disponibles |= Usuario.objects.filter(
                pk=self.instance.usuario_id_id
            )
        self.fields['usuario_id'].queryset = docentes_disponibles

class AulaCreateForm(forms.ModelForm):
    class Meta:
        model = Aula
        fields = ['nombre', 'cupos', 'curso_id']
        labels = {
            'nombre': 'Nombre del Aula',
            'cupos': 'Capacidad de Alumnos',
            'curso_id': 'Cursos Asignados',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control form-crud', 'required': ''}),
            'cupos': forms.NumberInput(attrs={'class': 'form-control form-crud', 'min': 1, 'step': 1, 'required': ''}),
            'curso_id': forms.SelectMultiple(attrs={'class': 'form-control form-crud'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        otras_aulas = Aula.objects.exclude(pk=self.instance.pk)
        ocupados = Curso.objects.filter(aula__in=otras_aulas).values('pk')
        self.fields['curso_id'].queryset = Curso.objects.exclude(pk__in=ocupados)

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()

        if Aula.objects.exclude(pk=self.instance.pk).filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError('Ya existe un aula con ese nombre.')

        return nombre

    def clean_cupos(self):
        cupos = self.cleaned_data.get('cupos')

        if cupos is not None and cupos < 1:
            raise forms.ValidationError('La capacidad debe ser al menos 1 alumno.')

        return cupos

    def clean_curso_id(self):
        cursos = self.cleaned_data.get('curso_id')

        if cursos is not None and cursos.count() > 2:
            raise forms.ValidationError('Un aula puede tener como máximo 2 cursos.')

        return cursos


class AulaUpdateForm(forms.ModelForm):
    class Meta:
        model = Aula
        fields = ['nombre', 'cupos', 'curso_id']
        labels = {
            'nombre': 'Nombre del Aula',
            'cupos': 'Capacidad de Alumnos',
            'curso_id': 'Cursos Asignados'
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control form-crud', 'required': ''}),
            'cupos': forms.NumberInput(attrs={'class': 'form-control form-crud', 'min': 1, 'step': 1, 'required': ''}),
            'curso_id': forms.SelectMultiple(attrs={'class': 'form-control form-crud'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        otras_aulas = Aula.objects.exclude(pk=self.instance.pk)
        ocupados = Curso.objects.filter(aula__in=otras_aulas).values('pk')
        self.fields['curso_id'].queryset = Curso.objects.exclude(pk__in=ocupados)

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()

        if Aula.objects.exclude(pk=self.instance.pk).filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError('Ya existe un aula con ese nombre.')

        return nombre

    def clean_cupos(self):
        cupos = self.cleaned_data.get('cupos')

        if cupos is not None and cupos < 1:
            raise forms.ValidationError('La capacidad debe ser al menos 1 alumno.')

        return cupos

    def clean_curso_id(self):
        cursos = self.cleaned_data.get('curso_id')

        if cursos is not None and cursos.count() > 2:
            raise forms.ValidationError('Un aula puede tener como máximo 2 cursos.')

        return cursos
    
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
    error_class = "bg-red-100 dark:bg-red-900 p-4 mb-4 text-sm text-red-700 rounded-lg dark:text-red-300 transition duration-200"
    class Meta:
        model = PlanDeEstudio
        fields = ['curso_id', 'hrs_asignatura', 'asignatura_id']
        labels = {
            'hrs_asignatura': 'Horas',
            'curso_id': 'Curso',
            'asignatura_id': 'Asignatura(s)'
        }
        widgets = { # sin curso_id required
            'curso_id': CursoSelect(attrs={'class': 'w-full rounded border my-2 px-2 py-2 invalid:border-red-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-300 dark:bg-slate-800 dark:text-white dark:border-slate-600 dark:focus:ring-blue-300 dark:focus:border-blue-300'}),
            'hrs_asignatura': forms.NumberInput(attrs={'class': 'form-control form-crud', 'min': 0, 'max': 8, 'step': 0.5, 'required': 'true'})
        }

class AsignaturasCreateForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['ident', 'nombre', 'descripcion', 'plan_diferencial']
        widgets = { 
            'nombre': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2 bg-white dark:bg-[#141826] text-sm focus:ring-blue-600 focus-visible:ring-[3px] transition duration-300 focus:transition focus:duration-300 rounded-lg invalid:border-red-400 focus:outline-none dark:bg-slate-800 dark:text-white'}),
            'plan_diferencial': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2 bg-white dark:bg-[#141826] text-sm focus:ring-blue-600 focus-visible:ring-[3px] transition duration-300 focus:transition focus:duration-300 rounded-lg invalid:border-red-400 focus:outline-none dark:bg-slate-800 dark:text-white'}),
        }

class AsignaturaUpdateForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['ident', 'nombre', 'descripcion', 'plan_diferencial']
        widgets = { 
            'nombre': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2 bg-white dark:bg-[#141826] text-sm focus:ring-blue-600 focus-visible:ring-[3px] transition duration-300 focus:transition focus:duration-300 rounded-lg invalid:border-red-400 focus:outline-none dark:bg-slate-800 dark:text-white'}),
            'plan_diferencial': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2 bg-white dark:bg-[#141826] text-sm focus:ring-blue-600 focus-visible:ring-[3px] transition duration-300 focus:transition focus:duration-300 rounded-lg invalid:border-red-400 focus:outline-none dark:bg-slate-800 dark:text-white'}),
        }