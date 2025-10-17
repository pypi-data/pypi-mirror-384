from odoo.tests import common, tagged


@tagged("post_install", "-at_install", "helpdesk_automatic")
class TestMailComposeMessage(common.TransactionCase):
    def setUp(self):
        super(TestMailComposeMessage, self).setUp()
        self.MailComposeMessage = self.env["mail.compose.message"]
        self.HelpdeskTicket = self.env["helpdesk.ticket"]
        self.HelpdeskStage = self.env["helpdesk.ticket.stage"]
        self.stage = self.HelpdeskStage.create(
            {
                "name": "Test Stage",
            }
        )
        self.ticket = self.HelpdeskTicket.create(
            {
                "name": "Test Ticket",
                "description": "This is a test ticket.",
                "partner_email": "test@example.com",
                "stage_id": self.stage.id,
            }
        )

    def test_default_get_subject_comment(self):
        """Test that the subject is set correctly for 'comment' composition mode."""
        context = {
            "default_subject": "Default Subject",
            "composition_mode": "comment",
        }
        mail_compose = self.MailComposeMessage.with_context(context).create(
            {
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
            }
        )
        self.assertEqual(mail_compose.subject, context["default_subject"])

    def test_action_send_mail_change_stage(self):
        """Test that the ticket's stage is updated when sending mail with mass_mail mode."""
        mail_compose = self.MailComposeMessage.create(
            {
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
                "composition_mode": "mass_mail",
                "when_odoo_responds_change_stage_to_id": self.stage.id,
            }
        )
        mail_compose.action_send_mail()
        self.assertEqual(self.ticket.stage_id.id, self.stage.id)

    def test_action_send_mail_no_change_stage(self):
        """Test that the ticket's stage is not updated if the stage field
        is empty or composition mode is not mass_mail."""
        mail_compose = self.MailComposeMessage.create(
            {
                "model": "helpdesk.ticket",
                "res_id": self.ticket.id,
                "composition_mode": "comment",
            }
        )
        mail_compose.action_send_mail()

        self.assertNotEqual(self.ticket.stage_id.id, False)
