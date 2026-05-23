import xmlrpc.client
import os
import logging

logger = logging.getLogger(__name__)


class OdooConnector:
    """Verbindt met Odoo via XML-RPC om klanten en projecten op te halen."""

    def _connect(self):
        url = os.getenv("ODOO_URL", "")
        db = os.getenv("ODOO_DB", "")
        username = os.getenv("ODOO_USERNAME", "")
        password = os.getenv("ODOO_PASSWORD", "")

        if not url or not username or not password:
            logger.warning("Odoo niet geconfigureerd: URL=%s user=%s wachtwoord=%s",
                           bool(url), bool(username), bool(password))
            return None, None, None, None

        try:
            common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
            uid = common.authenticate(db, username, password, {})
            if not uid:
                logger.error("Odoo authenticatie mislukt voor gebruiker %s", username)
                return None, None, None, None
            return url, db, uid, password
        except Exception as e:
            logger.error("Odoo verbindingsfout: %s", e)
            return None, None, None, None

    def get_partners(self, search=""):
        url, db, uid, password = self._connect()
        if not uid:
            return []
        try:
            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
            domain = [["is_company", "=", True], ["active", "=", True]]
            if search:
                domain.append(["name", "ilike", search])
            return models.execute_kw(
                db, uid, password,
                "res.partner", "search_read",
                [domain],
                {"fields": ["id", "name", "street", "zip", "city"], "limit": 50, "order": "name asc"},
            )
        except Exception as e:
            logger.error("Odoo get_partners fout: %s", e)
            return []

    def get_projects(self, search=""):
        url, db, uid, password = self._connect()
        if not uid:
            return []
        try:
            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
            domain = [["active", "=", True]]
            if search:
                domain.append(["name", "ilike", search])
            return models.execute_kw(
                db, uid, password,
                "project.project", "search_read",
                [domain],
                {"fields": ["id", "name"], "limit": 50, "order": "name asc"},
            )
        except Exception as e:
            logger.error("Odoo get_projects fout: %s", e)
            return []

    @property
    def configured(self):
        return bool(os.getenv("ODOO_URL") and os.getenv("ODOO_USERNAME") and os.getenv("ODOO_PASSWORD"))
