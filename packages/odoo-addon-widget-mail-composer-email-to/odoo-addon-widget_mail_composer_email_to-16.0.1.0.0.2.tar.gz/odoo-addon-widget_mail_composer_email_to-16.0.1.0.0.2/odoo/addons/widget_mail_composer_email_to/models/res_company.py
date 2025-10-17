from odoo import fields, models
from odoo.tools.translate import _


class ResCompany(models.Model):
    _inherit = "res.company"

    support_contact_tag_id = fields.Many2one(
        comodel_name="res.partner.category",
        string=_("Support Contact Tag"),
        help=_("Select the tag to categorize support contacts."),
    )
