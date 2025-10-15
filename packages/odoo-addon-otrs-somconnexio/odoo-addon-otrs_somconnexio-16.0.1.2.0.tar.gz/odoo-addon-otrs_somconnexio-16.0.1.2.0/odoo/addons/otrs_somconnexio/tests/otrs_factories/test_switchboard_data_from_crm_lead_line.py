from odoo.addons.switchboard_somconnexio.tests.helper_service import crm_lead_create
from odoo.addons.somconnexio.tests.sc_test_case import SCTestCase

from ...otrs_factories.switchboard_data_from_crm_lead_line import (
    SwitchboardDataFromCRMLeadLine,
)


class SwitchboardDataFromCRMLeadLineTest(SCTestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.partner_id = self.browse_ref("somconnexio.res_partner_2_demo")
        self.tecnology = self.env.ref(
            "switchboard_somconnexio.service_technology_switchboard"
        )

    def test_build_agent(self):
        sb_crm_lead = crm_lead_create(self.env, self.partner_id, "switchboard")
        crm_lead_line = sb_crm_lead.lead_line_ids[0]
        switchboard_isp_info = crm_lead_line.switchboard_isp_info

        switchboard_data = SwitchboardDataFromCRMLeadLine(crm_lead_line).build()

        self.assertEqual(
            switchboard_data.technology,
            self.tecnology.name,
        )
        self.assertEqual(
            switchboard_data.type,
            switchboard_isp_info.type,
        )
        self.assertEqual(
            switchboard_data.icc,
            switchboard_isp_info.icc,
        )
        self.assertEqual(
            switchboard_data.has_sim,
            switchboard_isp_info.has_sim,
        )
        self.assertEqual(
            switchboard_data.extension,
            switchboard_isp_info.extension,
        )
        self.assertFalse(
            switchboard_data.landline,
        )
        self.assertEqual(
            switchboard_data.agent_name,
            switchboard_isp_info.agent_name,
        )
        self.assertEqual(
            switchboard_data.agent_email,
            switchboard_isp_info.agent_email,
        )
        self.assertEqual(
            switchboard_data.shipment_address,
            switchboard_isp_info.delivery_full_street,
        )
        self.assertEqual(
            switchboard_data.shipment_city,
            switchboard_isp_info.delivery_city,
        )
        self.assertEqual(
            switchboard_data.shipment_zip,
            switchboard_isp_info.delivery_zip_code,
        )
        self.assertEqual(
            switchboard_data.shipment_subdivision,
            switchboard_isp_info.delivery_state_id.name,
        )
        self.assertFalse(switchboard_data.additional_products)
        self.assertFalse(switchboard_data.mobile_phone_number)
        self.assertFalse(switchboard_data.confirmed_documentation)

    def test_build_landline_portability(self):
        sb_crm_lead = crm_lead_create(
            self.env, self.partner_id, "switchboard", portability=True
        )
        crm_lead_line = sb_crm_lead.lead_line_ids[0]
        switchboard_isp_info = crm_lead_line.switchboard_isp_info
        switchboard_isp_info.phone_number = "972972972"

        switchboard_data = SwitchboardDataFromCRMLeadLine(crm_lead_line).build()

        self.assertEqual(
            switchboard_data.landline,
            switchboard_isp_info.phone_number,
        )
        self.assertEqual(
            switchboard_data.type,
            "portability",
        )
        self.assertEqual(
            switchboard_data.previous_owner_vat,
            switchboard_isp_info.previous_owner_vat_number,
        )
        self.assertEqual(
            switchboard_data.previous_owner_name,
            switchboard_isp_info.previous_owner_first_name,
        )
        self.assertEqual(
            switchboard_data.previous_owner_surname,
            switchboard_isp_info.previous_owner_name,
        )

    def test_build_agent_with_mobile(self):
        sb_crm_lead = crm_lead_create(
            self.env, self.partner_id, "switchboard", portability=True
        )
        crm_lead_line = sb_crm_lead.lead_line_ids[0]
        switchboard_isp_info = crm_lead_line.switchboard_isp_info

        mobile_sb_product = self.env.ref(
            "switchboard_somconnexio.CentraletaVirtualSIMUNL10GB"
        )
        phone_number = "123456789"
        switchboard_isp_info.mobile_phone_number = phone_number
        switchboard_isp_info.additional_product_ids = [(4, mobile_sb_product.id)]

        switchboard_data = SwitchboardDataFromCRMLeadLine(crm_lead_line).build()

        self.assertFalse(
            switchboard_data.landline,
        )
        self.assertEqual(
            switchboard_data.mobile_phone_number,
            switchboard_isp_info.mobile_phone_number,
        )
        self.assertEqual(
            switchboard_data.type,
            "portability",
        )
        self.assertEqual(
            switchboard_data.additional_products,
            ",".join(
                product.default_code
                for product in switchboard_isp_info.additional_product_ids
            ),
        )
