from django.db import models
from django.contrib.auth.models import AbstractUser 
# from datetime import datetime, date, timedelta
# from django.utils.timezone import now

# ID proporcionado por django EN TODOS los MODELOS ---------

class Rol(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name

class Usuario(AbstractUser):
    # Contraseña proporcionada por django
    name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    rut = models.CharField(max_length=10, unique=True, null=True)
    email = models.EmailField(max_length=254, unique=True)
    telefono = models.CharField(max_length=12, blank=True, null=True) # falta validacion
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, null=True)
    avatar = models.ImageField(upload_to='avatars', blank=True, null=True)
    passwd_changed = models.BooleanField(default=False, blank=True)
    # abstractuser tiene campo is_active

    def __str__(self) -> str:
        return f'{self.name} {self.last_name}'

class PlanDiferencial(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f'{self.nombre}'

class Asignatura(models.Model):
    ident = models.CharField(max_length=5)
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()
    plan_diferencial_id = models.ForeignKey(PlanDiferencial, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.ident} - {self.nombre}'

class Curso(models.Model):
    class Nivel(models.TextChoices):
        PRIMERO = '1°B', '1ro Básico'
        SEGUNDO = '2°B', '2do Básico'
        TERCERO = '3°B', '3ro Básico'
        CUARTO = '4°B', '4to Básico'
        QUINTO = '5°B', '5to Básico'
        SEXTO = '6°B', '6to Básico'
        SEPTIMO = '7°B', '7mo Básico'
        OCTAVO = '8°B', '8vo Básico'
        PRIMERO_MEDIO = '1°M', '1ro Medio'
        SEGUNDO_MEDIO = '2°M', '2do Medio'
        TERCERO_MEDIO = '3°M', '3ro Medio'
        CUARTO_MEDIO = '4°M', '4to Medio'

    nivel = models.CharField(max_length=12, choices=Nivel.choices)
    letra = models.CharField(max_length=1)
    horas_plan_total = models.FloatField()
    usuario_id = models.ForeignKey(Usuario, on_delete=models.RESTRICT)
    
    def __str__(self) -> str:
        return f'{self.nivel} {self.letra}'

class Estudiante(models.Model):
    nombre = models.CharField(max_length=50)
    apellido_p = models.CharField(max_length=50)
    apellido_m = models.CharField(max_length=50)
    rut = models.CharField(max_length=10, unique=True)
    promedio = models.FloatField()
    curso_id = models.ForeignKey(Curso, on_delete=models.RESTRICT)

    def __str__(self) -> str:
        return f'{self.nombre} {self.apellido_p} {self.apellido_m}'

class Nota(models.Model):
    nota = models.CharField(max_length=50)
    estudiante_id = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignatura_id = models.ForeignKey(Asignatura, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'Promedio de {self.estudiante_id.rut} en {self.asignatura_id.ident}: {self.nota}'

class Aula(models.Model):
    nombre = models.CharField(max_length=50)
    cupos = models.IntegerField()
    curso_id = models.ForeignKey(Curso, on_delete=models.RESTRICT, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.nombre}'

class Bloque(models.Model):
    class DiaSemana(models.TextChoices):
        LUNES = 'L', 'Lunes'
        MARTES = 'M', 'Martes'
        MIERCOLES = 'X', 'Miércoles'
        JUEVES = 'J', 'Jueves'
        VIERNES = 'V', 'Viernes'

    dia = models.CharField(max_length=50, choices=DiaSemana.choices)
    hora_inicio = models.TimeField() #HH:MM
    hora_termino = models.TimeField()

    def __str__(self) -> str:
        return f'{self.dia}: {self.hora_inicio} - {self.hora_termino}'

class PlanDeEstudio(models.Model):
    hrs_asignatura = models.FloatField()
    curso_id = models.ForeignKey(Curso, on_delete=models.CASCADE)
    asignatura_id = models.ForeignKey(Asignatura, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'{self.curso_id}: {self.hrs_asignatura}hrs. {self.asignatura_id}'

class Horario(models.Model):
    plan_de_estudio_id = models.ForeignKey(PlanDeEstudio, on_delete=models.RESTRICT)
    aula_id = models.ForeignKey(Aula, on_delete=models.RESTRICT)
    bloque_id = models.ManyToManyField(Bloque)

    def __str__(self) -> str:
        return f'Plan {self.plan_de_estudio_id}, Bloque: {self.bloque_id}, Aula: {self.aula_id}'

class CargaHoraria(models.Model):
    usuario_id = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    asignatura_id = models.ManyToManyField(Asignatura)
    curso_id = models.ManyToManyField(Curso)
    hrs_contrato = models.FloatField()
    hrs_aula = models.FloatField()
    hrs_cd = models.FloatField()
    hrs_aa = models.FloatField()

    def __str__(self) -> str:
        return f'{self.usuario_id} - {self.hrs_contrato}hrs. Contrato - {self.hrs_aula}hrs. Aula'