from django import forms
from phonenumber_field.formfields import PhoneNumberField
from .models import Curso, PlanDeEstudio, Usuario, Rol, NombresAsignatura, AreasPlanesDiferenciales, Asignatura, Estudiante, Aula, PromedioAsignatura
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UniqueDirectorRoleFormMixin:
    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if rol is None or rol.name.strip().casefold() != 'director':
            return rol

        usuarios_directores = Usuario.objects.filter(
            rol__name__iexact='director',
            is_active=True
        )
        if self.instance.pk:
            usuarios_directores = usuarios_directores.exclude(
                pk=self.instance.pk
            )
        if usuarios_directores.exists():
            raise forms.ValidationError(
                'Ya existe un usuario activo con el rol Director.'
            )
        return rol

class UsuarioForm(UniqueDirectorRoleFormMixin, UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'name', 'last_name', 'rut', 'email', 'telefono', 'rol', 'avatar', 'password1', 'password2']

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['name', 'description']

class UserUpdateForm(UniqueDirectorRoleFormMixin, UserChangeForm):
    password_nueva = forms.CharField(required=False, strip=False, widget=forms.PasswordInput)
    password_confirmacion = forms.CharField(required=False, strip=False, widget=forms.PasswordInput)
    telefono = PhoneNumberField()

    class Meta:
        model = Usuario
        fields = ['username', 'name', 'last_name', 'rut', 'email', 'telefono', 'rol', 'avatar', 'asignatura_id']

    def clean(self):
        cleaned = super().clean()
        nueva = cleaned.get('password_nueva')
        confirmacion = cleaned.get('password_confirmacion')
        asignaturas = cleaned.get('asignatura_id')

        if not asignaturas:
            self.add_error('asignatura_id', 'El docente debe estar asociado al menos en una asignatura.')
    
        if not (nueva or confirmacion):
            return cleaned # se deja en blanco si no se desea cambiar
    
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

    def save(self, commit=True):
        user = super().save(commit=False)
        nueva = self.cleaned_data.get('password_nueva')

        if nueva:
            user.set_password(nueva)
            
        if commit:
            user.save()
            self.save_m2m()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asignatura_id'].queryset = Asignatura.objects.filter(
            is_active=True
        ).select_related('nombres_asignatura_id')

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        docentes = Usuario.objects.filter(
            rol__name__iexact='docente',
            is_active=True
        )
        cursos_otros = Curso.objects.all()
        
        if self.instance.pk:
            print('self.instance.id: ', self.instance.pk)
            cursos_otros = cursos_otros.exclude(pk=self.instance.pk)

        docentes_asignados = cursos_otros.values_list(
            'usuario_id', flat=True
        )
        docentes_disponibles = docentes.exclude(pk__in=docentes_asignados, is_active=False)
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
            'rut': 'RUT',
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

class PromedioAsignaturaCreateForm(forms.ModelForm):
    nota = forms.CharField(required=False, label='Nota', widget=forms.TextInput())

    class Meta:
        model = PromedioAsignatura
        fields = ['asignatura_id', 'nota']
        labels = {
            'asignatura_id': 'Asignatura',
        }
        widgets = {
            'asignatura_id': forms.Select(),
        }

    def __init__(self, *args, estudiante=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.estudiante = estudiante
        self.instance.estudiante_id_id = estudiante.rut
        self.fields['asignatura_id'].queryset = Asignatura.objects.filter(
            is_active=True
        )

    def clean_nota(self):
        valor = (self.cleaned_data.get('nota') or '').strip().replace(',', '.')

        if not valor:
            return None

        try:
            numero = float(valor)
        except ValueError:
            raise forms.ValidationError('Ingrese una nota numérica, por ejemplo 5.5.')

        if not 1.0 <= numero <= 7.0:
            raise forms.ValidationError('La nota debe estar entre 1.0 y 7.0.')

        return round(numero, 1)

    def clean(self):
        cleaned = super().clean()
        asignatura = cleaned.get('asignatura_id')

        if asignatura:
            cantidad = PromedioAsignatura.objects.filter(
                estudiante_id=self.estudiante.rut,
                asignatura_id=asignatura,
            ).exclude(pk=self.instance.pk).count()

            if cantidad >= 8:
                raise forms.ValidationError('Un estudiante puede tener como máximo 8 notas por asignatura.')

        return cleaned

class PromedioAsignaturaUpdateForm(forms.ModelForm):
    nota = forms.CharField(required=False, label='Nota', widget=forms.TextInput())

    class Meta:
        model = PromedioAsignatura
        fields = ['asignatura_id', 'nota']
        labels = {
            'asignatura_id': 'Asignatura',
        }
        widgets = {
            'asignatura_id': forms.Select(),
        }

    def __init__(self, *args, estudiante=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.estudiante = estudiante
        self.instance.estudiante_id_id = estudiante.rut
        self.fields['asignatura_id'].queryset = Asignatura.objects.filter(
            is_active=True
        )

    def clean_nota(self):
        valor = (self.cleaned_data.get('nota') or '').strip().replace(',', '.')

        if not valor:
            return None

        try:
            numero = float(valor)
        except ValueError:
            raise forms.ValidationError('Ingrese una nota numérica, por ejemplo 5.5.')

        if not 1.0 <= numero <= 7.0:
            raise forms.ValidationError('La nota debe estar entre 1.0 y 7.0.')

        return round(numero, 1)

    def clean(self):
        cleaned = super().clean()
        asignatura = cleaned.get('asignatura_id')

        if asignatura:
            cantidad = PromedioAsignatura.objects.filter(
                estudiante_id=self.estudiante.rut,
                asignatura_id=asignatura,
            ).exclude(pk=self.instance.pk).count()

            if cantidad >= 5:
                raise forms.ValidationError('Un estudiante puede tener como máximo 5 notas por asignatura.')

        return cleaned

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
            'hrs_asignatura': forms.NumberInput(attrs={'class': 'form-control form-crud', 'min': 1, 'max': 8, 'step': 0.5, 'required': 'true'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asignatura_id'].queryset = Asignatura.objects.filter(
            is_active=True
        )

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
            'hrs_asignatura': forms.NumberInput(attrs={'class': 'form-control form-crud', 'min': 1, 'max': 8, 'step': 0.5, 'required': 'true'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asignatura_id'].queryset = Asignatura.objects.filter(
            is_active=True
        )

class AsignaturasCreateForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['ident', 'nombres_asignatura_id', 'descripcion', 'areas_planes_diferenciales_id', 'color']
        widgets = { 
            'nombres_asignatura_id': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2 bg-white dark:bg-[#141826] text-sm focus:ring-blue-600 focus-visible:ring-[3px] transition duration-300 focus:transition focus:duration-300 rounded-lg invalid:border-red-400 focus:outline-none dark:bg-slate-800 dark:text-white'}),
            'areas_planes_diferenciales_id': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2 bg-white dark:bg-[#141826] text-sm focus:ring-blue-600 focus-visible:ring-[3px] transition duration-300 focus:transition focus:duration-300 rounded-lg invalid:border-red-400 focus:outline-none dark:bg-slate-800 dark:text-white'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombres_asignatura_id'].queryset = NombresAsignatura.objects.filter(
            is_active=True
        )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['areas_planes_diferenciales_id'].queryset = AreasPlanesDiferenciales.objects.filter(
            is_active=True
        )

class AsignaturaUpdateForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['ident', 'nombres_asignatura_id', 'descripcion', 'areas_planes_diferenciales_id', 'color']
        widgets = { 
            'nombres_asignatura_id': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2 bg-white dark:bg-[#141826] text-sm focus:ring-blue-600 focus-visible:ring-[3px] transition duration-300 focus:transition focus:duration-300 rounded-lg invalid:border-red-400 focus:outline-none dark:bg-slate-800 dark:text-white'}),
            'areas_planes_diferenciales_id': forms.Select(attrs={'class': 'w-full rounded border my-2 px-2 py-2 bg-white dark:bg-[#141826] text-sm focus:ring-blue-600 focus-visible:ring-[3px] transition duration-300 focus:transition focus:duration-300 rounded-lg invalid:border-red-400 focus:outline-none dark:bg-slate-800 dark:text-white'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombres_asignatura_id'].queryset = NombresAsignatura.objects.filter(
            is_active=True
        )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['areas_planes_diferenciales_id'].queryset = AreasPlanesDiferenciales.objects.filter(
            is_active=True
        )

class NombresAsignaturaForm(forms.ModelForm):
    class Meta:
        model = NombresAsignatura
        fields = ['nombre']

class AreasPlanesDiferencialesForm(forms.ModelForm):
    class Meta:
        model = AreasPlanesDiferenciales
        fields = ['nombre']