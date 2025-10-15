from unittest.mock import patch

from odoo.exceptions import MissingError
from odoo.addons.somconnexio.tests.sc_test_case import SCTestCase


@patch(
    "odoo.addons.somconnexio.services.fiber_contract_to_pack.FiberContractToPackService.create"  # noqa
)
class TestCreateLeadfromPartnerWizard(SCTestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.partner = self.browse_ref("somconnexio.res_partner_2_demo")
        self.wizard_params = {
            "source": "others",
            "bank_id": self.partner.bank_ids.id,
            "email_id": self.partner.id,
            "phone_contact": "888888888",
            "product_id": self.ref("somconnexio.Fibra600Mb"),
            "product_categ_id": self.ref("somconnexio.broadband_fiber_service"),
            "type": "new",
            "service_street": "Principal A",
            "service_zip_code": "00123",
            "service_city": "Barcelona",
            "service_state_id": self.ref("base.state_es_b"),
            "delivery_street": "Principal B",
            "delivery_zip_code": "08027",
            "delivery_city": "Barcelona",
            "delivery_state_id": self.ref("base.state_es_b"),
            "mm_fiber_coverage": "fibraFTTH",
            "vdf_fiber_coverage": "fibraFTTH",
        }

    def test_isp_info_params_broadband(self, mock_get_fiber_contracts):
        mock_get_fiber_contracts.side_effect = MissingError("")

        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])
        crm_lead_line = crm_lead.lead_line_ids[0]

        self.assertEqual(
            crm_lead_line.broadband_isp_info.mm_fiber_coverage, "fibraFTTH"
        )
        self.assertEqual(
            crm_lead_line.broadband_isp_info.vdf_fiber_coverage, "fibraFTTH"
        )
        self.assertFalse(crm_lead_line.mobile_isp_info)

    def test_isp_info_params_not_broadband(self, mock_get_fiber_contracts):
        mock_get_fiber_contracts.side_effect = MissingError("")
        self.wizard_params.update(
            {
                "product_categ_id": self.ref("somconnexio.mobile_service"),
                "product_id": self.ref("somconnexio.SenseMinuts2GB"),
            }
        )
        wizard = (
            self.env["partner.create.lead.wizard"]
            .with_context(active_id=self.partner.id)
            .create(self.wizard_params)
        )

        crm_lead_action = wizard.create_lead()
        crm_lead = self.env["crm.lead"].browse(crm_lead_action["res_id"])
        crm_lead_line = crm_lead.lead_line_ids[0]

        self.assertFalse(crm_lead_line.broadband_isp_info)
        self.assertTrue(crm_lead_line.mobile_isp_info)
