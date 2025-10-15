from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = "product.category"

    name = fields.Char("Name", index="trigram", required=True, translate=True)

    def name_get(self):
        result = []
        for category in self:
            if self.env.context.get("show_short_name") and category.name:
                display_name = category.name
            else:
                display_name = category.complete_name
            result.append((category.id, display_name))
        return result
