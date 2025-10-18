try:
    from docxtpl import DocxTemplate
except Exception:  # pragma: no cover
    raise ImportError("docxtpl missing run: poetry add docxtpl")

from w.services.abstract_service import AbstractService
from w.services.technical.filesystem_service import FilesystemService
from w.services.technical.models.docx_tpl import DocxTpl


class DocxTplService(AbstractService):
    @staticmethod
    def render(docx_tpl: DocxTpl) -> None:
        FilesystemService.check_file_exists(docx_tpl.template_filename)
        FilesystemService.create_missing(docx_tpl.output_filename)
        tpl = DocxTemplate(docx_tpl.template_filename)
        tpl.render(docx_tpl.context)
        tpl.save(docx_tpl.output_filename)
