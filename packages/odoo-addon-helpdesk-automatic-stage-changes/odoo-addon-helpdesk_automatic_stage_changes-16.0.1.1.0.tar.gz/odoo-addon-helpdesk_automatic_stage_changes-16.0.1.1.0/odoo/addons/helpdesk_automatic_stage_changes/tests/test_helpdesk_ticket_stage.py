from odoo.tests import common, tagged
from unittest.mock import patch


@tagged("post_install", "-at_install", "helpdesk_automatic_stage_changes")
class TestHelpdeskTicketStage(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.stage0 = self.env["helpdesk.ticket.stage"].create({"name": "Stage 0"})
        self.stage1 = self.env["helpdesk.ticket.stage"].create(
            {"name": "Stage 1", "action_user_odoo": "0"}
        )
        self.stage2 = self.env["helpdesk.ticket.stage"].create(
            {
                "name": "Stage 2",
                "action_user_odoo": "1",
                "change_stage_to_id": self.stage1.id,
            }
        )
        self.stage3 = self.env["helpdesk.ticket.stage"].create(
            {"name": "Stage 3", "when_odoo_responds_change_stage_to_id": self.stage2.id}
        )
        self.ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "This is a test ticket.",
                "partner_email": "test@example.com",
                "partner_name": "Test Partner",
                "stage_id": self.stage0.id,
            }
        )

    def test_write_stage_and_ticket(self):
        """Test stage change color_row and color_background_row"""
        self.ticket.write({"stage_id": self.stage0.id})

        self.stage0.write(
            {
                "color_row": "#111111",
                "color_background_row": "#222222",
            }
        )

        self.assertEqual(
            self.stage0.color_row,
            self.ticket.color_row,
            "The color_row of the stage must be the same as the color_row of the "
            "ticket.",
        )
        self.assertEqual(
            self.stage0.color_background_row,
            self.ticket.color_background_row,
            "The color_background_row of the stage must be the same as the "
            "color_background_row of the ticket.",
        )
        self.assertEqual(
            self.stage0.action_user_odoo,
            self.ticket.action_user_odoo,
            "The action_user_odoo of the stage must be the same as the action_user_odoo"
            " of the ticket.",
        )
        self.assertEqual(
            self.stage0.change_stage_to_id,
            self.ticket.change_stage_to_id,
            "The change_stage_to_id of the stage must be the same as the "
            "change_stage_to_id of the ticket.",
        )
        self.assertEqual(
            self.stage0.when_odoo_responds_change_stage_to_id,
            self.ticket.when_odoo_responds_change_stage_to_id,
            "The when_odoo_responds_change_stage_to_id of the stage must be the same as"
            " the when_odoo_responds_change_stage_to_id of the ticket.",
        )

    def test_stage_not_changed_1(self):
        """Test stage not changed if action_user_odoo is not defined"""
        self.ticket.write({"stage_id": self.stage0.id})

        self.env["mail.message"].create(
            {
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
                "body": "Test Message",
                "email_from": "test@example.com",
            }
        )

        self.assertEqual(
            self.ticket.stage_id.id,
            self.stage0.id,
            "The id of the stage must be the same as the stage_id of the ticket.",
        )
        self.assertEqual(
            self.stage0.color_row,
            self.ticket.color_row,
            "The color_row of the stage must be the same as the color_row of the "
            "ticket.",
        )
        self.assertEqual(
            self.stage0.color_background_row,
            self.ticket.color_background_row,
            "The color_background_row of the stage must be the same as the "
            "color_background_row of the ticket.",
        )
        self.assertEqual(
            self.stage0.action_user_odoo,
            self.ticket.action_user_odoo,
            "The action_user_odoo of the stage must be the same as the action_user_odoo"
            " of the ticket.",
        )
        self.assertEqual(
            self.stage0.change_stage_to_id,
            self.ticket.change_stage_to_id,
            "The change_stage_to_id of the stage must be the same as the "
            "change_stage_to_id of the ticket.",
        )
        self.assertEqual(
            self.stage0.when_odoo_responds_change_stage_to_id,
            self.ticket.when_odoo_responds_change_stage_to_id,
            "The when_odoo_responds_change_stage_to_id of the stage must be the same "
            "as the when_odoo_responds_change_stage_to_id of the ticket.",
        )

    def test_stage_not_changed_2(self):
        """Test stage not changed if when_odoo_responds_change_stage_to_id
        is not defined"""
        self.ticket.write({"stage_id": self.stage0.id})

        wizard = self.env["mail.compose.message"].create(
            {
                "composition_mode": "mass_mail",
                "template_id": self.env.ref(
                    "helpdesk_ticket_mail_message.created_response_ticket_template"
                ).id
                or False,
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
                "when_odoo_responds_change_stage_to_id": self.ticket.when_odoo_responds_change_stage_to_id  # noqa: E501
                and self.ticket.when_odoo_responds_change_stage_to_id.id
                or False,
            }
        )
        wizard.action_send_mail()

        self.assertEqual(
            self.ticket.stage_id.id,
            self.stage0.id,
            "The id of the stage must be the same as the stage_id of the ticket.",
        )
        self.assertEqual(
            self.stage0.color_row,
            self.ticket.color_row,
            "The color_row of the stage must be the same as the color_row of the "
            "ticket.",
        )
        self.assertEqual(
            self.stage0.color_background_row,
            self.ticket.color_background_row,
            "The color_background_row of the stage must be the same as the "
            "color_background_row of the ticket.",
        )
        self.assertEqual(
            self.stage0.action_user_odoo,
            self.ticket.action_user_odoo,
            "The action_user_odoo of the stage must be the same as the action_user_odoo"
            " of the ticket.",
        )
        self.assertEqual(
            self.stage0.change_stage_to_id,
            self.ticket.change_stage_to_id,
            "The change_stage_to_id of the stage must be the same as the "
            "change_stage_to_id of the ticket.",
        )
        self.assertEqual(
            self.stage0.when_odoo_responds_change_stage_to_id,
            self.ticket.when_odoo_responds_change_stage_to_id,
            "The when_odoo_responds_change_stage_to_id of the stage must be the same "
            "as the when_odoo_responds_change_stage_to_id of the ticket.",
        )

    def test_stage_change_on_message_creation_1(self):
        """Test stage not changed if action_user_odoo is defined 0"""
        self.ticket.write({"stage_id": self.stage1.id})

        self.env["mail.message"].create(
            {
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
                "body": "Test Message",
                "email_from": "test@example.com",
            }
        )

        new_ticket = self.env["helpdesk.ticket"].search(
            [("description", "=", "Test Message")]
        )

        self.assertNotEquals(
            self.ticket.number, new_ticket.number, "Ticket should be distinct"
        )

        self.assertEqual(
            self.ticket.stage_id.id,
            self.stage1.id,
            "The id of the stage must be the same as the stage_id of the ticket.",
        )
        self.assertEqual(
            self.stage1.color_row,
            self.ticket.color_row,
            "The color_row of the stage must be the same as the color_row of the "
            "ticket.",
        )
        self.assertEqual(
            self.stage1.color_background_row,
            self.ticket.color_background_row,
            "The color_background_row of the stage must be the same as the "
            "color_background_row of the ticket.",
        )
        self.assertEqual(
            self.stage1.action_user_odoo,
            self.ticket.action_user_odoo,
            "The action_user_odoo of the stage must be the same as the action_user_odoo"
            " of the ticket.",
        )
        self.assertEqual(
            self.stage1.change_stage_to_id,
            self.ticket.change_stage_to_id,
            "The change_stage_to_id of the stage must be the same as the "
            "change_stage_to_id of the ticket.",
        )
        self.assertEqual(
            self.stage1.when_odoo_responds_change_stage_to_id,
            self.ticket.when_odoo_responds_change_stage_to_id,
            "The when_odoo_responds_change_stage_to_id of the stage must be the same as"
            " the when_odoo_responds_change_stage_to_id of the ticket.",
        )

    def test_stage_change_on_message_creation_2(self):
        """Test stage not changed if action_user_odoo is defined 1"""
        self.ticket.write({"stage_id": self.stage2.id})

        self.env["mail.message"].create(
            {
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
                "body": "Test Message",
                "email_from": "test@example.com",
            }
        )

        self.assertEqual(
            self.stage2.change_stage_to_id.color_row,
            self.ticket.color_row,
            "The color_row of the stage must be the same as the color_row of the "
            "ticket.",
        )
        self.assertEqual(
            self.stage2.change_stage_to_id.color_background_row,
            self.ticket.color_background_row,
            "The color_background_row of the stage must be the same as the "
            "color_background_row of the ticket.",
        )
        self.assertEqual(
            self.stage2.change_stage_to_id.when_odoo_responds_change_stage_to_id,
            self.ticket.when_odoo_responds_change_stage_to_id,
            "The when_odoo_responds_change_stage_to_id of the stage must be the same as"
            " the when_odoo_responds_change_stage_to_id of the ticket.",
        )

    def test_stage_change_on_message_creation_3(self):
        """Test stage not changed if when_odoo_responds_change_stage_to_id is defined"""
        self.ticket.write({"stage_id": self.stage3.id})

        self.assertEqual(
            self.stage3.when_odoo_responds_change_stage_to_id.id,
            self.ticket.when_odoo_responds_change_stage_to_id.id,
            "Ticket should be when_odoo_responds_change_stage_to_id same to Stage 3",
        )

        wizard = self.env["mail.compose.message"].create(
            {
                "composition_mode": "mass_mail",
                "template_id": self.env.ref(
                    "helpdesk_ticket_mail_message.created_response_ticket_template"
                ).id
                or False,
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
                "when_odoo_responds_change_stage_to_id": self.ticket.when_odoo_responds_change_stage_to_id.id,  # noqa: E501
            }
        )
        wizard.action_send_mail()

        self.assertEqual(
            self.stage3.when_odoo_responds_change_stage_to_id.color_row,
            self.ticket.color_row,
            "The color_row of the stage must be the same as the color_row of the "
            "ticket.",
        )
        self.assertEqual(
            self.stage3.when_odoo_responds_change_stage_to_id.color_background_row,
            self.ticket.color_background_row,
            "The color_background_row of the stage must be the same as the "
            "color_background_row of the ticket.",
        )
        self.assertEqual(
            self.stage3.when_odoo_responds_change_stage_to_id.action_user_odoo,
            self.ticket.action_user_odoo,
            "The action_user_odoo of the stage must be the same as the action_user_odoo"
            " of the ticket.",
        )
        self.assertEqual(
            self.stage3.when_odoo_responds_change_stage_to_id.change_stage_to_id,
            self.ticket.change_stage_to_id,
            "The change_stage_to_id of the stage must be the same as the "
            "change_stage_to_id of the ticket.",
        )
        self.assertEqual(
            self.stage3.when_odoo_responds_change_stage_to_id.id,
            self.ticket.stage_id.id,
            "The when_odoo_responds_change_stage_to_id of the stage must be the same "
            "as the when_odoo_responds_change_stage_to_id of the ticket.",
        )

    @patch("odoo.addons.mail.models.mail_thread.MailThread.message_subscribe")
    def test_create_email_with_new_ticket(self, mock_message_subscribe):
        """Check that a new ticket is created if an email
        with the same email_from as the ticket is received.
        and action_user_odoo is 0 (create)"""

        self.ticket.write({"action_user_odoo": "0"})

        self.env["mail.message"].create(
            {
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
                "message_type": "email",
                "email_from": "test@example.com",
                "subject": "Test Subject",
                "body": "Test Body",
            }
        )

        new_ticket = self.env["helpdesk.ticket"].search(
            [("description", "=", "Test Body")]
        )
        self.assertTrue(new_ticket)
        self.assertEqual(new_ticket.partner_email, "test@example.com")
        self.assertEqual(new_ticket.partner_name, "Test Partner")
        mock_message_subscribe.assert_called_once()
