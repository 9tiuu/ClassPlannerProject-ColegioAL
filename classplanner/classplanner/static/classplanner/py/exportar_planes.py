import unicodedata
from openpyxl import load_workbook
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Alignment, Side, PatternFill
from openpyxl.utils import get_column_letter
from django.db.models.query import QuerySet
from django.utils import timezone
from django.http import HttpResponse
from openpyxl.worksheet.table import Table
from pathlib import Path
import ctypes.wintypes
from tempfile import NamedTemporaryFile

titulo_font = Font(
    name='Arial',
    size=16,
    bold=True,
    italic=False,
    vertAlign=None,
    underline='none',
    strike=False,
)
subtitle_font = Font(
    name='Arial',
    size=11,
    bold=True,
    italic=False,
    vertAlign=None,
    underline='none',
    strike=False,
)
center_align = Alignment(
    horizontal='center',
    vertical='center',
    indent=0
)

plan_table_border = Border(
    left=Side(style='thin', color='000000'),
    right=Side(style='thin', color='000000'),
    top=Side(style='thin', color='000000'),
    bottom=Side(style='thin', color='000000'),
)

asigns_1_4_b = {
    'Lenguaje y Comunicación': 8,
    'Lengua y Cultura Pueblos Originarios Ancestrales: Interculturalidad': '--',
    'Idioma Extranjero: Inglés': '--',
    'Matemática': 6,
    'Historia, Geografía y Ciencias Sociales': 3,
    'Ciencias Naturales': 3,
    'Artes Visuales': 2,
    'Música': 2,
    'Educación Física y Salud': 3,
    'Orientación': 0.5,
    'Tecnología': 0.5,
    'Religión': 2,
    'Libre Disposición': '--',
}

asigns_5_6_b = {
    'Lenguaje y Comunicación': 6,
    'Lengua y Cultura Pueblos Originarios Ancestrales: Interculturalidad': '--',
    'Idioma Extranjero: Inglés': 3,
    'Matemática': 6,
    'Historia, Geografía y Ciencias Sociales': 4,
    'Ciencias Naturales': 3,
    'Artes Visuales': 1,
    'Música': 1,
    'Educación Física y Salud': 2,
    'Orientación': 1,
    'Tecnología': 1,
    'Religión': 2,
    'Libre Disposición': '--',
}

asigns_7_8_b = {
    'Lengua y Literatura': 6,
    'Matemática': 6,
    'Historia, Geografía y Ciencias Sociales': 4,
    'Artes Visuales y Música': 2,
    'Educación Física y Salud': 2,
    'Orientación': 1,
    'Tecnología': 1,
    'Religión': 2,
    'Ciencias Naturales': 4,
    'Idioma Extranjero: Inglés': 3,
    'Libre Disposición': 2,
    'Libre Disposición (Tecnología)': '--',
    'Libre Disposición (Formación Ciudadana)': '--',
}

asigns_1_2_m = {
    'Lengua y Literatura': 6,
    'Matemática': 6,
    'Historia, Geografía y Ciencias Sociales': 4,
    'Artes Visuales y Música': 2,
    'Educación Física y Salud': 2,
    'Orientación': 1,
    'Tecnología': 1,
    'Religión': 2,
    'Ciencias Naturales': 6,
    'Idioma Extranjero: Inglés': 3,
    'Libre Disposición': '--',
}

asigns_3_m = {
    'Lengua y Literatura': 3,
    'Matemática': 3,
    'Educación Ciudadana': 2,
    'Idioma Extranjero: Inglés': 2,
    'Filosofía': 2,
    'Ciencias para la Ciudadanía': 2,
    'Plan Común Electivo: Religión': 2,
    'Plan Diferenciado': 18,
    'Libre Disposición': 2,
    'Libre Disposición: Matemática': '--',
    'Libre Disposición: Orientación': '--',
}

asigns_4_m = {
    'Lengua y Literatura': 3,
    'Matemática': 3,
    'Educación Ciudadana': 2,
    'Idioma Extranjero: Inglés': 2,
    'Filosofía': 2,
    'Ciencias para la Ciudadanía': 2,
    'Plan Común Electivo: Historia, Geografía y C. Sociales': 2,
    'Plan Diferenciado': 18,
    'Libre Disposición': 2,
    'Libre Disposición: Matemática': '--',
    'Libre Disposición: Orientación': '--',
}

MINEDUC_TEMPLATES = {
    '1°B': ('1°-4° Básico', asigns_1_4_b),
    '2°B': ('1°-4° Básico', asigns_1_4_b),
    '3°B': ('1°-4° Básico', asigns_1_4_b),
    '4°B': ('1°-4° Básico', asigns_1_4_b),
    '5°B': ('5°-6° Básico', asigns_5_6_b),
    '6°B': ('5°-6° Básico', asigns_5_6_b),
    '7°B': ('7°-8° Básico', asigns_7_8_b),
    '8°B': ('7°-8° Básico', asigns_7_8_b),
    '1°M': ('1°-2° Medio', asigns_1_2_m),
    '2°M': ('1°-2° Medio', asigns_1_2_m),
    '3°M': ('3° Medio', asigns_3_m),
    '4°M': ('4° Medio', asigns_4_m),
}


def exportar_planes(planes=QuerySet, lst_asignaturas=QuerySet):
    planes_exportados = list(planes.select_related('curso_id', 'asignatura_id'))
    cursos_por_grupo = {}
    horas_por_asignatura_y_curso = {}

    for plan in planes_exportados:
        curso_id = plan.curso_id_id
        nivel = plan.curso_id.nivel
        if nivel not in MINEDUC_TEMPLATES:
            raise ValueError(f'No hay una plantilla MINEDUC para el curso {nivel}')

        sheet_title, _ = MINEDUC_TEMPLATES[nivel]
        grupo = cursos_por_grupo.setdefault(
            sheet_title,
            {'courses': {}},
        )
        grupo['courses'].setdefault(curso_id, str(plan.curso_id))

        key = (str(plan.asignatura_id.nombre).lower(), curso_id)
        horas_por_asignatura_y_curso[key] = (
            horas_por_asignatura_y_curso.get(key, 0) + plan.hrs_asignatura
        )

    wb = Workbook(write_only=False)
    grupos_ordenados = []
    grupos_vistos = set()
    for sheet_title, template in MINEDUC_TEMPLATES.values():
        if sheet_title in cursos_por_grupo and sheet_title not in grupos_vistos:
            grupos_ordenados.append((sheet_title, template))
            grupos_vistos.add(sheet_title)

    if not grupos_ordenados:
        grupos_ordenados = [('1°-4° Básico', asigns_1_4_b)]
        cursos_por_grupo['1°-4° Básico'] = {
            'courses': {},
        }

    for index, (sheet_title, template) in enumerate(grupos_ordenados):
        group = cursos_por_grupo[sheet_title]
        cursos_ids = list(group['courses'])
        worksheet = wb.active if index == 0 else wb.create_sheet()
        create_file(
            wb,
            [group['courses'][cur_id] for cur_id in cursos_ids],
            worksheet=worksheet,
            sheet_title=sheet_title,
        )

        for row, (asign_nombre, horas_semanales_mineduc) in enumerate(
            template.items(),
            start=3,
        ):
            hrs_anuales = (
                horas_semanales_mineduc * 38
                if isinstance(horas_semanales_mineduc, (int, float))
                else horas_semanales_mineduc
            )
            worksheet.cell(row=row, column=1, value=asign_nombre)
            worksheet.cell(row=row, column=2, value=hrs_anuales)
            worksheet.cell(row=row, column=3, value=horas_semanales_mineduc)
            for column, cur_id in enumerate(cursos_ids, start=4):
                worksheet.cell(
                    row=row,
                    column=column,
                    value=horas_por_asignatura_y_curso.get(
                        ((asign_nombre).lower(), cur_id),
                        0
                    ),
                )

        total_row = len(template) + 3
        worksheet.cell(total_row, column=1, value='Total tiempo escolar')
        for column, cur_id in enumerate(cursos_ids, start=4):
            total = sum(
                horas_por_asignatura_y_curso.get(
                    ((asign_nombre).lower(), cur_id),
                    0
                )
                for asign_nombre in template
            )
            print("total : ",total)
            worksheet.cell(total_row, column=column, value=total)
            worksheet.cell(total_row, column=column).number_format = '#0'

        last_column = 3 + len(cursos_ids)
        for row in worksheet.iter_rows(
            min_row=1,
            max_row=total_row,
            min_col=1,
            max_col=max(3, last_column),
        ):
            for cell in row:
                cell.border = plan_table_border
                cell.font = Font(
                    name='Arial',
                    size=11,
                    bold=(
                        cell.row <= 2
                        or cell.row == total_row
                        or (cell.column >= 4 and cell.row >= 3)
                    ),
                    color='000000',
                )
                if cell.column >= 4 and cell.row >= 3:
                    cell.number_format = '#0'
                cell.alignment = Alignment(
                    horizontal='left'
                    if cell.column == 1 and cell.row >= 3
                    else 'center',
                    vertical='center',
                )
                if cell.row >= 3:
                    worksheet.row_dimensions[cell.row].height = 17

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=PlanesDeEstudio.xlsx'
    wb.save(response)
    return response

def create_file(
    wb=None,
    curso_names=None,
    worksheet=None,
    sheet_title='PlanesDeEstudio',
):
    if wb is None:
        wb = Workbook()
    if curso_names is None:
        curso_names = ('curso 1', 'curso 2')

    ws = worksheet or wb.active
    ws.title = sheet_title

    curso_names = list(curso_names)
    last_curso_column = max(4, 3 + len(curso_names))
    ws.merge_cells('A1:A2')
    ws.merge_cells('B1:C1')
    ws.merge_cells(
        start_row=1,
        start_column=4,
        end_row=1,
        end_column=last_curso_column,
    )
    ws['A1'] = 'Plan de Estudios'
    ws['B1'] = 'Horas pedagógicas\n(MINEDUC)'
    ws['B2'] = 'Anuales'
    ws['C2'] = 'Semanales'
    ws.cell(row=1, column=4, value='Horas pedagógicas semanales')

    for column, curso_name in enumerate(curso_names, start=4):
        ws.cell(row=2, column=column, value=curso_name[:-4].replace("B"," básico").replace("M"," medio"))

    ws.column_dimensions['A'].width = 38
    ws.column_dimensions['B'].width = 13
    ws.column_dimensions['C'].width = 13
    for column in range(4, last_curso_column + 1):
        ws.column_dimensions[get_column_letter(column)].width = 18
    for row in ws.iter_rows(
        min_row=1,
        max_row=2,
        min_col=1,
        max_col=last_curso_column,
    ):
        for cell in row:
            cell.border = plan_table_border
            cell.font = subtitle_font
            cell.alignment = Alignment(
                horizontal='center',
                vertical='center',
                wrap_text=True,
            )


    ws['B1'].alignment = Alignment(
        horizontal='center',
        vertical='center',
        wrap_text=True,
    )
    ws.row_dimensions[1].height = 36
    ws.row_dimensions[2].height = 18