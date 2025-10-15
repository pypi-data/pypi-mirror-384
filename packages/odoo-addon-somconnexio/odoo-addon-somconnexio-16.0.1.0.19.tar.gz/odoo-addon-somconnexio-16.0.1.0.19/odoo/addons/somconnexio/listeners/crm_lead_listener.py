from odoo.addons.component.core import Component


class CrmLeadListener(Component):
    _name = "crm.lead.listener"
    _description = "Basic SC CRM Lead Listener"
    _inherit = "base.event.listener"
    _apply_on = ["crm.lead"]
