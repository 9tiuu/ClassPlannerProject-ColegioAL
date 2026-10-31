from django.contrib import admin
from .models import Rol, Usuario, Asignatura, Curso, Aula, Bloque, Horario, Nota, PlanDeEstudio, CargaHoraria

# Register your models here.

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Asignatura)
admin.site.register(Curso)
admin.site.register(Nota)
admin.site.register(Aula)
admin.site.register(Bloque)
admin.site.register(PlanDeEstudio)
admin.site.register(Horario)
admin.site.register(CargaHoraria)