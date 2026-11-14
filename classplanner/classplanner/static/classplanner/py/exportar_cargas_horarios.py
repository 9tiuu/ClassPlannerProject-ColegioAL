from datetime import date, datetime, time
from html import escape
from io import BytesIO
from pathlib import Path
import colorsys

import reportlab
from django.core.exceptions import BadRequest
from django.db.models.query import QuerySet
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table as PDFTable,
    TableStyle as PDFTableStyle,
)

from classplanner.models import Bloque, BloqueDeClase
from core.middleware import constants

reportlab_fonts = Path(reportlab.__file__).parent / 'fonts'
pdfmetrics.registerFont(TTFont('Vera', str(reportlab_fonts / 'Vera.ttf')))
pdfmetrics.registerFont(TTFont('Vera-Bold', str(reportlab_fonts / 'VeraBd.ttf')))

DIAS = (
    ('L', 'Lunes'),
    ('M', 'Martes'),
    ('X', 'Miércoles'),
    ('J', 'Jueves'),
    ('V', 'Viernes'),
)
JORNADAS = (
    ('JM', 'J. Mañana'),
    ('JT', 'J. Tarde'),
)
COLORES = {
    'borde': colors.HexColor('#64748B'),
    'encabezado': colors.HexColor('#DDE3F8'),
    'encabezado_borde': colors.HexColor('#7488D5'),
    'recreo': colors.HexColor('#FFF4D6'),
}


def _format_pdf_value(value):
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _clasificar_jornada(hora_inicio):
    if time(7, 45) <= hora_inicio < time(13, 30):
        return 'JM'
    if time(14, 0) <= hora_inicio < time(19, 0):
        return 'JT'
    return None


def _es_recreo(bloque):
    inicio = datetime.combine(date.today(), bloque.hora_inicio)
    termino = datetime.combine(date.today(), bloque.hora_termino)
    return (termino - inicio).total_seconds() < 30 * 60


def _format_hora(hora):
    return hora.strftime('%H:%M')


def _build_jornada_table_data(jornada, bloques, clases):
    clases_jornada = [
        clase
        for clase in clases
        if _clasificar_jornada(clase.bloque_id.hora_inicio) == jornada
    ]
    if not clases_jornada:
        return None

    bloques_unicos = {}
    for bloque in bloques:
        if _clasificar_jornada(bloque.hora_inicio) == jornada:
            bloques_unicos.setdefault(
                (bloque.hora_inicio, bloque.hora_termino),
                bloque,
            )
    for clase in clases_jornada:
        bloque = clase.bloque_id
        bloques_unicos.setdefault(
            (bloque.hora_inicio, bloque.hora_termino),
            bloque,
        )

    bloques_ordenados = sorted(
        bloques_unicos.values(),
        key=lambda bloque: (bloque.hora_inicio, bloque.hora_termino),
    )
    clases_por_casilla = {}
    for clase in clases_jornada:
        bloque = clase.bloque_id
        clave = (
            bloque.dia,
            bloque.hora_inicio,
            bloque.hora_termino,
        )
        clases_por_casilla.setdefault(clave, []).append(clase)

    encabezado = [dict(JORNADAS)[jornada]] + [nombre for _, nombre in DIAS]
    filas = [encabezado]
    for numero, bloque in enumerate(bloques_ordenados, start=1):
        etiqueta_bloque = (
            f'Hora {numero}\n'
            f'{_format_hora(bloque.hora_inicio)} - {_format_hora(bloque.hora_termino)}'
        )
        if _es_recreo(bloque):
            filas.append([etiqueta_bloque, 'Recreo', '', '', '', ''])
            continue

        fila = [etiqueta_bloque]
        for codigo_dia, _ in DIAS:
            clave = (codigo_dia, bloque.hora_inicio, bloque.hora_termino)
            clases_casilla = clases_por_casilla.get(clave, [])
            fila.append(
                '\n'.join(
                    f'{clase.asignatura_id.ident}\n{clase.curso_id}'
                    for clase in clases_casilla
                )
            )
        filas.append(fila)
    return filas


def _cargar_bloques():
    return Bloque.objects.order_by('hora_inicio', 'hora_termino')


def _paragraph(value, style):
    text = escape(_format_pdf_value(value)).replace('\n', '<br/>')
    return Paragraph(text, style)


def _crear_tabla_jornada(jornada, bloques, clases, ancho, estilos):
    datos = _build_jornada_table_data(jornada, bloques, clases)
    if datos is None:
        return None

    filas = []
    for indice, fila in enumerate(datos):
        fila_parrafos = []
        for columna, valor in enumerate(fila):
            estilo = estilos['cabecera'] if indice == 0 else (
                estilos['bloque'] if columna == 0 else estilos['celda']
            )
            if indice and columna and valor and valor != 'Recreo':
                lineas = valor.split('\n')
                contenido = '<b>{}</b><br/>{}'.format(
                    escape(lineas[0]),
                    '<br/>'.join(escape(linea) for linea in lineas[1:]),
                )
                fila_parrafos.append(Paragraph(contenido, estilos['celda']))
            else:
                fila_parrafos.append(_paragraph(valor, estilo))
        filas.append(fila_parrafos)

    ancho_bloque = 96
    ancho_dia = (ancho - ancho_bloque) / len(DIAS)
    tabla = PDFTable(
        filas,
        colWidths=[ancho_bloque] + [ancho_dia] * len(DIAS),
        repeatRows=1,
        hAlign='LEFT',
    )
    estilo_tabla = [
        ('GRID', (0, 0), (-1, -1), 0.5, COLORES['borde']),
        ('BACKGROUND', (0, 0), (-1, 0), COLORES['encabezado']),
        ('BOX', (0, 0), (-1, 0), 0.8, COLORES['encabezado_borde']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    for indice, fila in enumerate(datos[1:], start=1):
        if len(fila) > 1 and fila[1] == 'Recreo':
            estilo_tabla.extend(
                [
                    ('SPAN', (1, indice), (-1, indice)),
                    ('BACKGROUND', (1, indice), (-1, indice), COLORES['recreo']),
                    ('ALIGN', (1, indice), (-1, indice), 'CENTER'),
                ]
            )
    tabla.setStyle(PDFTableStyle(estilo_tabla))
    return tabla


def _crear_tabla_resumen(filas, ancho, estilos):
    datos = [
        [
            _paragraph(etiqueta, estilos['etiqueta']),
            _paragraph(valor, estilos['valor']),
        ]
        for etiqueta, valor in filas
    ]
    tabla = PDFTable(
        datos,
        colWidths=[ancho * 0.52, ancho * 0.48],
        hAlign='LEFT',
    )
    tabla.setStyle(
        PDFTableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.45, COLORES['borde']),
                ('BACKGROUND', (0, 0), (-1, 0), COLORES['encabezado']),
                ('SPAN', (0, 0), (-1, 0)),
                ('FONTNAME', (0, 0), (-1, 0), 'Vera-Bold'),
                ('BOX', (0, 0), (-1, 0), 0.8, COLORES['encabezado_borde']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabla


def _crear_pagina_docente(carga, clases, bloques, ancho):
    docente = carga.usuario_id
    anio = carga.anio_planificacion
    jornadas_presentes = {
        _clasificar_jornada(clase.bloque_id.hora_inicio)
        for clase in clases
    }
    jornadas_texto = ' + '.join(
        codigo for codigo, _ in JORNADAS if codigo in jornadas_presentes
    ) or '—'
    estilo_titulo = ParagraphStyle(
        'CargaHorariaTitle',
        fontName='Vera-Bold',
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#344054'),
    )
    estilo_general = ParagraphStyle(
        'CargaHorariaText',
        fontName='Vera',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#344054'),
    )
    estilo_etiqueta = ParagraphStyle(
        'CargaHorariaLabel',
        parent=estilo_general,
        fontName='Vera-Bold',
    )
    estilo_celda = ParagraphStyle(
        'CargaHorariaCell',
        parent=estilo_general,
        fontSize=7,
        leading=8.5,
    )
    estilo_bloque = ParagraphStyle(
        'CargaHorariaBlock',
        parent=estilo_celda,
        fontName='Vera-Bold',
    )
    estilo_cabecera = ParagraphStyle(
        'CargaHorariaHeader',
        parent=estilo_general,
        fontName='Vera-Bold',
        fontSize=8,
        leading=10,
    )
    estilos = {
        'etiqueta': estilo_etiqueta,
        'valor': estilo_general,
        'celda': estilo_celda,
        'bloque': estilo_bloque,
        'cabecera': estilo_cabecera,
    }

    imagen_logo = Path(__file__).resolve().parents[1] / 'img' / 'export' / 'logo_bk.png'
    logo = Image(str(imagen_logo), width=112, height=28, kind='proportional')
    titulo = Paragraph(f'Carga Horaria {escape(_format_pdf_value(anio))}', estilo_titulo)
    encabezado = PDFTable(
        [[logo, titulo]],
        colWidths=[130, ancho - 130],
        hAlign='LEFT',
    )
    encabezado.setStyle(
        PDFTableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]
        )
    )

    horas_contrato = carga.hrs_contrato or 0
    horas_aula = carga.hrs_aula or 0
    horas_cd = carga.hrs_cd or 0
    horas_aa = carga.hrs_aa or 0
    horas_no_lectivas = horas_cd + horas_aa
    libre_disposicion = horas_contrato - horas_aula - horas_no_lectivas
    info_docente = _crear_tabla_resumen(
        [
            ('Información Docente', ''),
            ('Docente', f'{docente.name} {docente.last_name}'.strip()),
            ('RUT', docente.rut or '—'),
            ('Año', _format_pdf_value(anio) or '—'),
            ('Jornadas', jornadas_texto),
        ],
        ancho * 0.42,
        estilos,
    )
    distribucion_horas = _crear_tabla_resumen(
        [
            ('Distribución de horas', ''),
            ('Horas Contrato', _format_pdf_value(horas_contrato)),
            ('Horas Aula', _format_pdf_value(horas_aula)),
            ('Horas No Lectivas', _format_pdf_value(horas_no_lectivas)),
            ('Carrera Docente (CD)', _format_pdf_value(horas_cd)),
            ('Atención Apoderados (AA)', _format_pdf_value(horas_aa)),
            ('Libre Disposición', _format_pdf_value(libre_disposicion)),
        ],
        ancho * 0.56,
        estilos,
    )
    resumen = PDFTable(
        [[info_docente, '', distribucion_horas]],
        colWidths=[ancho * 0.42, ancho * 0.02, ancho * 0.56],
        hAlign='LEFT',
    )
    resumen.setStyle(
        PDFTableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]
        )
    )

    historia = [encabezado, Spacer(1, 15), resumen, Spacer(1, 24)]
    for codigo, _ in JORNADAS:
        tabla_jornada = _crear_tabla_jornada(
            codigo,
            bloques,
            clases,
            ancho,
            estilos,
        )
        if tabla_jornada is not None:
            historia.extend([tabla_jornada, Spacer(1, 18)])
    return historia


def _clases_para_carga(carga, bloques):
    return [
        clase
        for clase in bloques
        if clase.usuario_id_id == carga.usuario_id_id
        and clase.horario_id is not None
        and clase.horario_id.anio_planificacion == carga.anio_planificacion
    ]

# ----------------------------------- # CARGAS HORARIAS

def exportar_cargas(cargas: QuerySet, bloques: QuerySet):
    cargas_exportadas = list(
        cargas.select_related('usuario_id').order_by(
            'anio_planificacion',
            'usuario_id__name',
            'usuario_id__last_name',
        )
    )
    if not cargas_exportadas:
        raise BadRequest('No hay cargas horarias para exportar')

    bloques_exportados = list(
        bloques.select_related(
            'usuario_id',
            'bloque_id',
            'asignatura_id',
            'curso_id',
            'horario_id',
        ).order_by(
            'usuario_id__name',
            'bloque_id__hora_inicio',
            'bloque_id__dia',
            'asignatura_id__ident',
        )
    )
    bloques_disponibles = list(_cargar_bloques())

    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=34,
        rightMargin=34,
        topMargin=30,
        bottomMargin=30,
        title='Cargas Horarias',
    )
    ancho_disponible = letter[0] - document.leftMargin - document.rightMargin
    historia = []

    for indice, carga in enumerate(cargas_exportadas):
        if indice:
            historia.append(PageBreak())
        clases_docente = _clases_para_carga(carga, bloques_exportados)
        historia.extend(
            _crear_pagina_docente(
                carga,
                clases_docente,
                bloques_disponibles,
                ancho_disponible,
            )
        )

    document.build(historia)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    anios = sorted(
        {
            str(carga.anio_planificacion)
            for carga in cargas_exportadas
            if carga.anio_planificacion is not None
        }
    )
    anio_archivo = '-'.join(anios) or 'sin-anio'
    response['Content-Disposition'] = (
        f'attachment; filename=CargaHoraria_{anio_archivo}.pdf'
    )
    return response

# ----------------------------------- # HORARIOS

DIAS_HORARIO = (
    ('L', 'Lunes'),
    ('M', 'Martes'),
    ('X', 'Miércoles'),
    ('J', 'Jueves'),
    ('V', 'Viernes'),
)

asign_list = list(constants.ASIGNATURAS)
COLORES_ASIGNATURAS = (
    (asign_list[0], "#DF151576"),
    (asign_list[1], "#63311476"),
    (asign_list[2], "#C765147D"),
    (asign_list[3], "#0051FF7D"),
    (asign_list[4], "#63311476"),
    (asign_list[5], "#19A51478"),
    (asign_list[6], "#DF265D67"),
    (asign_list[7], "#7E1BAC7A"),
    (asign_list[8], "#1AC58C73"),
    (asign_list[9], "#DF153052"),
    (asign_list[10], "#DF153052"),
    (asign_list[11], "#701DCE7A"),
    (asign_list[12], "#DF151576"),
    (asign_list[13], "#DF265D67"),
    (asign_list[14], "#63311476"),
    (asign_list[15], "#E0DD2379"),
    (asign_list[16], "#63311476"),
    # Plan diferenciado: Artes
    (asign_list[17], "#E23D9076"),
    (asign_list[18], "#E23D9076"),
    (asign_list[19], "#E23D9076"),
    (asign_list[20], "#E23D9076"),
    (asign_list[21], "#E23D9076"),
    (asign_list[22], "#E23D9076"),
    # Plan diferenciado: Ciencias
    (asign_list[23], "#7EC4227D"),
    (asign_list[24], "#7EC4227D"),
    (asign_list[25], "#7EC4227D"),
    (asign_list[26], "#7EC4227D"),
    (asign_list[27], "#7EC4227D"),
    # Plan diferenciado: Educación Física y Salud
    (asign_list[28], "#167FA873"),
    (asign_list[29], "#167FA873"),
    (asign_list[30], "#167FA873"),
    # Plan diferenciado: Filosofía
    (asign_list[31], "#E0DD2379"),
    (asign_list[32], "#E0DD2379"),
    (asign_list[33], "#E0DD2379"),
    # Plan diferenciado: Historia, Geografía y Ciencias sociales
    (asign_list[34], "#C25A1F7A"),
    (asign_list[35], "#C25A1F7A"),
    (asign_list[36], "#C25A1F7A"),
    # Plan diferenciado: Lengua y Literatura
    (asign_list[37], "#CC0D0D7A"),
    (asign_list[38], "#CC0D0D7A"),
    (asign_list[39], "#CC0D0D7A"),
    # Plan diferenciado: Matemática
    (asign_list[40], "#0E4DD37D"),
    (asign_list[41], "#0E4DD37D"),
    (asign_list[42], "#0E4DD37D"),
    (asign_list[43], "#0E4DD37D"),
)

def _build_horario_table_data(bloques, clases, jornada):
    clases_jornada = [
        clase
        for clase in clases
        if _clasificar_jornada(clase.bloque_id.hora_inicio) == jornada
    ]
    if not clases_jornada:
        return []

    bloques_por_hora = {}
    for bloque in bloques:
        if _clasificar_jornada(bloque.hora_inicio) == jornada:
            bloques_por_hora.setdefault(
                (bloque.hora_inicio, bloque.hora_termino),
                bloque,
            )
    for clase in clases_jornada:
        bloque = clase.bloque_id
        bloques_por_hora.setdefault(
            (bloque.hora_inicio, bloque.hora_termino),
            bloque,
        )

    clases_por_casilla = {}
    for clase in clases_jornada:
        bloque = clase.bloque_id
        clases_por_casilla.setdefault(
            (bloque.dia, bloque.hora_inicio, bloque.hora_termino),
            [],
        ).append(clase)

    filas = [
        {
            'tipo': 'encabezado',
            'celdas': ['Hora'] + [nombre for _, nombre in DIAS_HORARIO],
        }
    ]
    bloques_ordenados = sorted(
        bloques_por_hora.values(),
        key=lambda bloque: (bloque.hora_inicio, bloque.hora_termino),
    )
    for bloque in bloques_ordenados:
        es_recreo = _es_recreo(bloque)
        filas.append(
            {
                'tipo': 'recreo' if es_recreo else 'bloque',
                'bloque': bloque,
                'celdas': (
                    []
                    if es_recreo
                    else [
                        clases_por_casilla.get(
                            (codigo_dia, bloque.hora_inicio, bloque.hora_termino),
                            [],
                        )
                        for codigo_dia, _ in DIAS_HORARIO
                    ]
                ),
            }
        )
    return filas


def _colores_asignaturas(clases):
    asignaturas = {
        clase.asignatura_id_id: str(clase.asignatura_id.nombre).encode()
        for clase in clases
    }
    ordenadas = sorted(asignaturas.items(), key=lambda item: (item[1], item[0]))
    colores_por_nombre = {
        str(nombre).encode(): colors.HexColor(color, hasAlpha=True)
        for nombre, color in COLORES_ASIGNATURAS
    }
    return {
        asignatura_id: colores_por_nombre.get(nombre)
        or colors.cadetblue
        for indice, (asignatura_id, nombre) in enumerate(ordenadas)
    }


def _paragraph_horario(texto, estilo):
    return Paragraph(escape(_format_pdf_value(texto)).replace('\n', '<br/>'), estilo)


def _crear_tabla_horario(
    horario,
    clases,
    bloques,
    jornada,
    anchos,
    estilos,
    colores_asignaturas,
    cargas_por_docente,
):
    filas_datos = _build_horario_table_data(bloques, clases, jornada)
    if not filas_datos:
        return None

    filas_pdf = []
    coordenadas_color = []
    for indice_fila, fila in enumerate(filas_datos):
        if fila['tipo'] == 'encabezado':
            filas_pdf.append(
                [
                    _paragraph_horario(valor, estilos['encabezado'])
                    for valor in fila['celdas']
                ]
            )
            continue

        bloque = fila['bloque']
        hora = (
            f'{_format_hora(bloque.hora_inicio)} - '
            f'{_format_hora(bloque.hora_termino)}'
        )
        if fila['tipo'] == 'recreo':
            filas_pdf.append(
                [_paragraph_horario(hora, estilos['hora']),
                 _paragraph_horario('Recreo', estilos['recreo']),
                 '', '', '', '']
            )
            continue

        celdas_pdf = [_paragraph_horario(hora, estilos['hora'])]
        for indice_dia, clases_celda in enumerate(fila['celdas'], start=1):
            if not clases_celda:
                celdas_pdf.append(_paragraph_horario('—', estilos['vacio']))
                continue

            contenidos = []
            for clase in clases_celda:
                asignatura = clase.asignatura_id
                docente = clase.usuario_id
                carga_docente = cargas_por_docente.get(
                    (clase.usuario_id_id, horario.anio_planificacion)
                )
                if carga_docente is not None:
                    docente = carga_docente.usuario_id
                nombre_docente = str(docente) if docente else ''
                aula = horario.aula_id.nombre if horario.aula_id else ''
                contenidos.append(
                    '<b>{}</b><br/><font size="6.5">'
                    'Prof.: {}<br/>Aula: {}</font>'.format(
                        escape(str(asignatura.nombre)),
                        escape(nombre_docente),
                        escape(str(aula)),
                    )
                )
                coordenadas_color.append(
                    (
                        indice_dia,
                        indice_fila,
                        colores_asignaturas[clase.asignatura_id_id],
                    )
                )
            celdas_pdf.append(
                Paragraph('<br/><br/>'.join(contenidos), estilos['asignatura'])
            )
        filas_pdf.append(celdas_pdf)

    tabla = PDFTable(
        filas_pdf,
        colWidths=anchos,
        repeatRows=1,
        hAlign='LEFT',
    )
    estilos_tabla = [
        ('GRID', (0, 0), (-1, -1), 0.7, colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#244E9A')),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.white),
    ]
    for columna, fila, color_fondo in coordenadas_color:
        estilos_tabla.append(
            ('BACKGROUND', (columna, fila), (columna, fila), color_fondo)
        )

    indice_fila = 1
    for fila in filas_datos[1:]:
        if fila['tipo'] == 'recreo':
            estilos_tabla.extend(
                [
                    ('SPAN', (1, indice_fila), (-1, indice_fila)),
                    ('BACKGROUND', (1, indice_fila), (-1, indice_fila), colors.HexColor('#FDE68A')),
                    ('TEXTCOLOR', (1, indice_fila), (-1, indice_fila), colors.HexColor('#713F12')),
                ]
            )
        indice_fila += 1
    tabla.setStyle(PDFTableStyle(estilos_tabla))
    return tabla


def _crear_pagina_horario(curso, horario, clases, bloques, ancho, colores_asignaturas, cargas_por_docente):
    estilos = {
        'titulo': ParagraphStyle(
            'HorarioTitulo',
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=29,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#182230'),
        ),
        'encabezado': ParagraphStyle(
            'HorarioEncabezado',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.white,
        ),
        'hora': ParagraphStyle(
            'HorarioHora',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1F2937'),
        ),
        'asignatura': ParagraphStyle(
            'HorarioAsignatura',
            fontName='Vera',
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#172033'),
        ),
        'vacio': ParagraphStyle(
            'HorarioVacio',
            fontName='Vera',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6B7280'),
        ),
        'recreo': ParagraphStyle(
            'HorarioRecreo',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#713F12'),
        ),
        'detalle': ParagraphStyle(
            'HorarioDetalle',
            fontName='Vera',
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#344054'),
        ),
    }
    estilos['detalle_derecha'] = ParagraphStyle(
        'HorarioDetalleDerecha',
        parent=estilos['detalle'],
        alignment=TA_RIGHT,
    )

    ruta_logo = Path(__file__).resolve().parents[1] / 'img' / 'export' / 'logo_bk.png'
    logo = Image(str(ruta_logo), width=112, height=28, kind='proportional')
    titulo = Paragraph(
        f'Horario {escape(_format_pdf_value(horario.anio_planificacion))}',
        estilos['titulo'],
    )
    ancho_columna = ancho / 3
    encabezado = PDFTable(
        [[logo, titulo, '']],
        colWidths=[ancho_columna] * 3,
        hAlign='LEFT',
    )
    encabezado.setStyle(
        PDFTableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]
        )
    )
    profesor_jefe = str(curso.usuario_id) if curso.usuario_id else 'Sin asignar'
    detalles = PDFTable(
        [[
            _paragraph_horario(f'Curso: {curso}', estilos['detalle']),
            _paragraph_horario(
                f'Profesor(a) jefe: {profesor_jefe}',
                estilos['detalle_derecha'],
            ),
        ]],
        colWidths=[ancho / 2, ancho / 2],
    )
    detalles.setStyle(
        PDFTableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]
        )
    )

    ancho_hora = 68
    anchos_columnas = [ancho_hora] + [
        (ancho - ancho_hora) / len(DIAS_HORARIO)
    ] * len(DIAS_HORARIO)
    jornadas_presentes = [
        codigo
        for codigo, _ in JORNADAS
        if any(
            _clasificar_jornada(clase.bloque_id.hora_inicio) == codigo
            for clase in clases
        )
    ]
    if not jornadas_presentes:
        return [
            encabezado,
            Spacer(1, 13),
            detalles,
            Spacer(1, 6),
            _paragraph_horario(
                'No hay clases asignadas para este horario.',
                estilos['detalle'],
            ),
        ]

    historia = []
    for indice, jornada in enumerate(jornadas_presentes):
        tabla_horario = _crear_tabla_horario(
            horario,
            clases,
            bloques,
            jornada,
            anchos_columnas,
            estilos,
            colores_asignaturas,
            cargas_por_docente,
        )
        if tabla_horario is None:
            continue
        if indice:
            historia.append(PageBreak())
        historia.extend(
            [
                encabezado,
                Spacer(1, 13),
                detalles,
                Spacer(1, 6),
                tabla_horario,
            ]
        )
    return historia


def exportar_horarios(cursos, cargas: QuerySet, bloques: QuerySet):
    cursos_exportados = list(cursos)
    if not cursos_exportados:
        raise BadRequest('No hay horarios para exportar')

    cargas_exportadas = list(cargas.select_related('usuario_id'))
    bloques_exportados = list(
        bloques.select_related(
            'usuario_id',
            'bloque_id',
            'asignatura_id',
            'curso_id',
            'horario_id__aula_id',
        ).order_by(
            'bloque_id__hora_inicio',
            'bloque_id__dia',
            'asignatura_id__nombre',
        )
    )
    bloques_disponibles = list(_cargar_bloques())
    colores_asignaturas = _colores_asignaturas(bloques_exportados)
    cargas_por_docente = {
        (carga.usuario_id_id, carga.anio_planificacion): carga
        for carga in cargas_exportadas
    }

    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(A4),
        leftMargin=28,
        rightMargin=28,
        topMargin=24,
        bottomMargin=24,
        title='Horarios de cursos',
    )
    ancho_disponible = landscape(A4)[0] - document.leftMargin - document.rightMargin
    historia = []

    for indice, curso in enumerate(cursos_exportados):
        if indice:
            historia.append(PageBreak())
        horario = curso.horario_export
        clases_curso = [
            clase
            for clase in bloques_exportados
            if clase.curso_id_id == curso.pk
            and clase.horario_id_id == horario.pk
        ]
        historia.extend(
            _crear_pagina_horario(
                curso,
                horario,
                clases_curso,
                bloques_disponibles,
                ancho_disponible,
                colores_asignaturas,
                cargas_por_docente,
            )
        )

    document.build(historia)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    anios = sorted(
        {
            str(curso.horario_export.anio_planificacion)
            for curso in cursos_exportados
            if curso.horario_export.anio_planificacion is not None
        }
    )
    anio_archivo = '-'.join(anios) or 'sin-anio'
    response['Content-Disposition'] = (
        f'attachment; filename=Horarios_{anio_archivo}.pdf'
    )
    return response
