from django.forms import ValidationError
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views import View
from django.contrib import messages
from datetime import datetime
import re

from .models import Rol, Usuario, Asignatura, PlanDeEstudio, Curso
from .forms import RolForm, UsuarioForm, UserUpdateForm

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin

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

# ----------------------------------- # ASIGNATURAS

class ListAsignatura(UserPassesTestMixin, ListView):
    model = Asignatura
    template_name = 'tickets/asignaturas/asignaturalist.html'
    context_object_name = 'asignatura'

    def test_func(self):
            rol = self.request.user.rol.name
            return rol in ['root', 'Administrador']

# ----------------------------------- # PLAN DE ESTUDIO

class ListPlanDeEstudio(UserPassesTestMixin, ListView):
    model = PlanDeEstudio
    template_name = 'tickets/plandeestudio/plandeestudiolist.html'
    context_object_name = 'plandeestudio'

    def test_func(self):
            rol = self.request.user.rol.name
            return rol in ['root', 'Administrador', 'Profesor']

# ----------------------------------- #

def custom_logout(request):
    logout(request)  
    return redirect('login') 