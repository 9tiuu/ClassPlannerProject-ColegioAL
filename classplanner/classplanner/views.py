from django.forms import ValidationError
from django.http import request, Http404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views import View
from django.contrib import messages
from datetime import datetime
import re
from math import floor
from collections import defaultdict

from easyaudit.models import CRUDEvent
from .models import Rol, Usuario, Asignatura, PlanDeEstudio, Curso, PlanDiferencial, Estudiante, Aula, Nota
from .forms import (
    RolForm, UsuarioForm, UserUpdateForm,
    PlanDeEstudioCreateForm, PlanDeEstudioUpdateForm,
    CursoForm, AsignaturasCreateForm, AsignaturaUpdateForm,
    AulaCreateForm, AulaUpdateForm,
    PlanDiferencialCreateForm, PlanDiferencialUpdateForm,
    EstudiantesCreateForm, EstudiantesUpdateForm,
    NotasCreateForm, NotasUpdateForm
)

from django.contrib.auth import logout, get_user_model
from django.shortcuts import redirect
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from functools import wraps

# Create your views here.

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
        messages.success(self.request, '¡Rol Agregado con exito!')
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
        messages.success(self.request, '¡Rol Actualizado con exito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class DeleteRol(DeleteView):
    model = Rol
    template_name = 'classplanner/roles/roluser_delete.html'
    context_object_name = 'rol'
    success_url = reverse_lazy('listrol')

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Eliminado con exito!')
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
        
        messages.success(self.request, '¡Usuario Registrado con exito!')
        return super().form_valid(form)
    
@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class ListUsuario(ListView):
    model = Usuario
    template_name = 'classplanner/usuarios/userlist.html'
    context_object_name = 'usersys'

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class UpdateUsuario(UpdateView):
    model = Usuario
    form_class = UserUpdateForm
    template_name = 'classplanner/usuarios/userupdate.html'
    success_url = reverse_lazy('userlist')
    context_object_name = 'usuario'

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
        
        messages.success(self.request, '¡Usuario Registrado con exito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')    
@method_decorator(roles_required('root'), name='dispatch')
class DeleteUsuario(DeleteView):
    model = Usuario
    template_name = 'classplanner/usuarios/userdelete.html'
    success_url = reverse_lazy('userlist')
    context_object_name = 'usuario'

    def form_valid(self, form):
        messages.success(self.request, '¡Usuario Eliminado con exito!')
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

    def form_valid(self, form):
        # Validar que no exista otro curso con el mismo nivel y letra
        nivel = form.cleaned_data.get('nivel')
        letra = str(form.cleaned_data.get('letra')).upper()
        if Curso.objects.filter(nivel=nivel, letra=letra).exclude(pk=self.object.pk).exists():
            form.add_error('letra', 'Ya existe un curso con este nivel y letra.')
            return self.form_invalid(form)
        
        # Validar que no exista otro curso con la misma jefatura
        usuario_id = form.cleaned_data.get('usuario_id')
        if usuario_id and Curso.objects.filter(usuario_id=usuario_id).exclude(pk=self.object.pk).exists():
            form.add_error('usuario_id', 'El docente seleccionado ya tiene jefatura.')
            return self.form_invalid(form)
        curso = form.save()
        messages.success(self.request, '¡Curso actualizado con exito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class DeleteCurso(DeleteView):
    model = Curso
    template_name = 'classplanner/cursos/cursodelete.html'
    context_object_name = 'curso'
    success_url = reverse_lazy('cursos')

    def form_valid(self, form):
        messages.success(self.request, '¡Curso eliminado con exito!')
        return super().form_valid(form)

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
        messages.success(self.request, '¡Estudiante registrado con exito!')
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
        if not e.is_active:
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
        
        form.instance.nombre = form.cleaned_data['nombre'].title()
        form.instance.apellido_p = form.cleaned_data['apellido_p'].capitalize()
        form.instance.apellido_m = form.cleaned_data['apellido_m'].capitalize()
        messages.success(self.request, '¡Estudiante actualizado con exito!')
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
            raise Http404('Estudiante no encontrado')
        
        return e

    def form_valid(self, form):
        messages.success(self.request, '¡Estudiante eliminado con exito!')
        return super().form_valid(form)

# ----------------------------------- # NOTAS

def calcular_promedios(notas):
    por_asignatura = defaultdict(list)
    asignaturas = {}

    for nota in notas:
        por_asignatura[nota.asignatura_id_id].append(float(nota.nota))
        asignaturas[nota.asignatura_id_id] = nota.asignatura_id

    resultados = []

    for asignatura_id, valores in por_asignatura.items():
        media = sum(valores) / len(valores)
        resultados.append({
            'asignatura': asignaturas[asignatura_id],
            'cantidad': len(valores),
            'media': media,
            'promedio': round(media, 1),
            'provisorio': len(valores) < 4,
        })

    return resultados

def promedio_final(promedios):
    if not promedios:
        return 0

    return round(sum(p['media'] for p in promedios) / len(promedios), 1)

def actualizar_promedio_estudiante(rut, curso_id):
    notas = Nota.objects.filter(
        estudiante_rut=rut,
        estudiante_curso_id=curso_id,
    ).select_related('asignatura_id')

    final = promedio_final(calcular_promedios(notas))
    Estudiante.objects.filter(rut=rut, curso_id=curso_id).update(promedio=final)

class NotaEstudianteMixin:
    def get_estudiante(self):
        if not hasattr(self, '_estudiante'):
            if 'rut' in self.kwargs:
                rut, curso_id = self.kwargs['rut'], self.kwargs['curso_id']
            else:
                rut, curso_id = self.object.estudiante_rut, self.object.estudiante_curso_id

            self._estudiante = get_object_or_404(Estudiante, rut=rut, curso_id=curso_id)

        return self._estudiante

    def get_success_url(self):
        estudiante = self.get_estudiante()
        return reverse('notasestudiante', kwargs={'rut': estudiante.rut, 'curso_id': estudiante.curso_id_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estudiante'] = self.get_estudiante()
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class ListNotasEstudiante(NotaEstudianteMixin, ListView):
    template_name = 'classplanner/notas/notaslist.html'
    context_object_name = 'notas'

    def get_queryset(self):
        estudiante = self.get_estudiante()
        return Nota.objects.filter(
            estudiante_rut=estudiante.rut,
            estudiante_curso_id=estudiante.curso_id_id,
        ).select_related('asignatura_id').order_by('asignatura_id__ident', 'id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promedios = calcular_promedios(context['notas'])
        context['promedios'] = promedios
        context['promedio_final'] = promedio_final(promedios)
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class CreateNota(NotaEstudianteMixin, CreateView):
    model = Nota
    form_class = NotasCreateForm
    template_name = 'classplanner/notas/notascreate.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['estudiante'] = self.get_estudiante()
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        actualizar_promedio_estudiante(self.object.estudiante_rut, self.object.estudiante_curso_id)
        messages.success(self.request, '¡Nota registrada con éxito!')
        return response

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class UpdateNota(NotaEstudianteMixin, UpdateView):
    model = Nota
    form_class = NotasUpdateForm
    template_name = 'classplanner/notas/notasupdate.html'
    context_object_name = 'nota'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['estudiante'] = self.get_estudiante()
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        actualizar_promedio_estudiante(self.object.estudiante_rut, self.object.estudiante_curso_id)
        messages.success(self.request, '¡Nota actualizada con éxito!')
        return response

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director', 'Docente'), name='dispatch')
class DeleteNota(NotaEstudianteMixin, DeleteView):
    model = Nota
    template_name = 'classplanner/notas/notasdelete.html'
    context_object_name = 'nota'

    def form_valid(self, form):
        rut, curso_id = self.object.estudiante_rut, self.object.estudiante_curso_id
        response = super().form_valid(form)
        actualizar_promedio_estudiante(rut, curso_id)
        messages.success(self.request, '¡Nota eliminada con éxito!')
        return response

# ----------------------------------- # PLAN DIFERENCIAL

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class ListPlanDiferencial(ListView):
    model = PlanDiferencial
    template_name = 'classplanner/plandiferencial/plandiferenciallist.html'
    context_object_name = 'plandiferencial'

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class CreatePlanDiferencial(CreateView):
    model = PlanDiferencial
    form_class = PlanDiferencialCreateForm
    template_name = 'classplanner/plandiferencial/plandiferencialcreate.html'
    success_url = reverse_lazy('plandiferencial')

    def form_valid(self, form):
        messages.success(self.request, '¡Plan diferencial creado con exito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class UpdatePlanDiferencial(UpdateView):
    model = PlanDiferencial
    form_class = PlanDiferencialUpdateForm
    template_name = 'classplanner/plandiferencial/plandiferencialupdate.html'
    success_url = reverse_lazy('plandiferencial')
    context_object_name = 'plandiferencial'

    def form_valid(self, form):
        messages.success(self.request, '¡Plan diferencial actualizado con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class DeletePlanDiferencial(DeleteView):
    model = PlanDiferencial
    template_name = 'classplanner/plandiferencial/plandiferencialdelete.html'
    success_url = reverse_lazy('plandiferencial')
    context_object_name = 'plandiferencial'

    def form_valid(self, form):
        messages.success(self.request, '¡Plan diferencial eliminado con éxito!')
        return super().form_valid(form)

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
        form.instance.nombre = form.cleaned_data['nombre'].title()
        form.instance.descripcion = form.cleaned_data['descripcion'].capitalize()
        messages.success(self.request, '¡Asignatura creada con exito!')
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
        form.instance.nombre = form.cleaned_data['nombre'].title()
        form.instance.descripcion = form.cleaned_data['descripcion'].capitalize()
        messages.success(self.request, '¡Asignatura actualizada con éxito!')
        return super().form_valid(form)

# ("Cannot delete some instances of model 'Asignatura' because they are referenced through restricted foreign keys: 'PlanDeEstudio.asignatura_id'
@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador'), name='dispatch')
class DeleteAsignatura(DeleteView):
    model = Asignatura
    template_name = 'classplanner/asignaturas/asignaturadelete.html'
    success_url = reverse_lazy('asignaturas')
    context_object_name = 'asignatura'

    def form_valid(self, form):
        messages.success(self.request, '¡Asignatura eliminada con éxito!')
        return super().form_valid(form)
    
# ----------------------------------- # PLAN DE ESTUDIO

@login_required
@roles_required('root', 'Administrador')
def ListPlanDeEstudio(request):
    cursosModel = Curso.objects.all()
    plandeestudio = PlanDeEstudio.objects.all()

    cursos = []
    planes = {}
    for p in plandeestudio.values_list('curso_id', flat=True).distinct():
        if p == cursosModel.filter(id=p).first().id:
            c = int(cursosModel.filter(id=p).first().id)
            cursos.append(c)

    for c in cursos:
        curso_update = str(cursosModel.filter(id=c).first())
        curso_update_id = cursosModel.filter(id=c).first().id
        asignaturas_update = list(
            plandeestudio.filter(curso_id=c).values_list('asignatura_id__ident','hrs_asignatura')
        )
        horas = sum(plandeestudio.filter(curso_id=c).values_list('hrs_asignatura', flat=True))
        planes.update({f"{c}": [curso_update, asignaturas_update, horas, curso_update_id]})

    cursos.sort()  # Ordenar por curso_id
    context = {'plandeestudio': list(planes.values())}

    return render(request, 'classplanner/plandeestudio/plandeestudiolist.html', context)

@login_required
@roles_required('root', 'Administrador', 'Director')
def CreatePlanDeEstudio(request):
    asignaturas = Asignatura.objects.all()
    cursos = Curso.objects.all()
    context = {'form': PlanDeEstudioCreateForm(), 'asignaturas': asignaturas, 'cursos': cursos}

    return render(request, 'classplanner/plandeestudio/plandeestudiocreate.html', context)

@login_required
@roles_required('root', 'Administrador', 'Director')
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
def UpdatePlanDeEstudio(request, pk=None):
    curso = Curso.objects.get(pk=pk)
    horasCurso = int(curso.horas_plan_total)
    pdeModel = PlanDeEstudio.objects.all()
    asignaturasModel = Asignatura.objects.all()
    asignaturasSelected = list(pdeModel.filter(curso_id=curso.id).values_list('asignatura_id__ident','hrs_asignatura'))
    pdes = list(pdeModel.filter(curso_id=curso.id).values_list('pk', 'asignatura_id__ident'))
    print("pdes: ",pdes,"\nlast: ",pdeModel.last().pk)
    context = {
        'form': PlanDeEstudioUpdateForm(),
        'asignaturas': asignaturasModel,
        'asignaturasSelected': asignaturasSelected,
        'curso': curso,
        'horasCurso': horasCurso,
        'planesdeestudio': pdes,
        #'pdeCount': pdeModel.last().pk
    }

    return render(request, 'classplanner/plandeestudio/plandeestudioupdate.html', context)

@login_required
@roles_required('root', 'Administrador', 'Director')
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
            print("planes: ", planes,"\nhoras: ", horas,"\nasigns: ",asignaturas)
            for plan_id, hrs, asignatura_id in zip(
                planes, horas, asignaturas
            ):
                plan = planes_existentes.get(plan_id)
                print("planes existentes: ",planes_existentes,"\nplan loop: ",plan)
                if plan is None and not plan_id == "":
                    form.add_error(None, 'El plan seleccionado no es válido.')
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
                    planesCreate.append(nuevoPlan)
                else:
                    plan.hrs_asignatura = item_form.cleaned_data['hrs_asignatura']
                    plan.asignatura_id = item_form.cleaned_data['asignatura_id']
                    
                    planesUpdate.append(plan)
                #continue

            with transaction.atomic():
                print("planesUpdate: ", planesUpdate,"\nplanesCreate: ",planesCreate)
                PlanDeEstudio.objects.bulk_update(
                    planesUpdate,
                    ['hrs_asignatura', 'asignatura_id']
                )
                if planesCreate != []:
                    PlanDeEstudio.objects.bulk_create(planesCreate)

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

# ----------------------------------- #

def custom_logout(request):
    logout(request)
    return redirect('login') 