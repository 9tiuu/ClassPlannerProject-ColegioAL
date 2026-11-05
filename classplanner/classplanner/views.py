from django.forms import ValidationError
from django.http import request, Http404, HttpResponse
from django.core.exceptions import PermissionDenied, BadRequest
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views import View
from django.contrib import messages
from django.db.models.deletion import RestrictedError
from datetime import datetime
import re
from math import floor

from easyaudit.models import CRUDEvent
from .models import Rol, Usuario, Asignatura, PlanDeEstudio, Curso, Estudiante, Aula, PromedioAsignatura, CargaHoraria, Bloque, BloqueDeClase
from .forms import (
    RolForm, UsuarioForm, UserUpdateForm,
    PlanDeEstudioCreateForm, PlanDeEstudioUpdateForm,
    CursoForm, AsignaturasCreateForm, AsignaturaUpdateForm,
    AulaCreateForm, AulaUpdateForm,
    EstudiantesCreateForm, EstudiantesUpdateForm,
    PromedioAsignaturaCreateForm, PromedioAsignaturaUpdateForm
)

from django.contrib.auth import logout, get_user_model
from django.shortcuts import redirect
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.query import QuerySet
from functools import wraps
from .static.classplanner.py.exportar_planes import exportar_planes
from .static.classplanner.py.exportar_notas import _exportar_notas_pdf
from datetime import time, datetime, date

# Create your views here.

def fecha_actual():
    return datetime.now("America/Santiago")

def validar_rut(rut):
    rut = rut.replace(".", "").upper()
    match = re.match(r"^(\d{1,8})[-]([0-9Kk])$", rut)

    if not match:
        raise ValidationError("El RUT tiene un formato incorrecto")
    return True

def roles_required(*roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                rol = request.user.rol.name
            except AttributeError:
                raise PermissionDenied(
                    'Ha intentado visitar una página a la que no tiene acceso'
                )

            if rol not in roles_permitidos:
                raise PermissionDenied(
                    'Ha intentado visitar una página a la que no tiene acceso'
                )

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator

def periodo_planificacion_required():
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            año_actual = datetime.now().year
            hoy = datetime.now().date()
            if (
                hoy < datetime(
                    año_actual, month=8, day=1
                ).date() or 
                hoy > datetime(
                    año_actual+1, month=1, day=31
                ).date()
            ):
                raise PermissionDenied(
                    'No se puede acceder a esta página fuera del periodo de planificación'
                )
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator

# ----------------------------------- # HOME / DASHBOARD

@login_required
def Home(request):
    return render(request, 'classplanner/base.html', {})

# ----------------------------------- # ROLES

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class CreateRol(CreateView):
    model = Rol
    form_class = RolForm
    template_name = 'classplanner/roles/roluser_create.html'
    success_url = reverse_lazy('listrol')

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Agregado con éxito!')
        return super().form_valid(form)
    
@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch') 
class ListRol(ListView):
    model = Rol
    template_name = 'classplanner/roles/roluser_list.html'
    context_object_name = 'rol'

def FindRol(request):
    response = request.GET.get('find-rol')
    if response:
        roluser = Rol.objects.filter(name__icontains = response)
    else:
        roluser = Rol.objects.all()   
    return render(request, 'classplanner/roles/rolser_find.html', {'rol':roluser, 'response':response})

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class UpdateRol(UpdateView):
    model = Rol
    form_class = RolForm
    template_name = 'classplanner/roles/roluser_update.html'
    success_url = reverse_lazy('listrol')

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Actualizado con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class DeleteRol(DeleteView):
    model = Rol
    template_name = 'classplanner/roles/roluser_delete.html'
    context_object_name = 'rol'
    success_url = reverse_lazy('listrol')

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Eliminado con éxito!')
        return super().form_valid(form)

# ----------------------------------- # USUARIOS

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class CreateUsuario(CreateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = 'classplanner/usuarios/usercreate.html'
    success_url = reverse_lazy('userlist')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', username):
            form.add_error('username', 'El nombre de usuario solo puede contener letras y espacios.')
            return self.form_invalid(form)

        rut = form.cleaned_data.get('rut')
        try:
            validar_rut(rut)
        except ValidationError as e:
            form.add_error('rut', str(e))
            return self.form_invalid(form)

        name = form.cleaned_data.get('name')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', name):
            form.add_error('name', 'El nombre solo puede contener letras y espacios.')
            return self.form_invalid(form)
        
        last_name = form.cleaned_data.get('last_name')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', last_name):
            form.add_error('last_name', 'El apellido solo puede contener letras y espacios.')
            return self.form_invalid(form)
        
        messages.success(self.request, '¡Usuario Registrado con éxito!')
        return super().form_valid(form)
    
@method_decorator(login_required, name='dispatch') 
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class ListUsuario(ListView):
    model = Usuario
    template_name = 'classplanner/usuarios/userlist.html'
    context_object_name = 'usersys'
    def get_queryset(self):
        self.queryset = Usuario.objects.all()
        is_root = self.request.user.rol.name == 'root'
        if is_root:
            mostrar_desactivados = self.request.GET.get('change_state') == '1'
            return Usuario.objects.filter(is_active=not mostrar_desactivados)
        else: 
            # Director solo lista profesores
            if self.request.user.rol.name == 'Director' or self.request.user.rol.name == 'Administrador':
                return Usuario.objects.filter(rol__name='Docente', is_active=True)
            else:
                return Usuario.objects.filter(is_active=True)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mostrar_desactivados'] = (
            self.request.GET.get('change_state') == '1'
        )
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Director', 'Administrador'), name='dispatch')
class UpdateUsuario(UpdateView):
    model = Usuario
    form_class = UserUpdateForm
    template_name = 'classplanner/usuarios/userupdate.html'
    success_url = reverse_lazy('userlist')
    context_object_name = 'usuario'

    # Al ingresar como Director, solo muestra roles Docente y Administrador como opciones
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.rol.name == 'Director':
            form.fields['username'].disabled = True
            form.fields['name'].disabled = True
            form.fields['last_name'].disabled = True
            form.fields['email'].disabled = True
            form.fields['rut'].disabled = True
            form.fields['rol'].queryset = Rol.objects.filter(
                name__in=('Docente', 'Administrador')
            ).order_by('name')
        return form

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if (self.request.user.rol.name == 'Director' and obj.rol.name == 'Docente') or self.request.user.rol.name == 'root':
            if not obj.is_active and self.request.user.rol.name != 'root':
                raise Http404('Este usuario está desactivado')
            return obj
        elif self.request.user.rol.name == 'Director':
            raise PermissionDenied('No tiene permisos suficientes para editar este usuario')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', username):
            form.add_error('username', 'El nombre de usuario solo puede contener letras y espacios.')
            return self.form_invalid(form)

        rut = form.cleaned_data.get('rut')
        try:
            validar_rut(rut)
        except ValidationError as e:
            form.add_error('rut', str(e))
            return self.form_invalid(form)

        name = form.cleaned_data.get('name')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', name):
            form.add_error('name', 'El nombre solo puede contener letras y espacios.')
            return self.form_invalid(form)
        
        last_name = form.cleaned_data.get('last_name')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', last_name):
            form.add_error('last_name', 'El apellido solo puede contener letras y espacios.')
            return self.form_invalid(form)
        
        messages.success(self.request, '¡Usuario actualizado con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')    
@method_decorator(roles_required('root'), name='dispatch')
class DeleteUsuario(DeleteView):
    model = Usuario
    template_name = 'classplanner/usuarios/userdelete.html'
    success_url = reverse_lazy('userlist')
    context_object_name = 'usuario'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.pk == obj.pk:
            raise PermissionDenied("No puede eliminar su propio usuario")
        if not obj.is_active:
            raise Http404('Este usuario está desactivado')
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, '¡Usuario eliminado con éxito!')
        return super().form_valid(form)

# ----------------------------------- # REGISTROS

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador'), name='dispatch')
class ListRegistros(ListView):
    model = CRUDEvent
    template_name = 'classplanner/registros/registroslist.html'
    context_object_name = 'registros'

    def get_queryset(self):
        user_model = get_user_model()
        user_content_type = ContentType.objects.get_for_model(user_model)

        queryset = (
            CRUDEvent.objects
            .select_related("content_type", "user")
            .order_by("-datetime")
        )

        # Excluir update last_login
        queryset = queryset.exclude(
            Q(content_type=user_content_type) &
            Q(event_type=CRUDEvent.UPDATE) &
            Q(changed_fields__icontains="last_login")
        )

        # Filtros
        fecha_desde = self.request.GET.get("fecha_desde")
        if fecha_desde:
            queryset = queryset.filter(datetime__date__gte=fecha_desde)

        fecha_hasta = self.request.GET.get("fecha_hasta")
        if fecha_hasta:
            queryset = queryset.filter(datetime__date__lte=fecha_hasta)

        modulo = self.request.GET.get("modulo")
        if modulo:
            queryset = queryset.filter(content_type_id=modulo)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Módulos utilizados en los registros de auditoría
        context["modulos"] = (
            ContentType.objects
            .filter(
                id__in=CRUDEvent.objects.values_list(
                    "content_type_id",
                    flat=True
                )
            )
            .order_by("model")
        )

        # Mantener los valores seleccionados en el formulario
        context["fecha_desde"] = self.request.GET.get("fecha_desde", "")
        context["fecha_hasta"] = self.request.GET.get("fecha_hasta", "")
        context["modulo_seleccionado"] = self.request.GET.get("modulo", "")

        return context

# ----------------------------------- # CURSOS

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class ListCursos(ListView):
    model = Curso
    template_name = 'classplanner/cursos/cursolist.html'
    context_object_name = 'curso'

    def get_queryset(self):
        queryset = super().get_queryset()

        # mostrar horas como entero si es XX,0
        hrs = self.request.GET.get('hrs')
        for curso in queryset:
            if curso.horas_plan_total == int(curso.horas_plan_total):
                curso.horas_plan_total = floor(curso.horas_plan_total)
        return queryset

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class CreateCurso(CreateView):
    model = Curso
    form_class = CursoForm
    template_name = 'classplanner/cursos/cursocreate.html'
    success_url = reverse_lazy('cursos')

    def form_valid(self, form):
        # Validar que no exista otro curso con el mismo nivel y letra
        nivel = form.cleaned_data.get('nivel')
        letra = str(form.cleaned_data.get('letra')).upper()
        if Curso.objects.filter(nivel=nivel, letra=letra).exists():
            form.add_error('letra', 'Ya existe un curso con este nivel y letra.')
            return self.form_invalid(form)

        # Validar que no exista otro curso con la misma jefatura
        usuario_id = form.cleaned_data.get('usuario_id')
        if usuario_id and Curso.objects.filter(usuario_id=usuario_id).exists():
            form.add_error('usuario_id', 'El docente seleccionado ya tiene jefatura.')
            return self.form_invalid(form)
        
        form.instance.letra = letra
        messages.success(self.request, '¡Curso agregado con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class UpdateCurso(UpdateView):
    model = Curso
    form_class = CursoForm
    template_name = 'classplanner/cursos/cursoupdate.html'
    success_url = reverse_lazy('cursos')
    context_object_name = 'curso'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.rol.name == 'Director':
            form.fields['nivel'].disabled = True
        return form

    def form_valid(self, form):
        # Validar que no exista otro curso con el mismo nivel y letra
        nivel = form.cleaned_data.get('nivel')
        letra = str(form.cleaned_data.get('letra')).upper()
        if Curso.objects.filter(nivel=nivel, letra=letra).exclude(pk=self.object.pk).exists():
            form.add_error('letra', 'El curso que intenta agregar ya existe.')
            return self.form_invalid(form)
        
        # Validar que no exista otro curso con la misma jefatura
        usuario_id = form.cleaned_data.get('usuario_id')
        if usuario_id and Curso.objects.filter(usuario_id=usuario_id).exclude(pk=self.object.pk).exists():
            form.add_error('usuario_id', 'El docente seleccionado ya tiene jefatura.')
            return self.form_invalid(form)
        curso = form.save()
        messages.success(self.request, '¡Curso actualizado con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class DeleteCurso(DeleteView):
    model = Curso
    template_name = 'classplanner/cursos/cursodelete.html'
    context_object_name = 'curso'
    success_url = reverse_lazy('cursos')

    def form_valid(self, form):
        try: 
            super().form_valid(form)
            return messages.success(self.request, '¡Curso eliminado con éxito!')
        except RestrictedError:
            raise PermissionDenied('Este curso tiene un profesor jefe asignado, un curso no se puede eliminar si tiene un profesor jefe asignado')

# ----------------------------------- # AULAS

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class ListAula(ListView):
    model = Aula
    template_name = 'classplanner/aulas/aulalist.html'
    context_object_name = 'aulas'

    def get_queryset(self):
        return Aula.objects.prefetch_related('curso_id')

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class CreateAula(CreateView):
    model = Aula
    form_class = AulaCreateForm
    template_name = 'classplanner/aulas/aulacreate.html'
    success_url = reverse_lazy('aulas')

    def form_valid(self, form):
        messages.success(self.request, '¡Aula creada con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class UpdateAula(UpdateView):
    model = Aula
    form_class = AulaUpdateForm
    template_name = 'classplanner/aulas/aulaupdate.html'
    success_url = reverse_lazy('aulas')
    context_object_name = 'aula'

    def form_valid(self, form):
        messages.success(self.request, '¡Aula actualizada con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class DeleteAula(DeleteView):
    model = Aula
    template_name = 'classplanner/aulas/auladelete.html'
    success_url = reverse_lazy('aulas')
    context_object_name = 'aula'

    def form_valid(self, form):
        messages.success(self.request, '¡Aula eliminada con éxito!')
        return super().form_valid(form)

# ----------------------------------- # ESTUDIANTES

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class ListEstudiantes(ListView):
    model = Estudiante
    template_name = 'classplanner/estudiantes/estudianteslist.html'
    context_object_name = 'estudiantes'

    def get_queryset(self):
        is_root = self.request.user.rol.name == 'root'
        if is_root:
            mostrar_desactivados = self.request.GET.get('change_state') == '1'
            return Estudiante.objects.filter(is_active=not mostrar_desactivados)
        else: return Estudiante.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mostrar_desactivados'] = (
            self.request.GET.get('change_state') == '1'
        )
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class CreateEstudiante(CreateView):
    model = Estudiante
    form_class = EstudiantesCreateForm
    template_name = 'classplanner/estudiantes/estudiantescreate.html'
    success_url = reverse_lazy('estudiantes')

    def form_valid(self, form):
        rut = form.cleaned_data.get('rut')
        try:
            validar_rut(rut)
        except ValidationError as e:
            form.add_error('rut', str(e).removeprefix("['").removesuffix("']"))
            return self.form_invalid(form)

        nombre = form.cleaned_data.get('nombre')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', nombre):
            form.add_error('nombre', 'El nombre solo puede contener letras y espacios.')
            return self.form_invalid(form)

        apellido_p = form.cleaned_data.get('apellido_p')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', apellido_p):
            form.add_error('apellido_p', 'El apellido solo puede contener letras y espacios.')
            return self.form_invalid(form)
        apellido_m = form.cleaned_data.get('apellido_m')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', apellido_m):
            form.add_error('apellido_m', 'El apellido solo puede contener letras y espacios.')
            return self.form_invalid(form)

        form.instance.nombre = form.cleaned_data['nombre'].title()
        form.instance.apellido_p = form.cleaned_data['apellido_p'].capitalize()
        form.instance.apellido_m = form.cleaned_data['apellido_m'].capitalize()
        messages.success(self.request, '¡Estudiante registrado con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class UpdateEstudiante(UpdateView):
    model = Estudiante
    form_class = EstudiantesUpdateForm
    template_name = 'classplanner/estudiantes/estudiantesupdate.html'
    success_url = reverse_lazy('estudiantes')
    context_object_name = 'estudiantes'

    def get_object(self, queryset=None):
        e = get_object_or_404(
            Estudiante,
            rut=self.kwargs['rut'],
            curso_id_id=self.kwargs['curso_id']
        )
        if not e.is_active and self.request.user.rol.name != 'root':
            raise Http404('Estudiante no encontrado')
        
        return e

    def form_valid(self, form):
        nombre = form.cleaned_data.get('nombre')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', nombre):
            form.add_error('nombre', 'El nombre solo puede contener letras y espacios.')
            return self.form_invalid(form)

        apellido_p = form.cleaned_data.get('apellido_p')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', apellido_p):
            form.add_error('apellido_p', 'El apellido solo puede contener letras y espacios.')
            return self.form_invalid(form)
        apellido_m = form.cleaned_data.get('apellido_m')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', apellido_m):
            form.add_error('apellido_m', 'El apellido solo puede contener letras y espacios.')
            return self.form_invalid(form)
        
        Estudiante.objects.filter(
            rut=self.kwargs['rut'],
            curso_id_id=self.kwargs['curso_id']
        ).update(
            nombre=nombre.title(),
            apellido_p=apellido_p.capitalize(),
            apellido_m=apellido_m.capitalize(),
            curso_id=form.cleaned_data['curso_id'],
        )
        messages.success(self.request, '¡Estudiante actualizado con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class DeleteEstudiante(DeleteView):
    model = Estudiante
    template_name = 'classplanner/estudiantes/estudiantesdelete.html'
    success_url = reverse_lazy('estudiantes')
    context_object_name = 'estudiante'

    def get_object(self, queryset=None):
        e = get_object_or_404(
            Estudiante,
            rut=self.kwargs['rut'],
            curso_id_id=self.kwargs['curso_id']
        )
        if not e.is_active:
            raise Http404('El estudiante está desactivado')
        
        return e

    def form_valid(self, form):
        messages.success(self.request, '¡Estudiante eliminado con éxito!')
        return super().form_valid(form)

# ----------------------------------- # PROMEDIOS

MIN_NOTAS_PROMEDIO = 2

def calcular_promedios(notas):
    por_asignatura = {}

    for nota in notas:
        item = por_asignatura.setdefault(nota.asignatura_id_id, {
            'asignatura': nota.asignatura_id,
            'valores': [],
        })

        if nota.nota is not None:
            item['valores'].append(nota.nota)

    resultados = []

    for item in por_asignatura.values():
        valores = item['valores']
        media = sum(valores) / len(valores) if len(valores) >= MIN_NOTAS_PROMEDIO else None
        resultados.append({
            'asignatura': item['asignatura'],
            'cantidad': len(valores),
            'media': media,
            'promedio': None if media is None else round(media, 1),
        })

    return resultados

def promedio_final(promedios):
    medias = [p['media'] for p in promedios if p['media'] is not None]
    return round(sum(medias) / len(medias), 1) if medias else 0

def actualizar_promedio_estudiante(rut):
    notas = PromedioAsignatura.objects.filter(estudiante_id=rut).select_related('asignatura_id')
    final = promedio_final(calcular_promedios(notas))
    Estudiante.objects.filter(rut=rut).update(promedio=final)

@login_required
@roles_required('root', 'Administrador', 'Director', 'Docente')
def ExportarNotas(request, rut, export):
    porcentaje_asis = request.GET.get('asistencia')
    observacion = request.GET.get('observacion')
    notas_estudiante_model = PromedioAsignatura.objects.all()

    if Estudiante.objects.filter(rut=rut).exists():
        if not export:
            raise BadRequest('No se pudo completar la exportación')

        notas_estudiante = notas_estudiante_model.filter(estudiante_id__rut=rut)
        notas = [
            nota for nota in notas_estudiante
        ]
        if not notas:
            raise BadRequest('No existen notas para exportar')

        return _exportar_notas_pdf(
            notas_estudiante,
            Estudiante.objects.filter(rut=rut),
            export,
            porcentaje_asis,
            observacion,
        )
    else: raise Http404('El estudiante no existe')

class PromedioAsignaturaMixin:
    def get_estudiante(self):
        if not hasattr(self, '_estudiante'):
            if 'rut' in self.kwargs:
                self._estudiante = get_object_or_404(
                    Estudiante,
                    rut=self.kwargs['rut'],
                    curso_id=self.kwargs['curso_id'],
                )
            else:
                self._estudiante = get_object_or_404(Estudiante, rut=self.object.estudiante_id_id)

        return self._estudiante

    def get_success_url(self):
        estudiante = self.get_estudiante()
        return reverse('promedioasignatura', kwargs={'rut': estudiante.rut, 'curso_id': estudiante.curso_id_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estudiante'] = self.get_estudiante()
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class ListPromedioAsignatura(PromedioAsignaturaMixin, ListView):
    template_name = 'classplanner/promedioasignatura/promedioasignaturalist.html'
    context_object_name = 'notas'

    def get_queryset(self):
        estudiante = self.get_estudiante()
        if estudiante.is_active == False:
            raise Http404('No se pueden editar las notas de un estudiante desactivado')
        return PromedioAsignatura.objects.filter(
            estudiante_id=estudiante.rut,
        ).select_related('asignatura_id').order_by('asignatura_id__ident', 'id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promedios = calcular_promedios(context['notas'])
        context['promedios'] = promedios
        context['promedio_final'] = promedio_final(promedios)
        context['con_promedio'] = sum(1 for p in promedios if p['media'] is not None)
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class CreatePromedioAsignatura(PromedioAsignaturaMixin, CreateView):
    model = PromedioAsignatura
    form_class = PromedioAsignaturaCreateForm
    template_name = 'classplanner/promedioasignatura/promedioasignaturacreate.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['estudiante'] = self.get_estudiante()
        if self.get_estudiante().is_active == False:
            raise Http404('No se pueden editar las notas de un estudiante desactivado')
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        actualizar_promedio_estudiante(self.object.estudiante_id_id)
        messages.success(self.request, '¡Nota registrada con éxito!')
        return response

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class UpdatePromedioAsignatura(PromedioAsignaturaMixin, UpdateView):
    model = PromedioAsignatura
    form_class = PromedioAsignaturaUpdateForm
    template_name = 'classplanner/promedioasignatura/promedioasignaturaupdate.html'
    context_object_name = 'nota'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['estudiante'] = self.get_estudiante()
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        actualizar_promedio_estudiante(self.object.estudiante_id_id)
        messages.success(self.request, '¡Nota actualizada con éxito!')
        return response

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class DeletePromedioAsignatura(PromedioAsignaturaMixin, DeleteView):
    model = PromedioAsignatura
    template_name = 'classplanner/promedioasignatura/promedioasignaturadelete.html'
    context_object_name = 'nota'

    def form_valid(self, form):
        rut = self.object.estudiante_id_id
        response = super().form_valid(form)
        actualizar_promedio_estudiante(rut)
        messages.success(self.request, '¡Nota eliminada con éxito!')
        return response

# ----------------------------------- # ASIGNATURAS

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class ListAsignatura(ListView):
    model = Asignatura
    template_name = 'classplanner/asignaturas/asignaturalist.html'
    context_object_name = 'asignatura'

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador'), name='dispatch')
class CreateAsignatura(UserPassesTestMixin, CreateView):
    model = Asignatura
    form_class = AsignaturasCreateForm
    template_name = 'classplanner/asignaturas/asignaturacreate.html'
    success_url = reverse_lazy('asignaturas')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        form.instance.ident = form.cleaned_data['ident'].strip().upper()
        form.instance.ident = form.cleaned_data['ident'].replace(" ","")
        form.instance.descripcion = form.cleaned_data['descripcion'].capitalize()
        messages.success(self.request, '¡Asignatura creada con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class UpdateAsignatura(UpdateView):
    model = Asignatura
    form_class = AsignaturaUpdateForm
    template_name = 'classplanner/asignaturas/asignaturaupdate.html'
    success_url = reverse_lazy('asignaturas')
    context_object_name = 'asignatura'

    def form_valid(self, form):
        form.instance.ident = form.cleaned_data['ident'].strip().upper()
        form.instance.ident = form.cleaned_data['ident'].replace(" ","")
        form.instance.descripcion = form.cleaned_data['descripcion'].capitalize()
        messages.success(self.request, '¡Asignatura actualizada con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador'), name='dispatch')
class DeleteAsignatura(DeleteView):
    model = Asignatura
    template_name = 'classplanner/asignaturas/asignaturadelete.html'
    success_url = reverse_lazy('asignaturas')
    context_object_name = 'asignatura'

    def form_valid(self, form):
        try: 
            super().form_valid(form)
            return messages.success(self.request, '¡Asignatura eliminada con éxito!')
        except RestrictedError:
            raise PermissionDenied(
                'Esta asignatura está asignada en uno o más planes de estudio. ' \
                'Procure reorganizar las horas de los planes de estudio antes de continuar con la eliminación')
    
# ----------------------------------- # PLAN DE ESTUDIO

@login_required
@roles_required('root', 'Administrador', 'Director')
def ExportarPlanes(request, export):
    if export == 'excel':
        if request.method != 'POST':
            raise BadRequest('Solicitud de exportación inválida')

        planes_seleccionados = request.POST.getlist('plan_checkbox')
        if 'exportar_todo' in planes_seleccionados:
            return exportar_planes(PlanDeEstudio.objects.all(), export)

        cursos_seleccionados = [
            curso_id for curso_id in planes_seleccionados
            if curso_id != 'exportar_todo'
        ]
        if not cursos_seleccionados:
            raise BadRequest('Seleccione planes válidos para exportar')

        planes = PlanDeEstudio.objects.filter(curso_id__in=cursos_seleccionados)
        return exportar_planes(planes, export)
    
    elif export == 'pdf':
        if request.method != 'POST':
                raise BadRequest('Solicitud de exportación inválida')
    
        planes_seleccionados = request.POST.getlist('plan_checkbox')
        if 'exportar_todo' in planes_seleccionados:
            return exportar_planes(PlanDeEstudio.objects.all(), export)

        cursos_seleccionados = [
            curso_id for curso_id in planes_seleccionados
            if curso_id != 'exportar_todo'
        ]
        if not cursos_seleccionados:
            raise BadRequest('Seleccione planes válidos para exportar')

        planes = PlanDeEstudio.objects.filter(curso_id__in=cursos_seleccionados)
        return exportar_planes(planes, export)

@login_required
@roles_required('root', 'Administrador', 'Director')
def ListPlanDeEstudio(request):
    cursosModel = Curso.objects.all()
    plandeestudio = PlanDeEstudio.objects.all()

    cursos = []
    planes = {}
    for p in plandeestudio.values_list('curso_id', flat=True).distinct():
        if p == cursosModel.filter(id=p).first().id:
            c = int(cursosModel.filter(id=p).first().id)
            cursos.append(c)

    cursos_ordenados = list(
        cursosModel.filter(id__in=cursos).order_by('nivel').values_list('id', 'nivel')
    )
    cursos_ordenados.sort(
        key=lambda curso: (
            0 if str(curso[1]).endswith('°B')
            else 1 if str(curso[1]).endswith('°M')
            else 2
        )
    )

    for c, _nivel in cursos_ordenados:
        curso_update = str(cursosModel.filter(id=c).first())
        curso_update_id = cursosModel.filter(id=c).first().id
        asignaturas_update = list(
            plandeestudio.filter(curso_id=c).values_list('asignatura_id__nombre','hrs_asignatura')
        )
        horas = sum(plandeestudio.filter(curso_id=c).values_list('hrs_asignatura', flat=True))
        planes.update({f"{c}": [curso_update, asignaturas_update, horas, curso_update_id]})

    context = {'plandeestudio': [planes[str(c)] for c, _nivel in cursos_ordenados]}

    return render(request, 'classplanner/plandeestudio/plandeestudiolist.html', context)

@login_required
@roles_required('root', 'Administrador', 'Director')
@periodo_planificacion_required()
def CreatePlanDeEstudio(request):
    asignaturas = Asignatura.objects.all()
    cursos = Curso.objects.all()
    context = {'form': PlanDeEstudioCreateForm(), 'asignaturas': asignaturas, 'cursos': cursos}

    return render(request, 'classplanner/plandeestudio/plandeestudiocreate.html', context)

@login_required
@roles_required('root', 'Administrador', 'Director')
@periodo_planificacion_required()
def CreatePlanDeEstudioForm(request): # hacer validacion hrs plan curso >= total horas ingresadas (solo está en pde.js)
    max_forms = 7
    curso_id = request.POST.get('curso_id')
    horas = request.POST.getlist('hrs_asignatura')
    asignaturas = request.POST.getlist('asignatura_id')
    if request.method == 'POST':
        planes = []
        form = PlanDeEstudioCreateForm(request.POST)
        curso_ids = list(PlanDeEstudio.objects.values_list('curso_id', flat=True))
        
        for raw_curso_id in request.POST.getlist('curso_id'):
            if raw_curso_id in ('', None):
                continue
            try:
                curso_ids.append(int(raw_curso_id))
            except (TypeError, ValueError):
                curso_ids.append(raw_curso_id)
                form.add_error(None, 'Uno de los cursos ingresados no es válido')
                return render(
                    request,
                    'classplanner/plandeestudio/plandeestudioformerror.html',
                    {'form': form},
                )
        print(f"curso_ids: {curso_ids}\ncurso_ids[:-1]: {curso_ids[:-1]}\nplanes: {planes}")

        if not horas or len(horas) != len(asignaturas):
            form.add_error(None, 'Por favor, complete todos los campos')
            return render(
                request,
                'classplanner/plandeestudio/plandeestudioformerror.html',
                {'form': form},
            )
        else:
            print("campos completos")
            curso_repetido = int(curso_id) in curso_ids[:-1] # probar con mas de 1 form
            curso_ids_validos = [curso_id for curso_id in curso_ids if isinstance(curso_id, int)]
            cursos_existentes = set(
                Curso.objects.filter(pk__in=curso_ids_validos).values_list('pk', flat=True)
            )
            cursos_invalidos = [curso_id for curso_id in curso_ids_validos if curso_id not in cursos_existentes]
            print(f"curso actual: {curso_id}\ncurso repetido: {curso_repetido}\ncursos_invalidos: {cursos_invalidos}")

            for hrs, asignatura_id in zip(horas, asignaturas):
                item_form = PlanDeEstudioCreateForm({
                    'curso_id': curso_id,
                    'hrs_asignatura': hrs,
                    'asignatura_id': asignatura_id,
                }) 
                

                if not curso_ids_validos or curso_repetido or cursos_invalidos:
                    if curso_repetido:
                        form.add_error(None, 'No puede crear 2 planes de estudio para un mismo curso')
                    else:
                        form.add_error(None, 'Uno de los cursos ingresados no es válido')
                    return render(
                        request,
                        'classplanner/plandeestudio/plandeestudioformerror.html',
                        {'form': form},
                    )

                if item_form.is_valid():
                    print(hrs)
                    if int(hrs) > 0:
                        planes.append(item_form.cleaned_data)
                else:
                    form = PlanDeEstudioCreateForm(request.POST)
                    form.add_error(None, 'Datos inválidos')
                    form = item_form
                    break
            else:
                with transaction.atomic():
                    PlanDeEstudio.objects.bulk_create(
                        [PlanDeEstudio(**plan) for plan in planes]
                    )
                messages.success(
                    request,
                    '¡Planes de estudio añadidos con éxito!'
                )
                response = render(
                    request,
                    'classplanner/plandeestudio/plandeestudioform.html',
                )
                response['X-Planes-Guardados'] = 'true'
                return response
    elif request.method == 'GET':
        try:
            forms_count = int(request.GET.get('forms_count', 0))
        except (TypeError, ValueError):
            forms_count = 0

        if forms_count >= max_forms:
            messages.error(
                request,
                'Solo se pueden agregar los planes de estudio de 7 cursos a la vez.'
            )
            return render(
                request,
                'classplanner/plandeestudio/plandeestudioform.html',
                {'form': None}
            )

        form = PlanDeEstudioCreateForm()

    for i in horas:
        print(i)
        if int(i) > 8:
            form = PlanDeEstudioCreateForm(request.POST)
            form.add_error(None, 'Selecciona una asignatura e indica sus horas.')

    if request.method == 'POST' and form.errors:
        return render(
            request,
            'classplanner/plandeestudio/plandeestudioformerror.html',
            {'form': form},
        )

    return render(request, 'classplanner/plandeestudio/plandeestudioform.html', {'form': form})

@login_required
@roles_required('root', 'Administrador', 'Director')
@periodo_planificacion_required()
def UpdatePlanDeEstudio(request, pk=None):
    curso = Curso.objects.get(pk=pk)
    horasCurso = int(curso.horas_plan_total)
    pdeModel = PlanDeEstudio.objects.all()
    asignaturasModel = Asignatura.objects.all()
    asignaturasSelected = list(pdeModel.filter(curso_id=curso.id).values_list('asignatura_id__ident','hrs_asignatura'))
    pdes = list(pdeModel.filter(curso_id=curso.id).values_list('pk', 'asignatura_id__ident'))
    print("pdes: ",pdes)
    context = {
        'form': PlanDeEstudioUpdateForm(),
        'asignaturas': asignaturasModel,
        'asignaturasSelected': asignaturasSelected,
        'curso': curso,
        'horasCurso': horasCurso,
        'planesdeestudio': pdes,
    }

    return render(request, 'classplanner/plandeestudio/plandeestudioupdate.html', context)

@login_required
@roles_required('root', 'Administrador', 'Director')
@periodo_planificacion_required()
def UpdatePlanDeEstudioForm(request, pk=None): # hacer validacion hrs plan curso >= total horas ingresadas (solo está en pde.js)
    curso = Curso.objects.get(pk=pk)
    planes = request.POST.getlist('pde_id')
    horas = request.POST.getlist('hrs_asignatura')
    asignaturas = request.POST.getlist('asignatura_id')
    
    if request.method == 'POST':
        form = PlanDeEstudioUpdateForm(request.POST)

        if not horas or len(horas) != len(asignaturas):
            print("Por favor, complete todos los campos")
            form.add_error(None, 'Por favor, complete todos los campos')
            return render(
                request,
                'classplanner/plandeestudio/plandeestudioformerror.html',
                {'form': form},
            )
        else:
            # Obtener planes del curso actual
            planes_existentes = {
                str(plan.pk): plan
                for plan in PlanDeEstudio.objects.filter(curso_id=curso)
            }

            planesUpdate = []
            planesCreate = []
            planesDelete = []
            print("planes: ", planes,"\nhoras: ", horas,"\nasigns: ",asignaturas)
            for plan_id, hrs, asignatura_id in zip(
                planes, horas, asignaturas
            ):
                plan = planes_existentes.get(plan_id)

                #print("planes existentes: ",planes_existentes,"\nplan loop: ",plan)
                print("plan loop: ",plan)
                if plan is None and not plan_id == "":
                    form.add_error(None, 'Ocurrió un error, no se pudo validar el plan seleccionado.')
                    return render(
                        request,
                        'classplanner/plandeestudio/plandeestudioformerror.html',
                        {'form': form}
                    )

                item_form = PlanDeEstudioUpdateForm({
                    'curso_id': curso.pk,
                    'hrs_asignatura': hrs,
                    'asignatura_id': asignatura_id,
                })

                if not item_form.is_valid():
                    item_form.add_error(None, 'Datos inválidos.')
                    return render(
                        request,
                        'classplanner/plandeestudio/plandeestudioformerror.html',
                        {'form': item_form}
                    )

                # Modificar obj
                if plan is None:
                    nuevoPlan = PlanDeEstudio(
                        curso_id=curso,
                        hrs_asignatura=item_form.cleaned_data['hrs_asignatura'],
                        asignatura_id=item_form.cleaned_data['asignatura_id'],
                    )
                    if not float(nuevoPlan.hrs_asignatura) < 1:
                        planesCreate.append(nuevoPlan)
                elif float(hrs) < 1:
                    planesDelete.append(plan)
                else:
                    plan.hrs_asignatura = item_form.cleaned_data['hrs_asignatura']
                    plan.asignatura_id = item_form.cleaned_data['asignatura_id']

                    if not float(hrs) < 1:
                        planesUpdate.append(plan)

            with transaction.atomic():
                print("\n-----\nplanesUpdate: ", planesUpdate,"\nplanesDelete: ",planesDelete,"\nplanesCreate: ",planesCreate,"\n-----\n")
                for plan in planes_existentes.values():
                    if plan not in planesDelete and plan not in planesUpdate and plan not in planesDelete:
                        planesDelete.append(plan)
                        
                PlanDeEstudio.objects.bulk_update(
                    planesUpdate,
                    ['hrs_asignatura', 'asignatura_id']
                )
                if planesCreate != []:
                    PlanDeEstudio.objects.bulk_create(planesCreate)
                if planesDelete != []:
                    PlanDeEstudio.objects.filter(
                        pk__in=[plan.pk for plan in planesDelete]
                    ).delete()

            response = render(
                request,
                'classplanner/plandeestudio/plandeestudioupdateform.html',
            )
            response['X-Planes-Guardados'] = 'true'
            response['X-Planes-Guardados-Msg'] = '¡Plan de estudio actualizado con éxito!'
            return response
        
    elif request.method == 'GET':
        form = PlanDeEstudioCreateForm()

    if request.method == 'POST' and form.errors:
        return render(
            request,
            'classplanner/plandeestudio/plandeestudioformerror.html',
            {'form': form},
        )

    return render(request, 'classplanner/plandeestudio/plandeestudioupdateform.html', {'form': form})

# ----------------------------------- # CARGAS HORARIAS

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class ListCargaHoraria(ListView):
    model = CargaHoraria
    template_name = 'classplanner/cargahoraria/cargahorarialist.html'
    context_object_name = 'cargahoraria'

DIAS_CODIGO = {1: 'L', 2: 'M', 3: 'X', 4: 'J', 5: 'V'}
def es_recreo(inicio, termino):
    # deteccion de un bloque correspondiente a recreo; detecta si dura menos de 30 min
    duracion = (datetime.combine(date.today(), termino) - datetime.combine(date.today(), inicio)).total_seconds() / 60
    return duracion < 30

def obtener_bloques_por_jornada():
    vistos = set()
    bloques_jm, bloques_jt = [], []

    for b in Bloque.objects.order_by('hora_inicio', 'hora_termino'):
        clave = (b.hora_inicio, b.hora_termino)

        if clave in vistos:
            continue
        vistos.add(clave)

        item = {
            'hora_inicio': b.hora_inicio,
            'hora_termino': b.hora_termino,
            'es_recreo': es_recreo(b.hora_inicio, b.hora_termino),
        }

        if time(7, 45) <= b.hora_inicio < time(13, 30):
            bloques_jm.append(item)
        elif time(14, 0) <= b.hora_inicio < time(19, 0):
            bloques_jt.append(item)

    return {'JM': bloques_jm, 'JT': bloques_jt}

def leer_casillas(post, bloques_por_jornada):
    casillas, errores = [], []

    for clave in post:
        if not clave.startswith('asignatura_'):
            continue

        _, jornada, fila, dia = clave.split('_')
        asignatura_id = post.get(clave)
        curso_id = post.get(f'curso_{jornada}_{fila}_{dia}')

        if not asignatura_id and not curso_id:
            continue  # casilla vacía
        if not (asignatura_id and curso_id):
            errores.append('Hay una casilla con asignatura pero sin curso (o al revés).')
            continue

        bloque = bloques_por_jornada[jornada][int(fila) - 1]  # fila = forloop.counter (desde 1)

        casillas.append({
            'hora_inicio': bloque['hora_inicio'],
            'hora_termino': bloque['hora_termino'],
            'dia': DIAS_CODIGO[int(dia)],
            'asignatura_id': int(asignatura_id),
            'curso_id': int(curso_id),
        })

    return casillas, errores

@login_required
@roles_required('root', 'Administrador', 'Director')
def CreateCargaHoraria(request):
    bloques_por_jornada = obtener_bloques_por_jornada()

    if request.method == 'POST':
        errores = []

        # Docente
        docente = Usuario.objects.filter(
            id=request.POST.get('usuario_id') or 0, rol__name='Docente', is_active=True
        ).first()

        if not docente:
            errores.append('Selecciona un docente válido.')
        elif CargaHoraria.objects.filter(usuario_id=docente).exists():
            errores.append(f'{docente} ya tiene una carga horaria creada.')

        # Horas de contrato
        try:
            hrs_contrato = float(request.POST.get('hrs_contrato', '').replace(',', '.'))
            if hrs_contrato <= 0:
                raise ValueError
        except ValueError:
            hrs_contrato = None
            errores.append('Las horas de contrato deben ser un número mayor que 0.')

        # Casillas 
        casillas, errores_casillas = leer_casillas(request.POST, bloques_por_jornada)
        errores += errores_casillas

        if not casillas:
            errores.append('Asigna al menos una hora de clase.')

        hrs_aula = len(casillas) # cantidad de bloques asignados
        if hrs_contrato and hrs_aula > hrs_contrato:
            errores.append(f'Asignaste {hrs_aula} horas de aula y el contrato es de {hrs_contrato:g} horas.')

        if casillas: # resolver objetos reales (valida que existan)
            asignaturas_db = Asignatura.objects.in_bulk({c['asignatura_id'] for c in casillas})
            cursos_db = Curso.objects.in_bulk({c['curso_id'] for c in casillas})

            bloques_db = {
                (b.dia, b.hora_inicio, b.hora_termino): b
                for b in Bloque.objects.filter(
                    hora_inicio__in={c['hora_inicio'] for c in casillas}
                )
            }

            for c in casillas:
                c['asignatura'] = asignaturas_db.get(c['asignatura_id'])
                c['curso'] = cursos_db.get(c['curso_id'])
                c['bloque'] = bloques_db.get((c['dia'], c['hora_inicio'], c['hora_termino']))

                if not (c['asignatura'] and c['curso']):
                    errores.append('Una asignatura o curso seleccionado ya no existe.')
                    break

                if not c['bloque']:
                    errores.append(f'No existe el bloque {c["dia"]} {c["hora_inicio"]:%H:%M} en la base de datos.')
                    break

                # deteccion de conflicto si el curso ya tiene clase en ese bloque con otro docente
                conflicto = (
                    BloqueDeClase.objects
                    .filter(curso_id=c['curso'], bloque_id=c['bloque'])
                    .select_related('carga_horaria_id__usuario_id')
                    .first()
                )

                if conflicto:
                    errores.append(
                        f'El curso {c["curso"]} ya tiene clase el {c["bloque"].get_dia_display()} '
                        f'a las {c["hora_inicio"]:%H:%M} con {conflicto.carga_horaria_id.usuario_id}.'
                    )

        if errores:
            for e in dict.fromkeys(errores): 
                messages.error(request, e)
        else:
            with transaction.atomic():
                carga = CargaHoraria.objects.create(
                    usuario_id=docente,
                    hrs_contrato=hrs_contrato,
                    hrs_aula=hrs_aula,
                    hrs_cd=0,
                    hrs_aa=0,
                )

                BloqueDeClase.objects.bulk_create([
                    BloqueDeClase(
                        carga_horaria_id=carga,
                        bloque_id=c['bloque'],
                        asignatura_id=c['asignatura'],
                        curso_id=c['curso'],
                    )
                    for c in casillas
                ])

            messages.success(request, 'Carga horaria creada correctamente.')
            return redirect('cargashorarias')

    dias = [(1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'), (4, 'Jueves'), (5, 'Viernes')]

    docentes = (
        Usuario.objects
        .filter(rol__name='Docente', is_active=True)
        .select_related('rol')
        .order_by('name', 'last_name')
    )

    return render(request, 'classplanner/cargahoraria/cargahorariacreate.html', {
        'bloques_jm': bloques_por_jornada['JM'],
        'bloques_jt': bloques_por_jornada['JT'],
        'dias': dias,
        'cursos': Curso.objects.all(),
        'asignaturas': Asignatura.objects.all(),
        'docentes': docentes,
    })

# ----------------------------------- #

def custom_logout(request):
    logout(request)
    return redirect('login') 