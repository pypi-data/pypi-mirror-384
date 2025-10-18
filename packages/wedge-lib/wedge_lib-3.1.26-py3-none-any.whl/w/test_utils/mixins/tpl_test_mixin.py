from w.services.technical.models.tpl_models import TplSettings
from w.services.technical.tpl_service import TplService


class TplTestMixin:
    def setup_tpl_data(self, tpl_settings: TplSettings | None = None):
        sql = self.get_dataset(f"tpl/{tpl_settings.relative_dump_sql_filename}")
        conn = TplService._get_tpl_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
        finally:
            TplService._close_conn(conn)
