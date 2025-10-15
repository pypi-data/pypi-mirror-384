from odoo import models, fields


class ServiceTechnology(models.Model):
    _name = "service.technology"
    name = fields.Char("Name")
    service_product_category_id = fields.Many2one(
        "product.category",
        help="Products category that provide service with recurring billing for a given technology.",  # noqa
    )
