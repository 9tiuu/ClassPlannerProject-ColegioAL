from django.urls import path
from . import views
from .views import (
    CreateUsuario, ListUsuario, UpdateUsuario, DeleteUsuario,
    ListRegistros, ListLogins,
    ListRol, UpdateRol, DeleteRol, CreateRol,
    ListNombresAsignatura, CreateNombresAsignatura, UpdateNombresAsignatura, DeleteNombresAsignatura,
    ListAreasPlanesDiferenciales, CreateAreasPlanesDiferenciales, UpdateAreasPlanesDiferenciales, DeleteAreasPlanesDiferenciales,
    ListAula, CreateAula, UpdateAula, DeleteAula,
    ListCursos, CreateCurso, UpdateCurso, DeleteCurso,
    ListEstudiantes, CreateEstudiante, UpdateEstudiante, DeleteEstudiante,
    ListPromedioAsignatura, NotasDocente,
    ListAsignatura, CreateAsignatura, UpdateAsignatura, DeleteAsignatura,
    ListCargaHoraria, 
)
from .views import custom_logout
# from django.contrib.auth.views import LoginView

urlpatterns = [
    path('home/', views.Home, name='home'),

    # ROLES
    path('sistema/createrol/', CreateRol.as_view(), name='createrol'),
    path('sistema/listrol/', ListRol.as_view(), name='listrol'),
    path('sistema/updaterol/<int:pk>/', UpdateRol.as_view(), name='updaterol'),
    path('sistema/deleterol/<int:pk>/', DeleteRol.as_view(), name='deleterol'),
    path('sistema/findrol/', views.FindRol, name='findrol'),

    # USUARIOS
    path('sistema/usercreate/', CreateUsuario.as_view(), name='usercreate'),
    path('sistema/userlist/', ListUsuario.as_view(), name='userlist'),
    path('sistema/userupdate/<int:pk>/', UpdateUsuario.as_view(), name='userupdate'),
    path('sistema/userdelete/<int:pk>/', DeleteUsuario.as_view(), name='userdelete'),
    path('sistema/useractivate/<int:pk>/', views.ActivateUsuario, name='useractivate'),

    # NOMBRES DE ASIGNATURA
    path('sistema/nombresasignatura/', ListNombresAsignatura.as_view(), name='nombresasignatura'),
    path('sistema/nombresasignaturacreate/', CreateNombresAsignatura.as_view(), name='nombresasignaturacreate'),
    path('sistema/nombresasignaturaupdate/<int:pk>/', UpdateNombresAsignatura.as_view(), name='nombresasignaturaupdate'),
    path('sistema/nombresasignaturadelete/<int:pk>/', DeleteNombresAsignatura.as_view(), name='nombresasignaturadelete'),
    path('sistema/nombresasignaturaactivate/<int:pk>/', views.ActivateNombresAsignatura, name='nombresasignaturaactivate'),

    # NOMBRES DE PLANES DIFERENCIALES
    path('sistema/nombresplanes/', ListAreasPlanesDiferenciales.as_view(), name='nombresplanesdiferenciales'),
    path('sistema/nombresplanescreate/', CreateAreasPlanesDiferenciales.as_view(), name='nombresplanesdiferencialescreate'),
    path('sistema/nombresplanesupdate/<int:pk>/', UpdateAreasPlanesDiferenciales.as_view(), name='nombresplanesdiferencialesupdate'),
    path('sistema/nombresplanesdelete/<int:pk>/', DeleteAreasPlanesDiferenciales.as_view(), name='nombresplanesdiferencialesdelete'),
    path('sistema/nombresplanesactivate/<int:pk>/', views.ActivateAreasPlanesDiferenciales, name='nombresplanesdiferencialesactivate'),

    # REGISTROS
    path('sistema/registros/', ListRegistros.as_view(), name='registros'),

    # LOGINS
    path('sistema/login/', ListLogins.as_view(), name='logins'),

    # AULAS
    path('aulas/', ListAula.as_view(), name='aulas'),
    path('aulacreate/', CreateAula.as_view(), name='aulacreate'),
    path('aulaupdate/<int:pk>/', UpdateAula.as_view(), name='aulaupdate'),
    path('auladelete/<int:pk>/', DeleteAula.as_view(), name='auladelete'),

    # CURSOS
    path('cursos/', ListCursos.as_view(), name='cursos'),
    path('cursocreate/', CreateCurso.as_view(), name='cursocreate'),
    path('cursoupdate/<int:pk>/', UpdateCurso.as_view(), name='cursoupdate'),
    path('cursodelete/<int:pk>/', DeleteCurso.as_view(), name='cursodelete'),

    # ESTUDIANTES
    path('estudiantes/', ListEstudiantes.as_view(), name='estudiantes'),
    path('estudiantecreate/', CreateEstudiante.as_view(), name='estudiantecreate'),
    path('estudianteupdate/<str:rut>/<int:curso_id>/', UpdateEstudiante.as_view(), name='estudianteupdate'),
    path('estudiantedelete/<str:rut>/<int:curso_id>/', DeleteEstudiante.as_view(), name='estudiantedelete'),
    path('estudianteactivate/<str:rut>/', views.ActivateEstudiante, name='estudianteactivate'),

    # PROMEDIOS
    path('promedioasignatura/estudiante/<str:rut>/<int:curso_id>/', ListPromedioAsignatura.as_view(), name='promedioasignatura'),
    path('promedioasignaturaexport/<str:rut>/<int:export>', views.ExportarNotas, name='notasexport'),
    path('promedioasignatura/notasdocentelist/', NotasDocente.as_view(), name='notasdocente'),

    # ASIGNATURAS
    path('asignaturas/', ListAsignatura.as_view(), name='asignaturas'),
    path('asignaturacreate/', CreateAsignatura.as_view(), name='asignaturacreate'),
    path('asignaturaupdate/<int:pk>/', UpdateAsignatura.as_view(), name='asignaturaupdate'),
    path('asignaturadelete/<int:pk>/', DeleteAsignatura.as_view(), name='asignaturadelete'),
    path('asignaturaactivate/<int:pk>/', views.ActivateAsignatura, name='asignaturaactivate'),

    # PLAN DE ESTUDIOS
    path('plandeestudios/', views.ListPlanDeEstudio, name='plandeestudio'),
    path('plandeestudiocreate/', views.CreatePlanDeEstudio, name='plandeestudiocreate'),
    path('plandeestudiocreateform/', views.CreatePlanDeEstudioForm, name='plandeestudiocreateform'),
    path('plandeestudioupdate/<int:pk>/', views.UpdatePlanDeEstudio, name='plandeestudioupdate'),
    path('plandeestudioupdateform/<int:pk>/', views.UpdatePlanDeEstudioForm, name='plandeestudioupdateform'),
    path('plandeestudiosexport/<str:export>', views.ExportarPlanes, name='planesexport'),

    # CARGAS HORARIAS
    path('cargashorarias/', ListCargaHoraria.as_view(), name='cargashorarias'),
    path('cargashorariascreate/', views.CreateCargaHoraria, name='cargashorariascreate'),
    path('cargashorariasupdate/<int:pk>/', views.UpdateCargaHoraria, name='cargashorariasupdate'),
    path('cargashorariasexport/', views.ExportarCargaHoraria, name='cargashorariasexport'),

    # HORARIOS
    path('horarios/', views.ListHorarios, name='horarios'),
    path('horarioscreate/', views.CreateHorario, name='horariocreate'),
    path('horariosupdate/<int:pk>/', views.UpdateHorario, name='horarioupdate'),
    path('horariosexport/', views.ExportarHorario, name='horariosexport'),
    path('horarioshistorico/', views.ListHorariosHistoricos, name='horarioshistorico'),
    path('horarioshistorico/preview/<str:filename>/', views.PrevisualizarHorario, name='horariopdfpreview'),
    path('horarioshistorico/download-selected/', views.DescargarHorariosHistoricos, name='horarioshistoricoszip'),
    path('horarioshistorico/download/<str:filename>/', views.DescargarHorario, name='horariopdfdownload'),

    # AUTENTICACION
    path('logout/', custom_logout, name='logout'),
    # path('', LoginView.as_view(), name='login'),
]