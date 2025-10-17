# Copyright 2023-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class WizardSplit(models.TransientModel):
    _name = "helpdesk_split_and_merge.wizard_split"
    _description = "Split Helpdesk Tickets Wizard"

    ticket_id = fields.Many2one(
        "helpdesk.ticket", default=lambda self: self.env.context.get("active_id")
    )
    split_ticket_ids = fields.One2many(
        related="ticket_id.split_ticket_ids", readonly=False
    )
