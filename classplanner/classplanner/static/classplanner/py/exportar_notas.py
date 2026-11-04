from html import escape
from io import BytesIO
from pathlib import Path
import locale
locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')

import reportlab
from django.core.exceptions import BadRequest
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils import timezone
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table as PDFTable,
    TableStyle as PDFTableStyle,
)

reportlab_fonts = Path(reportlab.__file__).parent / 'fonts'
pdfmetrics.registerFont(TTFont('Vera', str(reportlab_fonts / 'Vera.ttf')))
pdfmetrics.registerFont(TTFont('Vera-Bold', str(reportlab_fonts / 'VeraBd.ttf')))


def _format_pdf_value(value):
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _build_grade_table_data(notas, promedio_general, asistencia):
    asignaturas = {}
    for nota in notas:
        asignatura = nota.asignatura_id
        asignatura_data = asignaturas.setdefault(
            nota.asignatura_id_id,
            {
                'asignatura': asignatura,
                'notas': [],
            },
        )
        asignatura_data['notas'].append(nota.nota)

    asignaturas_ordenadas = sorted(
        asignaturas.values(),
        key=lambda item: (
            item['asignatura'].plan_diferencial is not None,
            str(item['asignatura'].nombre).casefold(),
        ),
    )
    cantidad_notas = min(
        max((len(item['notas']) for item in asignaturas_ordenadas), default=0),
        8,
    )
    table_data = [
        ['Asignaturas']
        + [str(numero) for numero in range(1, cantidad_notas + 1)]
        + ['Prom.']
    ]

    for item in asignaturas_ordenadas:
        notas_asignatura = item['notas']
        notas_validas = [valor for valor in notas_asignatura if valor is not None]
        promedio = (
            _format_pdf_value(round(sum(notas_validas) / len(notas_validas), 1))
            if notas_validas
            else ''
        )
        notas_visibles = [
            _format_pdf_value(valor) for valor in notas_asignatura[:cantidad_notas]
        ]
        notas_visibles.extend([''] * (cantidad_notas - len(notas_visibles)))
        table_data.append(
            [item['asignatura'].nombre] + notas_visibles + [promedio]
        )

    table_data.append(
        ['PROMEDIO GENERAL']
        + [''] * cantidad_notas
        + [_format_pdf_value(promedio_general)]
    )
    table_data.append(
        ['% ASISTENCIA']
        + [''] * cantidad_notas
        + [_format_pdf_value(asistencia)]
    )
    return table_data, cantidad_notas


def _exportar_notas_pdf(
    notas: QuerySet,
    estudiante: QuerySet,
    semestre: int,
    asistencia=None,
    observacion='',
):
    if semestre == 1:
        semestre_texto = 'PRIMER SEMESTRE'
    elif semestre == 2:
        semestre_texto = 'SEGUNDO SEMESTRE'
    else:
        raise BadRequest('No se pudo completar la exportación')

    notas_exportadas = list(
        notas.select_related('asignatura_id').order_by('pk')
    )
    estudiante_exportado = estudiante.select_related(
        'curso_id__usuario_id'
    ).get()
    tabla_datos, cantidad_notas = _build_grade_table_data(
        notas_exportadas,
        estudiante_exportado.promedio,
        asistencia,
    )

    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=75,
        rightMargin=75,
        topMargin=66,
        bottomMargin=90,
        title=f'INFORME DE NOTAS {semestre_texto}',
    )
    ancho_disponible = letter[0] - document.leftMargin - document.rightMargin

    title_style = ParagraphStyle(
        'CertificateTitle',
        fontName='Vera-Bold',
        fontSize=10,
        spaceBefore=20,
        leading=12,
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        'CertificateBody',
        fontName='Vera',
        fontSize=8.5,
        leading=12,
        alignment=TA_JUSTIFY,
    )
    left_style = ParagraphStyle(
        'TeacherName',
        fontName='Vera',
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
    )
    table_header_style = ParagraphStyle(
        'GradeTableHeader',
        fontName='Vera-Bold',
        fontSize=7.5,
        leading=9,
        alignment=TA_CENTER,
    )
    table_cell_style = ParagraphStyle(
        'GradeTableCell',
        fontName='Vera',
        fontSize=7.5,
        leading=9,
        alignment=TA_CENTER,
    )
    table_subject_style = ParagraphStyle(
        'GradeTableSubject',
        fontName='Vera',
        fontSize=7.5,
        leading=9,
        alignment=TA_LEFT,
    )
    table_label_style = ParagraphStyle(
        'GradeTableLabel',
        fontName='Vera-Bold',
        fontSize=7.5,
        leading=9,
        alignment=TA_LEFT,
    )

    def paragraph(value, style):
        escaped_value = escape(_format_pdf_value(value)).replace('\n', '<br/>')
        return Paragraph(escaped_value, style)

    image_directory = Path(__file__).resolve().parents[1] / 'img'
    logo = Image(
        str(image_directory / 'export' / 'logo_bk.png'),
        width=132*0.5,
        height=37*0.5,
    )
    header = PDFTable(
        [
            [logo],
            [paragraph(f'INFORME DE NOTAS {semestre_texto}', title_style)],
        ],
        colWidths=[ancho_disponible],
    )
    header.setStyle(
        PDFTableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (0, 1), (0, 1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (0, 0), 0),
                ('TOPPADDING', (0, 1), (0, 1), 0),
            ]
        )
    )

    estudiante_nombre = ' '.join(
        (
            estudiante_exportado.nombre,
            estudiante_exportado.apellido_p,
            estudiante_exportado.apellido_m,
        )
    )
    curso = estudiante_exportado.curso_id
    texto_certificado = (
        'RECONOCIDO OFICIALMENTE POR EL MINISTERIO DE EDUCACIÓN DE LA '
        'RESPÚBLICA DE CHILE SEGÚN Res. Rec. Oficial/Doc. Traspaso N°409 DEL '
        'AÑO 1982 ROL BASE DE DATOS N°67-1 OTORGA EL PRESENTE CERTIFICADO DE '
        f'CALIFICACIONES SEMESTRALES A DON(A) {estudiante_nombre} DEL '
        f'{curso.nivel} {curso.letra} DE ACUERDO AL PLAN Y PROGRAMAS DE '
        'ESTUDIOS APROBADOS POR DECRETO DE EDUCACIÓN N°193 DE 2019 Y '
        'REGLAMENTO DE EVALUACIÓN Y PROMOCIÓN ESCOLAR DTO. EXENTO N°67 DE 2018.'
    )
    historia = [
        header,
        Spacer(1, 12),
        paragraph(texto_certificado, body_style),
        Spacer(1, 8),
        paragraph(
            f'Profesor Jefe: {curso.usuario_id}',
            left_style,
        ),
        Spacer(1, 12),
    ]

    ancho_asignatura = ancho_disponible * 0.44
    ancho_promedio = 48
    ancho_nota = (
        (ancho_disponible - ancho_asignatura - ancho_promedio) / cantidad_notas
        if cantidad_notas
        else 0
    )
    anchos_columnas = (
        [ancho_asignatura]
        + [ancho_nota] * cantidad_notas
        + [ancho_promedio]
    )
    datos_tabla = []
    for row_index, fila in enumerate(tabla_datos):
        datos_tabla.append(
            [
                paragraph(
                    valor,
                    table_header_style
                    if row_index == 0
                    else table_label_style
                    if columna == 0 and fila[0] in ('PROMEDIO GENERAL', '% ASISTENCIA')
                    else table_subject_style
                    if columna == 0
                    else table_cell_style,
                )
                for columna, valor in enumerate(fila)
            ]
        )

    tabla = PDFTable(
        datos_tabla,
        colWidths=anchos_columnas,
        repeatRows=1,
        hAlign='CENTER',
    )
    estilos_tabla = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.transparent),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('FONTNAME', (0, 0), (-1, 0), 'Vera-Bold'),
    ]
    for row_index, fila in enumerate(tabla_datos):
        if fila[0] in ('PROMEDIO GENERAL', '% ASISTENCIA'):
            estilos_tabla.extend(
                [
                    ('FONTNAME', (0, row_index), (-1, row_index), 'Vera-Bold'),
                    ('BACKGROUND', (0, row_index), (-1, row_index), colors.transparent),
                ]
            )
    tabla.setStyle(PDFTableStyle(estilos_tabla))
    historia.extend(
        [
            tabla,
            Spacer(1, 12),
            paragraph(f'Observaciones: {observacion or ""}', body_style),
        ]
    )

    hoy = timezone.localdate()
    with PILImage.open(image_directory / 'export' / 'escudo.png') as monkey_image:
        monkey_background = monkey_image.convert('RGBA')
    monkey_background.putalpha(38) # Imagen con 15% opacidad
    monkey_buffer = BytesIO()
    monkey_background.save(monkey_buffer, format='PNG')
    monkey_buffer.seek(0)
    monkey_background_reader = ImageReader(monkey_buffer)

    def dibujar_pie(canvas, doc):
        canvas.saveState()
        canvas.drawImage(
            monkey_background_reader,
            0,
            0,
            width=letter[0],
            height=letter[1],
            mask='auto',
        )
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.5)
        firma_y = 100
        firma_ancho = 135
        izquierda = doc.leftMargin + 8
        derecha = letter[0] - doc.rightMargin - firma_ancho - 8
        canvas.line(izquierda, firma_y, izquierda + firma_ancho, firma_y)
        canvas.line(derecha, firma_y, derecha + firma_ancho, firma_y)
        canvas.setFont('Vera', 8)
        canvas.drawCentredString(
            izquierda + firma_ancho / 2,
            firma_y - 16,
            'Profesor Jefe',
        )
        canvas.drawCentredString(
            derecha + firma_ancho / 2,
            firma_y - 16,
            'Director',
        )
        canvas.drawRightString(
            letter[0] - doc.rightMargin,
            20,
            f'Arica, {hoy.day} de {hoy.strftime("%B")} de {hoy.year}',
        )
        canvas.restoreState()

    document.build(
        historia,
        onFirstPage=dibujar_pie,
        onLaterPages=dibujar_pie,
    )
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=InformeDeNotas_{estudiante_nombre}.pdf'
    return response
