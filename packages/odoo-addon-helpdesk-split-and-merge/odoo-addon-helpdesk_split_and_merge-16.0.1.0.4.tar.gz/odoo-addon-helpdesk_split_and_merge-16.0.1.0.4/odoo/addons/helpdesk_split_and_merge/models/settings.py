from odoo import models, fields
from odoo.tools.translate import _


class Company(models.Model):
    _inherit = "res.company"

    merge_ticket_stage = fields.Many2one(
        "helpdesk.ticket.stage",
        string=_("Stage for Closed Tickets"),
        help="Select the stage to which tickets will be moved when they are closed by a merge.",  # noqa: E501
    )
    merge_email_template = fields.Many2one(
        "mail.template",
        string="Email Template for Merge",
        help="Select the email template to use when notifying customers about a merged ticket.",  # noqa: E501
    )


class Settings(models.TransientModel):
    _inherit = "res.config.settings"

    merge_ticket_stage = fields.Many2one(
        "helpdesk.ticket.stage",
        related="company_id.merge_ticket_stage",
        string=_("Stage for Closed Tickets"),
        readonly=False,
    )
    merge_email_template = fields.Many2one(
        related="company_id.merge_email_template",
        string=_("Email Template for Merge"),
        readonly=False,
    )
