from django.db import models
from django.contrib.auth.models import AbstractUser 
# from datetime import datetime, date, timedelta
# from django.utils.timezone import now

# ID proporcionado por django EN TODOS los MODELOS ---------

class Rol(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.name

class Usuario(AbstractUser):
    # Contraseña proporcionada por django
    name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    rut = models.CharField(max_length=10, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT)
    avatar = models.ImageField(upload_to='avatars', blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.name} {self.last_name}'

class GrupoElectivo(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f'{self.nombre}'

class Asignatura(models.Model):
    ident = models.CharField(max_length=50, null=True, blank=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()
    hrs_asignatura = models.FloatField()
    grupo_electivo_id = models.ForeignKey(GrupoElectivo, on_delete=models.RESTRICT, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.ident} {self.nombre}'

class Curso(models.Model):
    nombre = models.CharField(max_length=50)
    usuario_id = models.ForeignKey(Usuario, on_delete=models.RESTRICT, blank=True, null=True)
    
    def __str__(self) -> str:
        return f'{self.nombre}'

class Estudiante(models.Model):
    nombre = models.CharField(max_length=50)
    apellido_p = models.CharField(max_length=50)
    apellido_m = models.CharField(max_length=50)
    rut = models.CharField(max_length=10, unique=True)
    curso_id = models.ForeignKey(Curso, on_delete=models.RESTRICT, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.nombre} {self.apellido_p} {self.apellido_m}'

class Aula(models.Model):
    nombre = models.CharField(max_length=50)
    curso_id = models.ForeignKey(Curso, on_delete=models.RESTRICT)

    def __str__(self) -> str:
        return f'{self.nombre}'

class Bloque(models.Model):
    dia = models.CharField(max_length=50)
    hora_inicio = models.FloatField()
    hora_termino = models.FloatField()

    def __str__(self) -> str:
        return f'{self.dia} {self.hora_inicio} {self.hora_termino}'

class AsignaturaPorDocente(models.Model):
    curso_id = models.ForeignKey(Curso, on_delete=models.RESTRICT)
    usuario_id = models.ForeignKey(Usuario, on_delete=models.RESTRICT)
    asignatura_id = models.ForeignKey(Asignatura, on_delete=models.RESTRICT)
    hrs_semanales = models.FloatField()

    def __str__(self) -> str:
        return f'{self.curso_id} {self.usuario_id} {self.asignatura_id}'

class Horario(models.Model):
    asignatura_por_docente_id = models.ForeignKey(AsignaturaPorDocente, on_delete=models.RESTRICT)
    aula_id = models.ForeignKey(Aula, on_delete=models.RESTRICT)
    bloque_id = models.ForeignKey(Bloque, on_delete=models.RESTRICT)

    def __str__(self) -> str:
        return f'{self.asignatura_por_docente_id} {self.bloque_id} {self.aula_id}'