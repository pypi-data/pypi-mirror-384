# Copyright 2023-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, _
from odoo.exceptions import UserError
from markupsafe import Markup


class WizardMerge(models.TransientModel):
    _name = "helpdesk_split_and_merge.wizard_merge"
    _description = "Merge Helpdesk Tickets Wizard"

    ticket_id = fields.Many2one(
        "helpdesk.ticket",
        default=lambda self: self.env.context.get("active_id"),
        required=True,
    )
    merge_ticket_id = fields.Many2one("helpdesk.ticket", required=False)
    message = fields.Char(
        string="",
        default="This Ticket has been merged into ##",
        help="Leave the code ## where you want the ticket link to be",
    )
    message_main_ticket = fields.Char(
        string="",
        default="The Ticket ## was closed and has been merged into this Ticket",
        help="Leave the code ## where you want the ticket link to be",
    )

    def _validate_action_merge_ticket(self):
        """
        Validate the action of merging tickets.
        This method checks if the merge_ticket_id is set and if it is different
        from the ticket_id. It also checks if both tickets belong to the same
        partner and if the a merge stage is set in the company settings.
        Raises:
            UserError: If the merge_ticket_id is not set, if it is the same as
            ticket_id, or if they belong to different partners.
            UserError: If no merge stage is set in the company settings.
        Returns:
            recordset: The merge stage recordset.
        """
        if not (self.ticket_id and self.merge_ticket_id):
            raise UserError(_("A Ticket to merge into has to be set."))

        if self.ticket_id.id == self.merge_ticket_id.id:
            raise UserError(_("You can not merge a ticket with itself."))

        if self.ticket_id.partner_id != self.merge_ticket_id.partner_id:
            raise UserError(_("Tickets to merge must belong to the same Partner."))

        merge_stage = (
            self.env.company.merge_ticket_stage
            or self.env.user.company_id.merge_ticket_stage
        )
        if not merge_stage:
            raise UserError(_("No stage found in settings for closing tickets."))

        return merge_stage

    def action_merge_ticket(self):
        merge_stage = self._validate_action_merge_ticket()

        self.ticket_id.write(
            {
                "merge_ticket_id": self.merge_ticket_id.id,
                "stage_id": merge_stage.id,
            }
        )

        if self.message:
            message = Markup(
                self.message.replace(
                    "##", self.merge_ticket_id._get_html_link(self.merge_ticket_id.name)
                )
            )
            self.ticket_id.message_post(body=message)
        if self.message_main_ticket:
            message = Markup(
                self.message_main_ticket.replace(
                    "##", self.ticket_id._get_html_link(self.ticket_id.name)
                )
            )
            self.merge_ticket_id.message_post(body=message)

        if self.env.user.company_id.merge_email_template:
            template = self.env.user.company_id.merge_email_template
            template.send_mail(self.ticket_id.id, force_send=True)

        return True
