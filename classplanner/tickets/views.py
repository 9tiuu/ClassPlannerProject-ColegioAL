from django.forms import ValidationError
from django.http import request, Http404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views import View
from django.contrib import messages
from datetime import datetime
import re
from math import floor

from easyaudit.models import CRUDEvent
from .models import Rol, Usuario, Asignatura, PlanDeEstudio, Curso, PlanDiferencial, Estudiante, Aula
from .forms import (
    RolForm, UsuarioForm, UserUpdateForm,
    PlanDeEstudioCreateForm, PlanDeEstudioUpdateForm,
    CursoForm, AsignaturasCreateForm, AsignaturaUpdateForm,
    AulaCreateForm, AulaUpdateForm,
    PlanDiferencialCreateForm, PlanDiferencialUpdateForm,
    EstudiantesCreateForm, EstudiantesUpdateForm
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
    return render(request, 'tickets/base.html', {})

# ----------------------------------- # ROLES

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class CreateRol(CreateView):
    model = Rol
    form_class = RolForm
    template_name = 'tickets/roles/roluser_create.html'
    success_url = reverse_lazy('listrol')

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Agregado con exito!')
        return super().form_valid(form)
    
@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch') 
class ListRol(ListView):
    model = Rol
    template_name = 'tickets/roles/roluser_list.html'
    context_object_name = 'rol'

def FindRol(request):
    response = request.GET.get('find-rol')
    if response:
        roluser = Rol.objects.filter(name__icontains = response)
    else:
        roluser = Rol.objects.all()   
    return render(request, 'tickets/roles/rolser_find.html', {'rol':roluser, 'response':response})

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class UpdateRol(UpdateView):
    model = Rol
    form_class = RolForm
    template_name = 'tickets/roles/roluser_update.html'
    success_url = reverse_lazy('listrol')

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Actualizado con exito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class DeleteRol(DeleteView):
    model = Rol
    template_name = 'tickets/roles/roluser_delete.html'
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
    template_name = 'tickets/usuarios/usercreate.html'
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
    template_name = 'tickets/usuarios/userlist.html'
    context_object_name = 'usersys'

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class UpdateUsuario(UpdateView):
    model = Usuario
    form_class = UserUpdateForm
    template_name = 'tickets/usuarios/userupdate.html'
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
    template_name = 'tickets/usuarios/userdelete.html'
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
    template_name = 'tickets/registros/registroslist.html'
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
    template_name = 'tickets/cursos/cursolist.html'
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
    template_name = 'tickets/cursos/cursocreate.html'
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
    template_name = 'tickets/cursos/cursoupdate.html'
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
    template_name = 'tickets/cursos/cursodelete.html'
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
    template_name = 'tickets/aulas/aulalist.html'
    context_object_name = 'aulas'

    def get_queryset(self):
        return Aula.objects.prefetch_related('curso_id')

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class CreateAula(CreateView):
    model = Aula
    form_class = AulaCreateForm
    template_name = 'tickets/aulas/aulacreate.html'
    success_url = reverse_lazy('aulas')

    def form_valid(self, form):
        messages.success(self.request, '¡Aula creada con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class UpdateAula(UpdateView):
    model = Aula
    form_class = AulaUpdateForm
    template_name = 'tickets/aulas/aulaupdate.html'
    success_url = reverse_lazy('aulas')
    context_object_name = 'aula'

    def form_valid(self, form):
        messages.success(self.request, '¡Aula actualizada con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class DeleteAula(DeleteView):
    model = Aula
    template_name = 'tickets/aulas/auladelete.html'
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
    template_name = 'tickets/estudiantes/estudianteslist.html'
    context_object_name = 'estudiantes'

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class CreateEstudiante(CreateView):
    model = Estudiante
    form_class = EstudiantesCreateForm
    template_name = 'tickets/estudiantes/estudiantescreate.html'
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
    template_name = 'tickets/estudiantes/estudiantesupdate.html'
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
    template_name = 'tickets/estudiantes/estudiantesdelete.html'
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

# ----------------------------------- # PLAN DIFERENCIAL

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class ListPlanDiferencial(ListView):
    model = PlanDiferencial
    template_name = 'tickets/plandiferencial/plandiferenciallist.html'
    context_object_name = 'plandiferencial'

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class CreatePlanDiferencial(CreateView):
    model = PlanDiferencial
    form_class = PlanDiferencialCreateForm
    template_name = 'tickets/plandiferencial/plandiferencialcreate.html'
    success_url = reverse_lazy('plandiferencial')

    def form_valid(self, form):
        messages.success(self.request, '¡Plan diferencial creado con exito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class UpdatePlanDiferencial(UpdateView):
    model = PlanDiferencial
    form_class = PlanDiferencialUpdateForm
    template_name = 'tickets/plandiferencial/plandiferencialupdate.html'
    success_url = reverse_lazy('plandiferencial')
    context_object_name = 'plandiferencial'

    def form_valid(self, form):
        messages.success(self.request, '¡Plan diferencial actualizado con éxito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root'), name='dispatch')
class DeletePlanDiferencial(DeleteView):
    model = PlanDiferencial
    template_name = 'tickets/plandiferencial/plandiferencialdelete.html'
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
    template_name = 'tickets/asignaturas/asignaturalist.html'
    context_object_name = 'asignatura'

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador'), name='dispatch')
class CreateAsignatura(UserPassesTestMixin, CreateView):
    model = Asignatura
    form_class = AsignaturasCreateForm
    template_name = 'tickets/asignaturas/asignaturacreate.html'
    success_url = reverse_lazy('asignaturas')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        form.instance.ident = form.cleaned_data['ident'].strip().upper()
        form.instance.nombre = form.cleaned_data['nombre'].title()
        form.instance.descripcion = form.cleaned_data['descripcion'].capitalize()
        messages.success(self.request, '¡Asignatura creada con exito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class UpdateAsignatura(UpdateView):
    model = Asignatura
    form_class = AsignaturaUpdateForm
    template_name = 'tickets/asignaturas/asignaturaupdate.html'
    success_url = reverse_lazy('asignaturas')
    context_object_name = 'asignatura'

    def form_valid(self, form):
        messages.success(self.request, '¡Asignatura actualizada con éxito!')
        return super().form_valid(form)

# ("Cannot delete some instances of model 'Asignatura' because they are referenced through restricted foreign keys: 'PlanDeEstudio.asignatura_id'
@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador'), name='dispatch')
class DeleteAsignatura(DeleteView):
    model = Asignatura
    template_name = 'tickets/asignaturas/asignaturadelete.html'
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
        asignaturas_update = list(
            plandeestudio.filter(curso_id=c).values_list('asignatura_id__ident','hrs_asignatura')
        )
        horas = sum(plandeestudio.filter(curso_id=c).values_list('hrs_asignatura', flat=True))
        planes.update({f"{c}": [curso_update, asignaturas_update, horas]})

    cursos.sort()  # Ordenar por curso_id
    context = {'plandeestudio': list(planes.values())}

    return render(request, 'tickets/plandeestudio/plandeestudiolist.html', context)

@login_required
@roles_required('root', 'Administrador', 'Director')
def CreatePlanDeEstudio(request):
    asignaturas = Asignatura.objects.all()
    cursos = Curso.objects.all()
    context = {'form': PlanDeEstudioCreateForm(), 'asignaturas': asignaturas, 'cursos': cursos}

    return render(request, 'tickets/plandeestudio/plandeestudiocreate.html', context)

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
                    'tickets/plandeestudio/plandeestudioformerror.html',
                    {'form': form},
                )
        print(f"curso_ids: {curso_ids}\ncurso_ids[:-1]: {curso_ids[:-1]}\nplanes: {planes}")

        if not horas or len(horas) != len(asignaturas):
            form.add_error(None, 'Por favor, complete todos los campos')
            return render(
                request,
                'tickets/plandeestudio/plandeestudioformerror.html',
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
                        'tickets/plandeestudio/plandeestudioformerror.html',
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
                    'Planes de estudio agregados exitosamente.'
                )
                response = render(
                    request,
                    'tickets/plandeestudio/plandeestudioform.html',
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
                'tickets/plandeestudio/plandeestudioform.html',
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
            'tickets/plandeestudio/plandeestudioformerror.html',
            {'form': form},
        )

    return render(request, 'tickets/plandeestudio/plandeestudioform.html', {'form': form})

@method_decorator(login_required, name='dispatch')
@method_decorator(roles_required('root', 'Administrador', 'Director'), name='dispatch')
class UpdatePlanDeEstudio(UserPassesTestMixin, UpdateView):
    model = PlanDeEstudio
    form_class = PlanDeEstudioUpdateForm
    template_name = 'tickets/plandeestudio/plandeestudioupdate.html'
    success_url = reverse_lazy('plandeestudiolist')
    context_object_name = 'plandeestudio'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        hrs = form.cleaned_data.get('hrs_asignatura')
        if hrs < 0:
            form.add_error('hrs_asignatura', 'Las horas de asignatura no pueden ser menor a 0.')
            return self.form_invalid(form)
        
        user = form.save()
        messages.success(self.request, '¡Plan de Estudio actualizado con exito!')
        return super().form_valid(form)

# ----------------------------------- #

def custom_logout(request):
    logout(request)
    return redirect('login') 