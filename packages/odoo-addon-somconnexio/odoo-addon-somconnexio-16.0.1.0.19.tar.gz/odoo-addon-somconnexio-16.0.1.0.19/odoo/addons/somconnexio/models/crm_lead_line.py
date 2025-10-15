from odoo import models, fields, api, _
from odoo.tools import html2plaintext
from odoo.exceptions import ValidationError


class CRMLeadLine(models.Model):
    _inherit = "crm.lead.line"

    iban = fields.Char(string="IBAN")

    broadband_isp_info = fields.Many2one(
        "broadband.isp.info", string="Broadband ISP Info"
    )
    mobile_isp_info = fields.Many2one("mobile.isp.info", string="Mobile ISP Info")

    is_mobile = fields.Boolean(compute="_compute_is_mobile", store=True)
    is_adsl = fields.Boolean(
        compute="_compute_is_adsl",
    )
    is_fiber = fields.Boolean(
        compute="_compute_is_fiber",
    )
    is_4G = fields.Boolean(
        compute="_compute_is_4G",
    )

    create_date = fields.Datetime("Creation Date")
    mobile_isp_info_type = fields.Selection(related="mobile_isp_info.type")
    mobile_isp_info_icc = fields.Char(related="mobile_isp_info.icc", store=True)
    mobile_isp_info_has_sim = fields.Boolean(
        related="mobile_isp_info.has_sim", store=False, readonly=False
    )
    mobile_isp_info_phone_number = fields.Char(related="mobile_isp_info.phone_number")
    mobile_isp_info_invoice_street = fields.Char(
        related="mobile_isp_info.invoice_street"
    )
    mobile_isp_info_invoice_street2 = fields.Char(
        related="mobile_isp_info.invoice_street2"
    )
    mobile_isp_info_invoice_zip_code = fields.Char(
        related="mobile_isp_info.invoice_zip_code"
    )
    mobile_isp_info_invoice_city = fields.Char(related="mobile_isp_info.invoice_city")
    mobile_isp_info_invoice_state_id = fields.Many2one(
        related="mobile_isp_info.invoice_state_id"
    )
    mobile_isp_info_delivery_street = fields.Char(
        related="mobile_isp_info.delivery_street"
    )
    mobile_isp_info_delivery_street2 = fields.Char(
        related="mobile_isp_info.delivery_street2"
    )
    mobile_isp_info_delivery_zip_code = fields.Char(
        related="mobile_isp_info.delivery_zip_code"
    )
    mobile_isp_info_delivery_city = fields.Char(related="mobile_isp_info.delivery_city")
    mobile_isp_info_delivery_state_id = fields.Many2one(
        related="mobile_isp_info.delivery_state_id"
    )
    partner_id = fields.Many2one(related="lead_id.partner_id")
    broadband_isp_info_type = fields.Selection(related="broadband_isp_info.type")
    broadband_isp_info_phone_number = fields.Char(
        related="broadband_isp_info.phone_number"
    )
    broadband_isp_info_service_street = fields.Char(
        related="broadband_isp_info.service_street"
    )
    broadband_isp_info_service_street2 = fields.Char(
        related="broadband_isp_info.service_street2"
    )
    broadband_isp_info_service_zip_code = fields.Char(
        related="broadband_isp_info.service_zip_code"
    )
    broadband_isp_info_service_city = fields.Char(
        related="broadband_isp_info.service_city"
    )
    broadband_isp_info_service_state_id = fields.Many2one(
        "res.country.state", related="broadband_isp_info.service_state_id"
    )
    broadband_isp_info_delivery_street = fields.Char(
        related="broadband_isp_info.delivery_street"
    )
    broadband_isp_info_delivery_street2 = fields.Char(
        related="broadband_isp_info.delivery_street2"
    )
    broadband_isp_info_delivery_city = fields.Char(
        related="broadband_isp_info.delivery_city"
    )
    broadband_isp_info_delivery_state_id = fields.Many2one(
        "res.country.state", related="broadband_isp_info.delivery_state_id"
    )
    broadband_isp_info_invoice_street = fields.Char(
        related="broadband_isp_info.invoice_street"
    )
    broadband_isp_info_invoice_street2 = fields.Char(
        related="broadband_isp_info.invoice_street2"
    )
    broadband_isp_info_invoice_city = fields.Char(
        related="broadband_isp_info.invoice_city"
    )
    broadband_isp_info_invoice_state_id = fields.Many2one(
        "res.country.state", related="broadband_isp_info.invoice_state_id"
    )
    broadband_isp_info_no_previous_phone_number = fields.Boolean(
        related="broadband_isp_info.no_previous_phone_number"
    )
    stage_id = fields.Many2one("crm.stage", string="Stage", related="lead_id.stage_id")
    notes = fields.Html(
        string="Notes",
        readonly=False,
    )
    tree_view_notes = fields.Text(
        compute="_compute_notes",
    )
    create_user_id = fields.Many2one(
        "res.users", string="Creator", default=lambda self: self.env.user, index=True
    )

    check_phone_number = fields.Boolean()

    partner_category_id = fields.Many2many(
        "res.partner.category",
        string="Tags",
        related="lead_id.partner_id.category_id",
    )
    create_reason = fields.Selection(
        [
            ("portability", _("Portability")),
            ("new", _("New")),
            ("location_change", _("Location Change")),
            ("holder_change", _("Holder Change")),
        ],
        string="CRM Create Reason",
        compute="_compute_crm_creation_reason",
        store=True,
    )
    is_from_pack = fields.Boolean(compute="_compute_is_from_pack", store=True)

    active = fields.Boolean("Active", default=True, track_visibility=True)
    confirmed_documentation = fields.Boolean(
        related="lead_id.confirmed_documentation",
        help="Provision ticket generated with correct documentation check",
    )

    external_provisioning_required = fields.Boolean(
        string="Requires External Provisioning",
        compute="_compute_external_provisioning_required",
    )

    @api.depends("product_id")
    def _compute_is_from_pack(self):
        pack_attr = self.env.ref("somconnexio.IsInPack")
        for record in self:
            record.is_from_pack = (
                pack_attr
                in record.product_id.product_template_attribute_value_ids.mapped(
                    "product_attribute_value_id"
                )
            )

    @api.depends("product_id")
    def _compute_is_mobile(self):
        mobile = self.env.ref("somconnexio.mobile_service")
        for record in self:
            record.is_mobile = (
                mobile.id == record.product_id.product_tmpl_id.categ_id.id
            )

    @api.depends("product_id")
    def _compute_is_adsl(self):
        adsl = self.env.ref("somconnexio.broadband_adsl_service")
        for record in self:
            record.is_adsl = adsl.id == record.product_id.product_tmpl_id.categ_id.id

    @api.depends("product_id")
    def _compute_is_fiber(self):
        fiber = self.env.ref("somconnexio.broadband_fiber_service")
        for record in self:
            record.is_fiber = fiber.id == record.product_id.product_tmpl_id.categ_id.id

    @api.depends("product_id")
    def _compute_is_4G(self):
        service_4G = self.env.ref("somconnexio.broadband_4G_service")
        for record in self:
            record.is_4G = (
                service_4G.id == record.product_id.product_tmpl_id.categ_id.id
            )

    @api.onchange("mobile_isp_info_icc")
    def _onchange_icc(self):
        icc_change = {"icc": self.mobile_isp_info_icc}
        if isinstance(self.id, models.NewId):
            self._origin.mobile_isp_info.write(icc_change)
        else:
            self.mobile_isp_info.write(icc_change)

    @api.onchange("check_phone_number")
    def _onchange_check_phone_number(self):
        self.lead_id.write(
            {"skip_duplicated_phone_validation": self.check_phone_number}
        )

    @api.depends("notes")
    def _compute_notes(self):
        for record in self:
            if record.notes and len(record.notes) > 50:
                record.tree_view_notes = html2plaintext(record.notes[0:50]) + "..."
            else:
                record.tree_view_notes = html2plaintext(record.notes)

    @api.depends("broadband_isp_info_type", "mobile_isp_info_type")
    def _compute_crm_creation_reason(self):
        for line in self:
            line.create_reason = (
                line.mobile_isp_info_type or line.broadband_isp_info_type
            )

    @api.constrains("is_mobile", "broadband_isp_info", "mobile_isp_info")
    def _check_isp_info(self):
        for record in self:
            if record.is_mobile:
                if not record.mobile_isp_info:
                    raise ValidationError(
                        _(
                            "A mobile lead line needs a Mobile ISP Info "
                            + "instance related."
                        )
                    )
            elif record.is_fiber or record.is_adsl or record.is_4G:
                if not record.broadband_isp_info:
                    raise ValidationError(
                        _(
                            "A broadband lead line needs a Broadband "
                            + "ISP Info instance related."
                        )
                    )

    def action_restore(self):
        for lead_line in self:
            lead_line.lead_id.message_post(
                _("CRM Lead Line restored with id {}.".format(lead_line.id))
            )
            lead_line.active = True

    def action_archive(self):
        for lead_line in self:
            lead_line.lead_id.message_post(
                _(
                    "CRM Lead Line archived with id {}.\n".format(lead_line.id)
                    + "If you need to restore it, talk with IT department"
                )
            )
            lead_line.active = False

    def _get_formview_id(self):
        if self.env.context.get("is_mobile"):
            view_id = self.env.ref("somconnexio.view_form_lead_line_mobile").id
        else:
            view_id = self.env.ref("somconnexio.view_form_lead_line_broadband").id

        return view_id

    def get_formview_action(self):
        view_id = self._get_formview_id()

        return {
            "type": "ir.actions.act_window",
            "name": "Model Title",
            "views": [[view_id, "form"]],
            "res_model": self._name,
            "res_id": self.env.context.get("crm_lead_id"),
            "target": "current",
        }

    def is_portability(self):
        if self.create_reason == "portability":
            return True
        return False

    def _compute_external_provisioning_required(self):
        """
        Compute if the lead line requires external provisioning based
        on the product template.
        :return: Boolean
        """
        for line in self:
            line.external_provisioning_required = (
                line.product_id.product_tmpl_id.external_provisioning_required
            )

    def _prepare_contract_vals_from_line(self, supplier_id, date_start=False):
        """
        Prepare the values for creating a contract.
        from the lead line information.
        :param supplier_id: The service supplier ID.
        :return: Dictionary of values for the contract creation.
        """
        if not date_start:
            date_start = fields.Date.today()
        partner = self.lead_id.partner_id
        mandate = partner.get_mandate(self.iban.replace(" ", "").upper())
        partner_email = partner.get_or_create_contract_email(self.lead_id.email_from)
        service_technology_id = self.product_id.get_technology()
        contract_line = {
            "name": self.product_id.name,
            "product_id": self.product_id.id,
            "date_start": date_start,
        }

        return {
            "name": "Contract from lead line {}".format(self.id),
            "partner_id": self.lead_id.partner_id.id,
            "mandate_id": mandate.id,
            "email_ids": [(4, partner_email.id, False)],
            "service_technology_id": service_technology_id.id,
            "service_supplier_id": supplier_id.id,
            "payment_mode_id": self.env.ref("somconnexio.payment_mode_inbound_sepa").id,
            "crm_lead_line_id": self.id,
            "contract_line_ids": [(0, False, contract_line)],
        }
