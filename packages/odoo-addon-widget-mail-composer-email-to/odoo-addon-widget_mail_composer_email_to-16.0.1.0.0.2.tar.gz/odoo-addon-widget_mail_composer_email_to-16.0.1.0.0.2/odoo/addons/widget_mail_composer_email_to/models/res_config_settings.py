from odoo import models, fields
from odoo.tools.translate import _


class ResConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    support_contact_tag_id = fields.Many2one(
        string=_("Support Contact Tag"),
        comodel_name="res.partner.category",
        related="company_id.support_contact_tag_id",
        readonly=False,
        help=_("Select the tag to categorize support contacts."),
    )
