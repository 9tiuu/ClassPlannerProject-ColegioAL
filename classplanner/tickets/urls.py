from django.urls import path
from . import views
from .views import CreateRol, CreateUsuario, ListUsuario, UpdateUsuario, DeleteUsuario, ListRol, UpdateRol, DeleteRol, ListAsignatura, ListPlanDeEstudio
from .views import custom_logout
from django.contrib.auth.views import LoginView

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

    # ASIGNATURAS
    path('asignaturas/', ListAsignatura.as_view(), name='asignaturas'),

    # ASIGNATURAS POR DOCENTE / O HORARIOS
    path('asignaturaspordocentes/', ListPlanDeEstudio.as_view(), name='asignaturaspordocente'),

    # AUTENTICACION
    path('logout/', custom_logout, name='logout'),
    path('', LoginView.as_view(), name='login'),
]