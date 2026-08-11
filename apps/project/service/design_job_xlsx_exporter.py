from collections import defaultdict
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


class DesignJobXlsxExporter:
    SHEET_NAME = "测试用例-全量"
    HEADERS = ["用例编号", "测试模块", "测试场景", "关联数据表", "关联字段",
               "前置条件", "测试步骤", "预期结果", "优先级", "用例类型"]
    COLUMN_WIDTHS = [16, 16, 28, 20, 22, 24, 52, 52, 8, 10]
    PRIORITY_STYLE_MAP = {"P0": 2, "P1": 3, "P2": 4}

    @classmethod
    def build_workbook(cls, job, testcases=None):
        rows = cls._extract_rows(job, testcases=testcases)
        return cls._build_xlsx_bytes(cls.SHEET_NAME, cls.HEADERS, rows, cls.COLUMN_WIDTHS)

    @classmethod
    def _extract_rows(cls, job, testcases=None):
        structured_result = getattr(job, "structured_result", None) or {}
        rows = structured_result.get("rows")
        if isinstance(rows, list) and rows:
            return [cls._normalize_row(row, index=i) for i, row in enumerate(rows, 1)]
        if testcases:
            return [cls._normalize_row({
                "case_no": f"TC-FUNC-{i:03d}",
                "module_name": getattr(getattr(tc, "suite", None), "module", None) and tc.suite.module.name or "",
                "scenario": tc.description or tc.name,
                "description": tc.description or tc.name,
                "preconditions": tc.preconditions,
                "steps": tc.steps,
                "expected_result": tc.expected_result,
                "priority": "P1",
                "case_type": "功能测试",
            }, index=i) for i, tc in enumerate(testcases, 1)]
        return []

    @classmethod
    def _normalize_row(cls, row, *, index):
        return {
            "case_no": cls._cl(row.get("case_no")) or f"TC-FUNC-{index:03d}",
            "module_name": cls._cl(row.get("module_name")) or "",
            "scenario": cls._cl(row.get("scenario") or row.get("name") or row.get("description")),
            "related_tables": cls._cl(row.get("related_tables") or row.get("tables") or ""),
            "related_fields": cls._cl(row.get("related_fields") or row.get("fields") or ""),
            "preconditions": cls._cl(row.get("preconditions")),
            "steps": cls._cm(row.get("steps")),
            "expected_result": cls._cm(row.get("expected_result")),
            "priority": cls._cl(row.get("priority")) or "P1",
            "case_type": cls._cl(row.get("case_type")) or "功能测试",
        }

    @classmethod
    def _build_xlsx_bytes(cls, sheet_name, headers, rows, column_widths):
        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as wb:
            wb.writestr("[Content_Types].xml", cls._content_types_xml())
            wb.writestr("_rels/.rels", cls._root_rels_xml())
            wb.writestr("xl/workbook.xml", cls._workbook_xml(sheet_name))
            wb.writestr("xl/_rels/workbook.xml.rels", cls._workbook_rels_xml())
            wb.writestr("xl/styles.xml", cls._styles_xml())
            wb.writestr("xl/worksheets/sheet1.xml", cls._worksheet_xml(headers, rows, column_widths))
        return buffer.getvalue()

    @classmethod
    def _worksheet_xml(cls, headers, rows, column_widths):
        xml_rows = [cls._build_row(1, headers, style_ids=[1] * len(headers))]
        for index, row in enumerate(rows, start=2):
            style_ids = [0, 0, 0, 0, 0, 0, 0, 0, cls.PRIORITY_STYLE_MAP.get(row["priority"], 0), 0]
            xml_rows.append(cls._build_row(index, cls._row_values(row), style_ids=style_ids))
        cols_xml = "".join(
            '<col min="%d" max="%d" width="%d" customWidth="1"/>' % (i, i, w)
            for i, w in enumerate(column_widths, start=1)
        )
        sheet_dim = "A1:%s%d" % (cls._column_letter(len(headers)), len(rows) + 1)
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<dimension ref="%s"/>'
                '<sheetViews><sheetView tabSelected="1" workbookViewId="0">'
                '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
                '</sheetView></sheetViews>'
                '<sheetFormatPr defaultColWidth="9" defaultRowHeight="13.5"/>'
                '<cols>%s</cols><sheetData>%s</sheetData></worksheet>') % (
                sheet_dim, cols_xml, "".join(xml_rows))

    @classmethod
    def _build_row(cls, row_number, values, style_ids):
        cells = []
        for column_index, value in enumerate(values, start=1):
            cell_ref = "%s%d" % (cls._column_letter(column_index), row_number)
            style_id = style_ids[column_index - 1] if column_index - 1 < len(style_ids) else 0
            cell_text = escape("" if value is None else str(value))
            cells.append(
                '<c r="%s" t="inlineStr" s="%d"><is><t xml:space="preserve">%s</t></is></c>' % (
                    cell_ref, style_id, cell_text))
        row_height = 28 if row_number == 1 else 60
        return '<row r="%d" ht="%d" customHeight="1">%s</row>' % (row_number, row_height, "".join(cells))

    @staticmethod
    def _row_values(row):
        return [row["case_no"], row["module_name"], row["scenario"],
                row.get("related_tables", ""), row.get("related_fields", ""),
                row["preconditions"], row["steps"], row["expected_result"],
                row["priority"], row["case_type"]]

    @staticmethod
    def _column_letter(column_number):
        letters = []
        while column_number > 0:
            column_number, remainder = divmod(column_number - 1, 26)
            letters.append(chr(65 + remainder))
        return "".join(reversed(letters))

    @staticmethod
    def _cl(value):
        if value is None: return ""
        return str(value).strip()

    @staticmethod
    def _cm(value):
        if value is None: return ""
        if isinstance(value, list):
            return "\n".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip()

    @staticmethod
    def _content_types_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>')

    @staticmethod
    def _root_rels_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')

    @staticmethod
    def _workbook_xml(sheet_name):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="%s" sheetId="1" r:id="rId1"/></sheets></workbook>') % escape(sheet_name)

    @staticmethod
    def _workbook_rels_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>')

    @staticmethod
    def _styles_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="2">'
            '<font><sz val="11"/><name val="Calibri"/></font>'
            '<font><b/><sz val="11"/><name val="Calibri"/></font>'
            '</fonts>'
            '<fills count="5">'
            '<fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FFDCEBFA"/></patternFill></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FFF4CCCC"/></patternFill></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FFFCE5CD"/></patternFill></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FFD9EAD3"/></patternFill></fill>'
            '</fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="5">'
            '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="1" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
            '<xf numFmtId="0" fontId="0" fillId="2" borderId="0" xfId="0" applyFill="1"/>'
            '<xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1"/>'
            '<xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1"/>'
            '</cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>')
