# Copyright 2023-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import exceptions
from odoo.tests import common, Form, tagged


@tagged("post_install", "-at_install", "helpdesk_split_and_merge")
class TestHelpdeskSplitAndMerge(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.ticket = self.env["helpdesk.ticket"].create(
            {"name": "Test Ticket", "description": "This is a test ticket."}
        )

    def test_split_ticket(self):
        """Test if a ticket can be splitted into multiple sub-tickets and if the original ticket has a reference to them."""  # noqa: E501
        with Form(self.ticket) as form:
            form.name = "Main Ticket"
        split1 = self.env["helpdesk.ticket"].create(
            {
                "name": "Sub-Ticket 1",
                "description": "This is a sub-ticket.",
                "split_ticket_id": self.ticket.id,
            }
        )
        split2 = self.env["helpdesk.ticket"].create(
            {
                "name": "Sub-Ticket 2",
                "description": "This is another sub-ticket.",
                "split_ticket_id": self.ticket.id,
            }
        )

        self.assertEqual(
            self.ticket.split_ticket_ids,
            (split1 | split2),
            "The original ticket should have a reference to the splitted tickets.",
        )

    def test_split_wizard(self):
        """Test if the split wizard is working properly by splitting a ticket into two sub-tickets."""  # noqa: E501
        with Form(self.ticket) as form:
            form.name = "Test Ticket"

        split_wiz = (
            self.env["helpdesk_split_and_merge.wizard_split"]
            .with_context(active_id=self.ticket.id)
            .create({})
        )
        with Form(split_wiz) as form:
            with form.split_ticket_ids.new() as split1:
                split1.name = "Sub-Ticket 1"
                split1.description = "This is a sub-ticket."
            with form.split_ticket_ids.new() as split2:
                split2.name = "Sub-Ticket 2"
                split2.description = "This is another sub-ticket."

        self.assertEqual(
            len(self.ticket.split_ticket_ids),
            2,
            "The original ticket should have two splitted tickets.",
        )

    def test_split_sub_ticket(self):
        """Test if the user cannot split a ticket that is already a sub-ticket."""
        main_ticket = self.env["helpdesk.ticket"].create(
            {"name": "Main Ticket", "description": "This is the main ticket."}
        )
        sub_ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Sub-Ticket",
                "description": "This is a sub-ticket.",
                "split_ticket_id": main_ticket.id,
            }
        )

        with self.assertRaises(exceptions.UserError):
            sub_ticket.split_ticket()

    def test_splitted_tickets_counter(self):
        """Test if the counter of splitted tickets is displayed and works correctly."""  # noqa: E501
        with Form(self.ticket) as form:
            form.name = "Main Ticket"

        split1 = self.env["helpdesk.ticket"].create(  # noqa: F841
            {
                "name": "Sub-Ticket 1",
                "description": "This is a sub-ticket.",
                "split_ticket_id": self.ticket.id,
            }
        )
        split2 = self.env["helpdesk.ticket"].create(  # noqa: F841
            {
                "name": "Sub-Ticket 2",
                "description": "This is another sub-ticket.",
                "split_ticket_id": self.ticket.id,
            }
        )

        main_form = Form(self.ticket)
        self.assertEqual(
            main_form.split_ticket_ids_count,
            2,
            "The counter of splitted tickets should be 2.",
        )
