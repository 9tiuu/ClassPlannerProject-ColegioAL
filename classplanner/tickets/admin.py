from django.contrib import admin
from .models import Rol, Usuario, Asignatura, Curso, GrupoElectivo, Estudiante, Aula, Bloque, Horario, AsignaturaPorDocente

# Register your models here.

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Asignatura)
admin.site.register(Curso)
admin.site.register(GrupoElectivo)
admin.site.register(Estudiante)
admin.site.register(Aula)
admin.site.register(Bloque)
admin.site.register(Horario)
admin.site.register(AsignaturaPorDocente)