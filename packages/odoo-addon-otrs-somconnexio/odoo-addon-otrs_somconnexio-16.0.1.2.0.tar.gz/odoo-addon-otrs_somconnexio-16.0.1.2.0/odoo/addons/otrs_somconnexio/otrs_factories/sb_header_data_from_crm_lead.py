from otrs_somconnexio.otrs_models.switchboard_header_data import SwitchboardHeaderData
from .base_data import BaseDataFromOdoo
from odoo.tools import html2plaintext


class SBHeaderDataFromCRMLead(BaseDataFromOdoo):
    DataModel = SwitchboardHeaderData

    def __init__(self, crm_lead):
        self.crm_lead = crm_lead

    def _get_data(self):
        return {
            "contact_phone": self.crm_lead.phone,
            "notes": html2plaintext(self.crm_lead.description),
            "email": self.crm_lead.email_from,
            "sales_team": self.crm_lead.team_id.code,
            "order_id": self.crm_lead.id,
            "technology": "Switchboard",
        }
