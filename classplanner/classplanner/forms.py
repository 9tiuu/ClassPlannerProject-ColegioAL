from django import forms
from phonenumber_field.formfields import PhoneNumberField
from .models import Curso, PlanDeEstudio, Usuario, Rol, NombresAsignatura, AreasPlanesDiferenciales, Asignatura, Estudiante, Aula, PromedioAsignatura
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from django.utils.timezone import now
import re

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
    letra = forms.CharField(
        max_length=1,
        widget=forms.TextInput(attrs={'class': 'form-control form-crud', 'required': ''}),
        error_messages={'max_length': 'Solo se aceptan letras de A-Z.'},
    )

    def clean_letra(self):
        letra = (self.cleaned_data.get('letra') or '').strip().upper()
        if re.fullmatch(r'[A-Z]', letra) is None:
            raise forms.ValidationError('Solo se aceptan letras de A-Z.')
        return letra

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

#PROMEDIOS
MIN_NOTAS_PROMEDIO = 1
MAX_NOTAS_ASIGNATURA = 8

class NotaField(forms.Field):
    def __init__(self, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('widget', forms.NumberInput(attrs={
            'class': 'form-control nota-input',
            'placeholder': '-',
            'inputmode': 'decimal',
            'step': '0.1',
            'min': '1.0',
            'max': '7.0',
        }))
        super().__init__(**kwargs)

    def to_python(self, value):
        valor = str(value if value is not None else '').strip().replace(',', '.')
        if not valor:
            return None
        if not re.fullmatch(r'[1-7]\.[0-9]', valor):
            raise forms.ValidationError('Ingrese una nota válida, por ejemplo 5.5.')
        nota = Decimal(valor)
        if nota > Decimal('7.0'):
            raise forms.ValidationError('La nota debe estar entre 1.0 y 7.0.')
        return float(nota)


class PlanillaNotasForm(forms.Form):
    def __init__(self, *args, estudiantes, curso, asignaturas, **kwargs):
        super().__init__(*args, **kwargs)
        self.estudiantes = list(estudiantes)
        self.curso = curso
        self.asignaturas = list(asignaturas)
        self.notas = {}
        existentes = PromedioAsignatura.objects.filter(
            estudiante_id__in=[e.rut for e in self.estudiantes],
            curso_id=self.curso.pk,
            asignatura_id__in=[a.pk for a in self.asignaturas],
        ).order_by('id')
        for nota in existentes:
            self.notas.setdefault(
                (nota.estudiante_id_id, nota.asignatura_id_id), []
            ).append(nota)
        for estudiante in self.estudiantes:
            for asignatura in self.asignaturas:
                guardadas = self.notas.get((estudiante.rut, asignatura.pk), [])
                for numero in range(1, MAX_NOTAS_ASIGNATURA + 1):
                    self.fields[self.nombre(estudiante.rut, asignatura.pk, numero)] = NotaField(
                        label=f'Nota {numero}',
                        initial=guardadas[numero - 1].nota if numero <= len(guardadas) else None,
                    )

    @staticmethod
    def nombre(rut, asignatura_pk, numero):
        return f'nota_{rut}_{asignatura_pk}_{numero}'

    def fila(self, rut, asignatura_pk):
        campos = [
            self[self.nombre(rut, asignatura_pk, n)]
            for n in range(1, MAX_NOTAS_ASIGNATURA + 1)
        ]
        valores = []
        for campo in campos:
            valor = campo.value()
            if valor in (None, ''):
                continue
            try:
                valores.append(float(str(valor).replace(',', '.')))
            except ValueError:
                pass
        media = sum(valores) / len(valores) if len(valores) >= MIN_NOTAS_PROMEDIO else None
        return {
            'campos': campos,
            'cantidad': len(valores),
            'media': media,
            'promedio': None if media is None else round(media, 1),
        }

    def save(self):
        crear, actualizar, borrar = [], [], []
        for estudiante in self.estudiantes:
            for asignatura in self.asignaturas:
                guardadas = self.notas.get((estudiante.rut, asignatura.pk), [])
                valores = [
                    valor
                    for valor in (
                        self.cleaned_data.get(self.nombre(estudiante.rut, asignatura.pk, n))
                        for n in range(1, MAX_NOTAS_ASIGNATURA + 1)
                    )
                    if valor is not None
                ]
                for indice, valor in enumerate(valores):
                    if indice < len(guardadas):
                        if guardadas[indice].nota != valor:
                            guardadas[indice].nota = valor
                            actualizar.append(guardadas[indice])
                    else:
                        crear.append(PromedioAsignatura(
                            estudiante_id=estudiante,
                            curso_id=self.curso,
                            asignatura_id=asignatura,
                            nota=valor,
                        ))
                borrar.extend(nota.pk for nota in guardadas[len(valores):])
        with transaction.atomic():
            if actualizar:
                PromedioAsignatura.objects.bulk_update(actualizar, ['nota'])
            if crear:
                PromedioAsignatura.objects.bulk_create(crear)
            if borrar:
                PromedioAsignatura.objects.filter(pk__in=borrar).delete()
        return [estudiante.rut for estudiante in self.estudiantes]

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