from otrs_somconnexio.services.set_SIM_recieved_mobile_ticket import (
    SetSIMRecievedMobileTicket,
)
from otrs_somconnexio.services.set_SIM_returned_mobile_ticket import (
    SetSIMReturnedMobileTicket,
)
from otrs_somconnexio.exceptions import TicketNotReadyToBeUpdatedWithSIMReceivedData

from ..services.mobile_activation_date_service import (
    MobileActivationDateService,
)
from odoo.addons.component.core import Component

# 5 mins in seconds to delay the jobs
ETA = 300


class CrmLeadListener(Component):
    _inherit = "crm.lead.listener"

    def on_record_write(self, record, fields=None):
        super().on_record_write(record, fields=fields)
        won_stage = self.env.ref("crm.stage_lead4")

        if "stage_id" in fields and record.stage_id == won_stage:
            self.create_OTRS_ticket_if_lead_just_won(record)
        if "sim_delivery_in_course" in fields and not record.sim_delivery_in_course:
            self.update_OTRS_tickets_if_sim_delivery_not_in_course(record)

    def create_OTRS_ticket_if_lead_just_won(self, record):
        """
        Create OTRS tickets for lead lines if the lead is just won/validated.
        If the lead has both mobile and broadband lead lines, or mobile lead
        lines with sharing data bond, the corresponding tickets are linked as a pack.
        If the lead has switchboard lead lines, a header ticket is created instead.
        :param record: The CRM lead record that has been updated.
        """
        for line in record.lead_line_ids:
            if line.external_provisioning_required:
                line.with_delay().create_ticket()
        if record.has_mobile_lead_lines and record.has_broadband_lead_lines:
            record.with_delay(eta=ETA).link_pack_tickets()
        if record.mobile_lead_line_ids.filtered(
            lambda l: (l.product_id.has_sharing_data_bond)
        ):
            record.with_delay(eta=ETA + 100).link_mobile_tickets_in_pack()
        if record.has_switchboard_lead_lines:
            record.with_delay().create_header_ticket()
            record.with_delay(eta=ETA + 100).link_tickets_to_header()

    def update_OTRS_tickets_if_sim_delivery_not_in_course(self, record):
        """
        Set SIM received or returned to OTRS tickets when SIM delivery
        status changed to False (finished or null).
        If the SIM delivery completes successfully, mobile OTRS tickets
        are updated with the activation and introduced dates.
        :param record: The CRM lead record that has been updated.
        """

        if not record.correos_tracking_code:
            for line in record.lead_line_ids:
                if not line.is_mobile or line.mobile_isp_info_has_sim:
                    continue
                SetSIMReturnedMobileTicket(line.ticket_number).run()
        else:
            for line in record.lead_line_ids:
                if not line.is_mobile or line.mobile_isp_info_has_sim:
                    continue
                date_service = MobileActivationDateService(
                    self.env,
                    line.is_portability(),
                )
                try:
                    SetSIMRecievedMobileTicket(
                        line.ticket_number,
                        date_service.get_activation_date(),
                        date_service.get_introduced_date(),
                    ).run()
                except TicketNotReadyToBeUpdatedWithSIMReceivedData:
                    pass
