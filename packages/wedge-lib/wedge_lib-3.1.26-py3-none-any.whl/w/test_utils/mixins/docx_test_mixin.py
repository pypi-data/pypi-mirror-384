try:
    import docx2txt
except Exception:
    raise ImportError("docx2txt missing run: poetry add -D docx2txt")


class DocxTestMixin:
    @staticmethod
    def docx_to_list(docx_filename) -> list:
        # cette lib fait un job approximatif qui ajoute des lignes vide et des
        # tabulations => on supprime toutes les lignes vides et les tab par paires
        return [
            r
            for r in docx2txt.process(docx_filename).replace("\t\t", "").split("\n")
            if r
        ]
