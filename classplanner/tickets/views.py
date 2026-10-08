from django.forms import ValidationError
from django.http import request
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
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
from .models import Rol, Usuario, Asignatura, PlanDeEstudio, Curso, PlanDiferencial
from .forms import (
    RolForm, UsuarioForm, UserUpdateForm,
    PlanDeEstudioCreateForm, PlanDeEstudioUpdateForm,
    CursoForm, AsignaturasCreateForm, AsignaturaUpdateForm,
    PlanDiferencialCreateForm, PlanDiferencialUpdateForm
)

from django.contrib.auth import logout, get_user_model
from django.shortcuts import redirect
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

# Create your views here.

def validar_rut(rut):
    rut = rut.replace(".", "").upper()
    match = re.match(r"^(\d{1,8})[-]([0-9Kk])$", rut)

    if not match:
        raise ValidationError("El RUT tiene un formato incorrecto")
    return True

# ----------------------------------- # HOME / DASHBOARD

@login_required
def Home(request):
    return render(request, 'tickets/base.html', {})

# ----------------------------------- # ROLES

@method_decorator(login_required, name='dispatch')
class CreateRol(UserPassesTestMixin, CreateView):
    model = Rol
    form_class = RolForm
    template_name = 'tickets/roles/roluser_create.html'
    success_url = reverse_lazy('listrol')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Agregado con exito!')
        return super().form_valid(form)
    
    
class ListRol(UserPassesTestMixin, ListView):
    model = Rol
    template_name = 'tickets/roles/roluser_list.html'
    context_object_name = 'rol'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

def FindRol(request):
    response = request.GET.get('find-rol')
    if response:
        roluser = Rol.objects.filter(name__icontains = response)
    else:
        roluser = Rol.objects.all()   
    return render(request, 'tickets/roles/rolser_find.html', {'rol':roluser, 'response':response})

class UpdateRol(UserPassesTestMixin, UpdateView):
    model = Rol
    form_class = RolForm
    template_name = 'tickets/roles/roluser_update.html'
    success_url = reverse_lazy('listrol')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Actualizado con exito!')
        return super().form_valid(form)

class DeleteRol(UserPassesTestMixin, DeleteView):
    model = Rol
    template_name = 'tickets/roles/roluser_delete.html'
    context_object_name = 'rol'
    success_url = reverse_lazy('listrol')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Rol Eliminado con exito!')
        return super().form_valid(form)

# ----------------------------------- # USUARIOS

@method_decorator(login_required, name='dispatch')
class CreateUsuario(UserPassesTestMixin, CreateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = 'tickets/usuarios/usercreate.html'
    success_url = reverse_lazy('userlist')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

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
        
        user = form.save()
        messages.success(self.request, '¡Usuario Registrado con exito!')
        return super().form_valid(form)
    
@method_decorator(login_required, name='dispatch')    
class ListUsuario(UserPassesTestMixin, ListView):
    model = Usuario
    template_name = 'tickets/usuarios/userlist.html'
    context_object_name = 'usersys'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

@method_decorator(login_required, name='dispatch')
class UpdateUsuario(UserPassesTestMixin, UpdateView):
    model = Usuario
    form_class = UserUpdateForm
    template_name = 'tickets/usuarios/userupdate.html'
    success_url = reverse_lazy('userlist')
    context_object_name = 'usuario'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

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
        
        user = form.save()
        messages.success(self.request, '¡Usuario Registrado con exito!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')    
class DeleteUsuario(UserPassesTestMixin, DeleteView):
    model = Usuario
    template_name = 'tickets/usuarios/userdelete.html'
    success_url = reverse_lazy('userlist')
    context_object_name = 'usuario'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Usuario Eliminado con exito!')
        return super().form_valid(form)

# ----------------------------------- # REGISTROS

class ListRegistros(UserPassesTestMixin, ListView):
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

    def test_func(self):
        try:
            rol = self.request.user.rol.name
            return rol in ['root', 'Administrador']
        except AttributeError:
            raise PermissionDenied('Ha intentado visitar una página a la que no tiene acceso')

# ----------------------------------- # CURSOS

class ListCursos(UserPassesTestMixin, ListView):
    model = Curso
    template_name = 'tickets/cursos/cursolist.html'
    context_object_name = 'curso'

    def test_func(self):
            rol = self.request.user.rol.name
            return rol in ['root', 'Administrador']

    def get_queryset(self):
        queryset = super().get_queryset()

        # mostrar horas como entero si es XX,0
        hrs = self.request.GET.get('hrs')
        for curso in queryset:
            if curso.horas_plan_total == int(curso.horas_plan_total):
                curso.horas_plan_total = floor(curso.horas_plan_total)
        return queryset

class CreateCurso(UserPassesTestMixin, CreateView):
    model = Curso
    form_class = CursoForm
    template_name = 'tickets/cursos/cursocreate.html'
    success_url = reverse_lazy('cursos')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        # Validar que no exista otro curso con el mismo nivel y letra
        nivel = form.cleaned_data.get('nivel')
        letra = form.cleaned_data.get('letra')
        if Curso.objects.filter(nivel=nivel, letra=letra).exists():
            raise ValueError("Ya existe este curso.")

        # Validar que no exista otro curso con la misma jefatura
        usuario_id = form.cleaned_data.get('usuario_id')
        if usuario_id and Curso.objects.filter(usuario_id=usuario_id).exists():
            raise ValueError("El docente seleccionado ya tiene jefatura.")

        form.instance.letra = str(form.instance.letra).capitalize()
        curso = form.save()
        messages.success(self.request, '¡Curso agregado con exito!')
        return super().form_valid(form)

class UpdateCurso(UserPassesTestMixin, UpdateView):
    model = Curso
    form_class = CursoForm
    template_name = 'tickets/cursos/cursoupdate.html'
    success_url = reverse_lazy('cursolist')
    context_object_name = 'curso'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        # Validar que no exista otro curso con el mismo nivel y letra
        nivel = form.cleaned_data.get('nivel')
        letra = form.cleaned_data.get('letra')
        if Curso.objects.filter(nivel=nivel, letra=letra).exclude(pk=self.pk).exists():
            raise ValueError("Ya existe este curso.")

        # Validar que no exista otro curso con la misma jefatura
        usuario_id = form.cleaned_data.get('usuario_id')
        if usuario_id and Curso.objects.filter(usuario_id=usuario_id).exclude(pk=self.pk).exists():
            raise ValueError("El docente seleccionado ya tiene jefatura.")
        curso = form.save()
        messages.success(self.request, '¡Curso actualizado con exito!')
        return super().form_valid(form)

class DeleteCurso(UserPassesTestMixin, DeleteView):
    model = Curso
    template_name = 'tickets/cursos/cursodelete.html'
    context_object_name = 'curso'
    success_url = reverse_lazy('cursolist')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Curso eliminado con exito!')
        return super().form_valid(form)

# ----------------------------------- # PLAN DIFERENCIAL

class ListPlanDiferencial(UserPassesTestMixin, ListView):
    model = PlanDiferencial
    template_name = 'tickets/plandiferencial/plandiferenciallist.html'
    context_object_name = 'plandiferencial'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

class CreatePlanDiferencial(UserPassesTestMixin, CreateView):
    model = PlanDiferencial
    form_class = PlanDiferencialCreateForm
    template_name = 'tickets/plandiferencial/plandiferencialcreate.html'
    success_url = reverse_lazy('plandiferencial')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Plan diferencial creado con exito!')
        return super().form_valid(form)

class UpdatePlanDiferencial(UserPassesTestMixin, UpdateView):
    model = PlanDiferencial
    form_class = PlanDiferencialUpdateForm
    template_name = 'tickets/plandiferencial/plandiferencialupdate.html'
    success_url = reverse_lazy('plandiferencial')
    context_object_name = 'plandiferencial'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Plan diferencial actualizado con éxito!')
        return super().form_valid(form)

class DeletePlanDiferencial(UserPassesTestMixin, DeleteView):
    model = PlanDiferencial
    template_name = 'tickets/plandiferencial/plandiferencialdelete.html'
    success_url = reverse_lazy('plandiferencial')
    context_object_name = 'plandiferencial'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Plan diferencial eliminado con éxito!')
        return super().form_valid(form)

# ----------------------------------- # ASIGNATURAS

class ListAsignatura(UserPassesTestMixin, ListView):
    model = Asignatura
    template_name = 'tickets/asignaturas/asignaturalist.html'
    context_object_name = 'asignatura'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

class CreateAsignatura(UserPassesTestMixin, CreateView):
    model = Asignatura
    form_class = AsignaturasCreateForm
    template_name = 'tickets/asignaturas/asignaturacreate.html'
    success_url = reverse_lazy('asignaturas')

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Asignatura creada con exito!')
        return super().form_valid(form)

class UpdateAsignatura(UserPassesTestMixin, UpdateView):
    model = Asignatura
    form_class = AsignaturaUpdateForm
    template_name = 'tickets/asignaturas/asignaturupdate.html'
    success_url = reverse_lazy('asignaturas')
    context_object_name = 'asignatura'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Asignatura actualizada con éxito!')
        return super().form_valid(form)

class DeleteAsignatura(UserPassesTestMixin, DeleteView):
    model = Asignatura
    template_name = 'tickets/asignaturas/asignaturadelete.html'
    success_url = reverse_lazy('asignaturas')
    context_object_name = 'asignatura'

    def test_func(self):
        rol = self.request.user.rol.name
        return rol in ['root', 'Administrador']

    def form_valid(self, form):
        messages.success(self.request, '¡Asignatura eliminada con éxito!')
        return super().form_valid(form)
    
# ----------------------------------- # PLAN DE ESTUDIO

def ListPlanDeEstudio(request): 
    cursosModel = Curso.objects.all()
    plandeestudio = PlanDeEstudio.objects.all()

    cursos = []
    planes = {}
    for p in plandeestudio.values_list('curso_id', flat=True).distinct():
        if p == cursosModel.filter(id=p).first().id:
            c = cursosModel.filter(id=p).first()
            cursos.append(c)

    horas = [sum(plandeestudio.filter(curso_id=c.id).values_list('hrs_asignatura', flat=True)) for c in cursos]
    # agregar curso, asignaturas y sumar horas semanales al diccionario para iterar en lista
    # por hacer
    planes.update({"curso": list(plandeestudio.filter(curso_id=c.id).values_list('curso_id', flat=True)) for c in cursos})
    planes.update({"asignaturas": list(plandeestudio.filter(curso_id=c.id).values_list('asignatura_id', flat=True)) for c in cursos})
    planes.update({"horas": horas})

    cursos.sort(key=lambda c: (c.nivel, c.letra))  # Ordenar por nivel y letra

    print(f"cursos: {cursos}\nplandeestudio: {planes}")

    context = {'plandeestudio': plandeestudio, 'cursos': cursos}

    return render(request, 'tickets/plandeestudio/plandeestudiolist.html', context)

def HorasPlanCurso(): # horas totales semanales, para validación en create
    basica_1_4 = 30
    basica_5_6 = 30
    basica_7_8 = 33
    media_1_2 = 33
    media_3_4 = 36

def CreatePlanDeEstudio(request):
    asignaturas = Asignatura.objects.all()
    context = {'form': PlanDeEstudioCreateForm(), 'asignaturas': asignaturas}

    return render(request, 'tickets/plandeestudio/plandeestudiocreate.html', context)

def CreatePlanDeEstudioForm(request):
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
        print(f"curso_ids: {curso_ids}\ncurso_ids[:-1]: {curso_ids[:-1]}\nplanes: {planes}")

        if not horas or len(horas) != len(asignaturas):
            form.add_error(None, 'Por favor, complete todos los campos')
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