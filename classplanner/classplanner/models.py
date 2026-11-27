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

class NombresAsignatura(models.Model):
    nombre = models.CharField(max_length=80, unique=True,
        error_messages = {
            'unique': 'Este nombre ya está registrado.'
        }                      
    )
    is_active = models.BooleanField(default=True, blank=True)

    def delete(self, *args, **kwargs):
        # para mantener dependencias en cargas/horarios
        self.is_active = False
        self.save()

    def __str__(self):
        return self.nombre

class AreasPlanesDiferenciales(models.Model):
    nombre = models.CharField(max_length=60, unique=True,
        error_messages = {
            'unique': 'Este nombre ya está registrado.'
        }                      
    )
    is_active = models.BooleanField(default=True, blank=True)

    def delete(self, *args, **kwargs):
        # para mantener dependencias en cargas/horarios
        self.is_active = False
        self.save()

    def __str__(self):
        return self.nombre

class Asignatura(models.Model):
    ident = models.CharField(
        max_length=10, unique=True,
        error_messages = {
            'unique': 'Ya existe una asignatura con este identificador.'
        }
        )
    descripcion = models.TextField()
    nombres_asignatura_id = models.ForeignKey(
        NombresAsignatura, on_delete=models.RESTRICT,unique=True,
        error_messages = {
            'unique': 'Ya existe una asignatura con este nombre.'
        }
        )
    areas_planes_diferenciales_id = models.ForeignKey(AreasPlanesDiferenciales, on_delete=models.RESTRICT, blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True)
    color = models.CharField(max_length=7, default='#64748b')

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

    def __str__(self) -> str:
        return f'{self.ident} - {self.nombres_asignatura_id}'

class Usuario(AbstractUser):
    # Contraseña proporcionada por django
    name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    rut = models.CharField(max_length=10, unique=True, null=True,
        error_messages = {
            'unique': 'Ya existe un usuario con este RUT.'
        }
    )
    email = models.EmailField(max_length=254, unique=True,
        error_messages = {
            'unique': 'Ya existe un usuario con este correo.'
        }
    )
    telefono = models.CharField(max_length=12, blank=True, null=True)
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, null=True)
    avatar = models.ImageField(upload_to='avatars', blank=True, null=True)
    passwd_changed = models.BooleanField(default=False, blank=True)
    asignatura_id = models.ManyToManyField(Asignatura, blank=True, null=True)
    # abstractuser tiene campo is_active

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.rol = None
        self.save()

    def __str__(self) -> str:
        return f'{self.name} {self.last_name}'

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
    created_at = models.DateField(auto_now_add=True)
    
    def __str__(self) -> str:
        return f'{self.nivel} "{self.letra}"'

class Estudiante(models.Model):
    pk = models.CompositePrimaryKey('rut', 'curso_id')
    nombre = models.CharField(max_length=50)
    apellido_p = models.CharField(max_length=50)
    apellido_m = models.CharField(max_length=50)
    rut = models.CharField(max_length=10, unique=True,
        error_messages = {
                    'unique': 'Un estudiante ya está registrado con este RUT.'
                }    
        )
    promedio = models.FloatField(default=0, blank=True)
    curso_id = models.ForeignKey(Curso, on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True, blank=True)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()
    def __str__(self) -> str:
        return f'{self.nombre} {self.apellido_p} {self.apellido_m}'

class PromedioAsignatura(models.Model):
    nota = models.FloatField(null=True, blank=True)
    estudiante_id = models.ForeignKey(Estudiante, on_delete=models.CASCADE, to_field='rut')
    asignatura_id = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    curso_id = models.ForeignKey(Curso, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        valor = '—' if self.nota is None else self.nota
        return f'Nota de {self.estudiante_id} en {self.asignatura_id} ({self.curso_id}): {valor}'
    
class Aula(models.Model):
    nombre = models.CharField(max_length=50)
    cupos = models.IntegerField()
    curso_id = models.ManyToManyField(Curso, blank=True)
    created_at = models.DateField(auto_now_add=True)

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
    asignatura_id = models.ForeignKey(Asignatura, on_delete=models.RESTRICT)

    def __str__(self) -> str:
        return f'{self.curso_id}: {self.hrs_asignatura}hrs. {self.asignatura_id}'

class CargaHoraria(models.Model):
    usuario_id = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    hrs_contrato = models.FloatField()
    hrs_aula = models.FloatField(null=True, blank=True)
    hrs_cd = models.FloatField(null=True, blank=True)
    hrs_aa = models.FloatField(null=True, blank=True)
    anio_planificacion = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.usuario_id} - {self.hrs_contrato} hrs. Contrato - {self.hrs_aula} hrs. Aula / Planificación: {self.anio_planificacion}'

class Horario(models.Model):
    plan_de_estudio_id = models.ForeignKey(PlanDeEstudio, on_delete=models.RESTRICT)
    anio_planificacion = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f'Plan {self.plan_de_estudio_id}, Planificacion: {self.anio_planificacion}'

class BloqueDeClase(models.Model):
    horario_id = models.ForeignKey(Horario, on_delete=models.CASCADE, null=True, blank=True)
    usuario_id = models.ForeignKey(Usuario, on_delete=models.RESTRICT, null=True, blank=True)
    bloque_id = models.ForeignKey(Bloque, on_delete=models.RESTRICT)
    asignatura_id = models.ForeignKey(Asignatura, on_delete=models.RESTRICT)
    curso_id = models.ForeignKey(Curso, on_delete=models.RESTRICT)
    aula_id = models.ForeignKey(Aula, on_delete=models.RESTRICT, null=True, blank=True)

    def __str__(self) -> str:
        return f'({self.asignatura_id} / {self.curso_id} / {self.usuario_id}): {self.bloque_id}'

class BloqueNoLectivo(models.Model):
    class HoraNoLectiva(models.TextChoices):
        CD = 'CD', 'Carrera Docente'
        AA = 'AA', 'Atención Apoderados'

    tipo_hora = models.CharField(max_length=50, choices=HoraNoLectiva.choices)
    carga_horaria_id = models.ForeignKey(CargaHoraria, on_delete=models.CASCADE, null=True, blank=True)
    bloque_id = models.ForeignKey(Bloque, on_delete=models.RESTRICT)

    def __str__(self) -> str:
        return f'{self.tipo_hora}: ({self.bloque_id} / {self.carga_horaria_id})'