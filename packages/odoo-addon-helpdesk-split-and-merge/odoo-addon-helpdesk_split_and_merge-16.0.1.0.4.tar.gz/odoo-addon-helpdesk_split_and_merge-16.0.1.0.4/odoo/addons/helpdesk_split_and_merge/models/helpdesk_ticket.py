from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.id and record.split_ticket_id:
                main_ticket = record.split_ticket_id
                if main_ticket:
                    message = _(
                        "This Ticket is a split from the main Ticket: %s",
                        main_ticket._get_html_link(main_ticket.name),
                    )
                    message_main_ticket = _(
                        "This Ticket has been splitted to this Sub-Ticket: %s",
                        record._get_html_link(record.name),
                    )
                    record.message_post(body=message)
                    main_ticket.message_post(body=message_main_ticket)

        return records

    split_ticket_id = fields.Many2one("helpdesk.ticket", string="Original Split Ticket")
    split_ticket_ids = fields.One2many(
        "helpdesk.ticket", "split_ticket_id", string="Sub-Tickets"
    )
    split_ticket_ids_count = fields.Integer(
        "Split", compute="_compute_split_ticket_ids_count", store=False
    )
    merge_ticket_id = fields.Many2one("helpdesk.ticket", string="Merge Ticket")
    merge_tickets_ids = fields.One2many(
        "helpdesk.ticket", "merge_ticket_id", string="Original Merged Tickets"
    )
    merge_ticket_ids_count = fields.Integer(
        "Merged", compute="_compute_merged_ticket_ids_count", store=False
    )

    @api.constrains("merge_ticket_id")
    def _check_merge_ticket_id(self):
        for ticket in self:
            if ticket.merge_ticket_id == ticket:
                raise ValidationError(_("A ticket cannot be merged with itself."))

    @api.depends("split_ticket_ids")
    def _compute_split_ticket_ids_count(self):
        for ticket in self:
            ticket.split_ticket_ids_count = len(ticket.split_ticket_ids)

    @api.depends("merge_tickets_ids")
    def _compute_merged_ticket_ids_count(self):
        for ticket in self:
            ticket.merge_ticket_ids_count = len(ticket.merge_tickets_ids)

    def split_ticket(self):
        """
        Split a ticket into multiple sub-tickets.
        """

        if len(self) > 1:
            raise UserError(_("You are only able to split ONE ticket at a time."))
        if self.split_ticket_id:
            raise UserError(_("This ticket can not be splitted if it is a sub-ticket."))

        return {
            "name": _("Split"),
            "view_mode": "form",
            "view_type": "form",
            "res_model": self._name,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {"default_split_ticket_id": self.id},
        }

    def merge_ticket(self):
        """Merge tickets into one main ticket."""

        if len(self) > 1:
            raise UserError(_("You are only able to merge ONE ticket at a time."))
        if self.merge_ticket_id or self.stage_id.closed:
            raise UserError(_("This ticket can not be remerged."))

        wizard_model = "helpdesk_split_and_merge.wizard_merge"
        wizard = self.env[wizard_model].create({"ticket_id": self.id})

        # we set the context so that the tickets can
        # be selected based on the same partner
        ctx = dict(self._context, partner_id=self.partner_id.id)

        return {
            "name": _("Merge"),
            "view_mode": "form",
            "res_model": wizard_model,
            "res_id": wizard.id,
            "context": ctx,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        # Getting the current active_id record from the context
        split_active_id = self._context.get("default_split_ticket_id")
        if split_active_id:
            active_record = self.env[self._name].browse(split_active_id)

            # Then we copy the active_record fields except the ones that will
            # need to restored like the status
            stage_id = self.env["helpdesk.ticket.stage"].search(
                [], order="sequence asc", limit=1
            )  # First initial stage to be assigned
            non_copiable = {
                "stage_id": stage_id.id,
            }
            non_copiable_use_default = [
                "split_active_id",
                "number",
            ]
            to_copy = active_record.copy_data(default=non_copiable)

            # filtering only the fields that has been asked
            asked_to_copy = {}
            if to_copy and len(to_copy) > 0 and to_copy[0]:
                asked_to_copy = dict(
                    filter(
                        lambda x: x[0] in fields_list
                        and x[0] not in non_copiable_use_default,
                        to_copy[0].items(),
                    )
                )

            # We need to explicitly set split_ticket_id from the father
            asked_to_copy.update(
                {
                    "split_ticket_id": split_active_id,
                }
            )

            defaults.update(asked_to_copy)

        return defaults

    @api.onchange("split_ticket_id", "user_id", "team_id")
    def _onchange_split_ticket_id(self):
        """
        This method aims to copy the data of user_id and team_id of the main ticket when splitting      # noqa: E501
        since those fields become impossible to set initially due to their respective onchange.         # noqa: E501
        """
        for ticket in self:
            if not ticket.user_id and not ticket.team_id:
                ticket.user_id = ticket.split_ticket_id.user_id
                ticket.team_id = ticket.split_ticket_id.team_id

    def get_view_helpdesk_main_ticket(self):
        context = self._context.copy()
        return {
            "name": self.name,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "helpdesk.ticket",
            "res_id": context.get("ticket_id"),
            "type": "ir.actions.act_window",
            "context": context,
        }
