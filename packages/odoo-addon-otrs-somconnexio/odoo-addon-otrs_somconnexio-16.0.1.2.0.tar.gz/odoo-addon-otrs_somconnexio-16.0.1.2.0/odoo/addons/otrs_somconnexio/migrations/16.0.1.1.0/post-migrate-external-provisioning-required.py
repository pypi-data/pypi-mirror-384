# Copyright 2025 Coopdevs Treball SCCL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
import logging

_logger = logging.getLogger(__name__)

product_template_xml_id_list = [
    ("somconnexio", "Mobile_product_template"),
    ("somconnexio", "Fiber_product_template"),
    ("somconnexio", "ADSL_product_template"),
    ("somconnexio", "Router4G_product_template"),
    ("switchboard_somconnexio", "Switchboard_product_template"),
    ("switchboard_somconnexio", "Switchboard_mobile_product_template"),
]


@openupgrade.migrate()
def migrate(env, version):
    """
    Set external_provisioning_required to True for some product templates
    that need external provisioning.
    This migration is necessary due to the no-update parameter in the product
    template data xml files.
    """
    for module, xml_id in product_template_xml_id_list:
        product_template = env.ref(f"{module}.{xml_id}", raise_if_not_found=False)
        if product_template:
            _logger.info(
                "Setting external_provisioning_required to True for %s", xml_id
            )
            product_template.write({"external_provisioning_required": True})
        else:
            _logger.warning(
                "Product template with XML ID %s not found, skipping update.", xml_id
            )
