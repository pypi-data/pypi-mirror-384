from odoo.addons.somconnexio.tests.sc_test_case import SCTestCase
from odoo.addons.switchboard_somconnexio.tests.helper_service import crm_lead_create
from ...otrs_factories.sb_header_data_from_crm_lead import SBHeaderDataFromCRMLead
from odoo.tools import html2plaintext


class SBHeaderDataFromCRMLeadTest(SCTestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.partner_id = self.browse_ref("somconnexio.res_partner_2_demo")

    def test_build(self):
        description = "<p>Header activation notes to consider</p>"
        service_type = "switchboard"
        sb_crm_lead = crm_lead_create(self.env, self.partner_id, service_type)
        sb_crm_lead.description = description
        lead_data = SBHeaderDataFromCRMLead(sb_crm_lead).build()

        self.assertEqual(lead_data.order_id, sb_crm_lead.id)
        self.assertEqual(lead_data.sales_team, sb_crm_lead.team_id.name)
        self.assertEqual(lead_data.service_type, "header_switchboard")
        self.assertEqual(lead_data.contact_phone, sb_crm_lead.phone)
        self.assertEqual(lead_data.email, sb_crm_lead.email_from)
        self.assertEqual(lead_data.notes, html2plaintext(description))
