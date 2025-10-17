from odoo.tests import common, Form, tagged
from odoo.exceptions import ValidationError


@tagged("post_install", "-at_install", "helpdesk_split_and_merge")
class TestHelpdeskMerge(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.stage_id = self.env.user.company_id.merge_ticket_stage = self.env[
            "helpdesk.ticket.stage"
        ].create(  # noqa: E501
            {"name": "Close Stage", "closed": True}
        )
        self.ticket1 = self.env["helpdesk.ticket"].create(
            {"name": "Test Ticket 1", "description": "This is a test ticket."}
        )
        self.ticket2 = self.env["helpdesk.ticket"].create(
            {"name": "Test Ticket 2", "description": "This is another test ticket."}
        )

    def test_merge_ticket(self):
        """Test if two tickets can be merged into one main ticket and if the main ticket has a reference to the merged tickets."""  # noqa: E501
        with Form(self.ticket1) as form:
            form.name = "Main Ticket"
        self.ticket2.write({"merge_ticket_id": self.ticket1.id})

        self.assertEqual(
            self.ticket1.merge_tickets_ids,
            self.ticket2,
            "The main ticket should have a reference to the merged tickets.",
        )

    def test_merge_wizard(self):
        """Test if the merge wizard is working properly by merging two tickets into one."""  # noqa: E501
        with Form(self.ticket1) as form:
            form.name = "Main Ticket"

        merge_wiz = (
            self.env["helpdesk_split_and_merge.wizard_merge"]
            .with_context(active_id=self.ticket1.id)
            .create(
                {  # noqa: E501
                    "merge_ticket_id": self.ticket2.id  # provide a value for merge_ticket_id
                }
            )
        )
        with Form(merge_wiz) as form:
            form.merge_ticket_id = self.ticket2  # assign the record, not the id

        merge_wiz.action_merge_ticket()

        self.assertEqual(
            len(self.ticket2.merge_tickets_ids),
            1,
            "The main ticket should have one merged ticket.",
        )

    def test_merge_same_ticket(self):
        """Test if the user cannot merge a ticket with itself."""
        with self.assertRaises(ValidationError):  # expect a ValidationError
            self.ticket1.write({"merge_ticket_id": self.ticket1.id})

    def test_merged_tickets_counter(self):
        """Test if the counter of merged tickets is displayed and works correctly."""
        with Form(self.ticket1) as form:
            form.name = "Main Ticket"

        self.ticket2.write({"merge_ticket_id": self.ticket1.id})

        main_form = Form(self.ticket1)
        self.assertEqual(
            main_form.merge_ticket_ids_count,
            1,
            "The counter of merged tickets should be 1.",
        )
