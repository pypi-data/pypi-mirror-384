from odoo import models, fields
from otrs_somconnexio.otrs_models.coverage.mm_fiber import MMFiberCoverage
from otrs_somconnexio.otrs_models.coverage.vdf_fiber import VdfFiberCoverage


class CreateLeadFromPartnerWizard(models.TransientModel):
    _inherit = "partner.create.lead.wizard"

    fiber_supplier = fields.Selection(
        [("MM", "masmovil"), ("VDF", "vodafone")], default="MM"
    )
    mm_fiber_coverage = fields.Selection(
        MMFiberCoverage.VALUES,
        "MM Fiber Coverage",
    )
    vdf_fiber_coverage = fields.Selection(
        VdfFiberCoverage.VALUES,
        "Vdf Fiber Coverage",
    )

    def _create_isp_info_params(self):
        isp_info_model_name, isp_info_res_id = super()._create_isp_info_params()
        if isp_info_model_name == "broadband.isp.info":
            isp_info_res_id.write(
                {
                    "mm_fiber_coverage": self.mm_fiber_coverage,
                    "vdf_fiber_coverage": self.vdf_fiber_coverage,
                }
            )
        return isp_info_model_name, isp_info_res_id
