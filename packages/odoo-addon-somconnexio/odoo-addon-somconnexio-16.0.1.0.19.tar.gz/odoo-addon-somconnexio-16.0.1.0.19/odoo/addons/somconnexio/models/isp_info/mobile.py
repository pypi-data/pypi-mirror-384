from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MobileISPInfo(models.Model):
    _inherit = "base.isp.info"

    _name = "mobile.isp.info"
    _description = "Mobile ISP Info"
    icc = fields.Char(string="ICC")
    has_sim = fields.Boolean(string="Has sim card", default=False)
    icc_donor = fields.Char(string="ICC Donor")
    previous_contract_type = fields.Selection(
        [("contract", "Contract"), ("prepaid", "Prepaid")],
        string="Previous Contract Type",
    )
    delivery_street = fields.Char(string="Delivery Street")
    delivery_zip_code = fields.Char(string="Delivery ZIP")
    delivery_city = fields.Char(string="Delivery City")
    delivery_state_id = fields.Many2one("res.country.state", string="Delivery State")
    linked_fiber_contract_id = fields.Many2one(
        "contract.contract", string="Fiber linked to mobile offer"
    )
    shared_bond_id = fields.Char(string="Shared bond ID")

    @api.constrains(
        "type",
        "icc_donor",
        "previous_contract_type",
        "previous_provider",
        "phone_number",
    )
    def _check_mobile_portability_info(self):
        if not self.type == "portability":
            return True
        if not self.phone_number:
            raise ValidationError(_("Phone number is required in a portability"))
        if not self.previous_contract_type:
            raise ValidationError(
                _("Previous contract type is required in a portability")
            )
        if not self.icc_donor and self.previous_contract_type == "prepaid":
            raise ValidationError(_("ICC donor is required in a portability"))
        if not self.previous_provider.mobile:
            raise ValidationError(
                _("This previous provider does not offer mobile services")
            )
