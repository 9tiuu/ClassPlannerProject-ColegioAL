from django.urls import path
from . import views
from .views import (
    CreateUsuario, ListUsuario, UpdateUsuario, DeleteUsuario,
    ListRegistros,
    ListRol, UpdateRol, DeleteRol, CreateRol,
    ListCursos, CreateCurso, UpdateCurso, DeleteCurso,
    ListPlanDiferencial, CreatePlanDiferencial, UpdatePlanDiferencial, DeletePlanDiferencial,
    ListAsignatura, CreateAsignatura, UpdateAsignatura, DeleteAsignatura,
    ListPlanDeEstudio, CreatePlanDeEstudio, UpdatePlanDeEstudio
)
from .views import custom_logout
# from django.contrib.auth.views import LoginView

urlpatterns = [
    path('home/', views.Home, name='home'),

    # ROLES
    path('createrol/', CreateRol.as_view(), name='createrol'),
    path('listrol/', ListRol.as_view(), name='listrol'),
    path('updaterol/<int:pk>/', UpdateRol.as_view(), name='updaterol'),
    path('deleterol/<int:pk>/', DeleteRol.as_view(), name='deleterol'),
    path('findrol/', views.FindRol, name='findrol'),

    # USUARIOS
    path('usercreate/', CreateUsuario.as_view(), name='usercreate'),
    path('userlist/', ListUsuario.as_view(), name='userlist'),
    path('userupdate/<int:pk>/', UpdateUsuario.as_view(), name='userupdate'),
    path('userdelete/<int:pk>/', DeleteUsuario.as_view(), name='userdelete'),

    # REGISTROS
    path('registros/', ListRegistros.as_view(), name='registros'),

    # CURSOS
    path('cursos/', ListCursos.as_view(), name='cursos'),
    path('cursocreate/', CreateCurso.as_view(), name='cursocreate'),
    path('cursoupdate/<int:pk>/', UpdateCurso.as_view(), name='cursoupdate'),
    path('cursodelete/<int:pk>/', DeleteCurso.as_view(), name='cursodelete'),

    # PLAN DIFERENCIAL
    path('plandiferencial/', ListPlanDiferencial.as_view(), name='plandiferencial'),
    path('plandiferencialcreate/', CreatePlanDiferencial.as_view(), name='plandiferencialcreate'),
    path('plandiferencialupdate/<int:pk>/', UpdatePlanDiferencial.as_view(), name='plandiferencialupdate'),
    path('plandiferencialdelete/<int:pk>/', DeletePlanDiferencial.as_view(), name='plandiferencialdelete'),

    # ASIGNATURAS
    path('asignaturas/', ListAsignatura.as_view(), name='asignaturas'),
    path('asignaturacreate/', CreateAsignatura.as_view(), name='asignaturacreate'),
    path('asignaturaupdate/<int:pk>/', UpdateAsignatura.as_view(), name='asignaturaupdate'),
    path('asignaturadelete/<int:pk>/', DeleteAsignatura.as_view(), name='asignaturadelete'),

    # PLAN DE ESTUDIOS
    path('plandeestudios/', views.ListPlanDeEstudio, name='plandeestudio'),
    path('plandeestudiocreate/', views.CreatePlanDeEstudio, name='plandeestudiocreate'),
    path('plandeestudiocreateform/', views.CreatePlanDeEstudioForm, name='plandeestudiocreateform'),
    path('plandeestudioupdate/<int:pk>/', UpdatePlanDeEstudio.as_view(), name='plandeestudioupdate'),

    # AUTENTICACION
    path('logout/', custom_logout, name='logout'),
    # path('', LoginView.as_view(), name='login'),
]