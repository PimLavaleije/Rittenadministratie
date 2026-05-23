import xmlrpc.client
import os


class OdooConnector:
    """Verbindt met Odoo via XML-RPC om klanten en projecten op te halen."""

    def __init__(self):
        self.url = os.getenv("ODOO_URL", "")
        self.db = os.getenv("ODOO_DB", "")
        self.username = os.getenv("ODOO_USERNAME", "")
        self.password = os.getenv("ODOO_PASSWORD", "")
        self._uid = None

    def _connect(self):
        if not self.url or not self.username:
            return False
        try:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self._uid = common.authenticate(self.db, self.username, self.password, {})
            return bool(self._uid)
        except Exception:
            return False

    def _models(self):
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def get_partners(self, search=""):
        if not self._connect():
            return []
        try:
            domain = [["is_company", "=", True], ["active", "=", True]]
            if search:
                domain.append(["name", "ilike", search])
            result = self._models().execute_kw(
                self.db, self._uid, self.password,
                "res.partner", "search_read",
                [domain],
                {"fields": ["id", "name", "email"], "limit": 50, "order": "name asc"},
            )
            return result
        except Exception:
            return []

    def get_projects(self, search=""):
        if not self._connect():
            return []
        try:
            domain = [["active", "=", True]]
            if search:
                domain.append(["name", "ilike", search])
            result = self._models().execute_kw(
                self.db, self._uid, self.password,
                "project.project", "search_read",
                [domain],
                {"fields": ["id", "name"], "limit": 50, "order": "name asc"},
            )
            return result
        except Exception:
            return []

    @property
    def configured(self):
        return bool(self.url and self.username and self.password)
