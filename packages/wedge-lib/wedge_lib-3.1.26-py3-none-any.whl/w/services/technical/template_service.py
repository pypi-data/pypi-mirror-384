from django.template.loader import render_to_string

from w.services.abstract_service import AbstractService


class TemplateService(AbstractService):
    @staticmethod
    def render_template(template_name, context=None):
        """
        Render mail template
        """
        return render_to_string(template_name, context)
