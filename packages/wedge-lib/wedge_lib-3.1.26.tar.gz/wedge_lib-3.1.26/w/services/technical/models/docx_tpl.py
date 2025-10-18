from pydantic import BaseModel

FullPath = str


class DocxTpl(BaseModel):
    template_filename: FullPath
    output_filename: FullPath
    context: dict
