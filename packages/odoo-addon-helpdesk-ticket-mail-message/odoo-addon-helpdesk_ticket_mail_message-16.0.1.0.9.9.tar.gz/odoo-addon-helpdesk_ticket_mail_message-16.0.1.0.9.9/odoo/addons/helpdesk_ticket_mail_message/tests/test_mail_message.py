from odoo.tests import common, tagged


@tagged("post_install", "-at_install", "helpdesk_ticket_mail_message")
class TestMailMessage(common.TransactionCase):
    def setUp(self):
        super(TestMailMessage, self).setUp()
        self.Message = self.env["mail.message"]
        self.Ticket = self.env["helpdesk.ticket"]
        self.ticket = self.Ticket.create(
            {
                "name": "Test Ticket",
                "description": "Test Description",
                "partner_email": "test@example.com",
                "partner_name": "Test Partner",
                "category_id": self.env.ref("helpdesk_mgmt.helpdesk_category_1").id,
            }
        )
        self.message_values = {
            "model": "helpdesk.ticket",
            "res_id": self.ticket.id,
            "message_type": "email",
            "email_from": "test@example.com",
            "subject": "Test Subject",
            "body": "Test Body",
        }

    def test_create_email_received(self):
        """
        Check that a received email message is configured correctly.
        Any message created without message_type_mail in the context
        will be flagged as email_received in the helpdesk_ticket module.
        (model: helpdesk.ticket, res_id: helpdesk.ticket.id)
        """

        message = self.Message.create(self.message_values)

        self.assertEqual(message.message_type_mail, "email_received")
        self.assertEqual(message.color_row, "#FFFFFF")
        self.assertEqual(message.color_background_row, "#000000")

    def test_create_email_sent(self):
        """
        Check that a sent email message is configured correctly.
        Only messages with message_type_mail in the context will be
        flagged as email_sent in the helpdesk_ticket module.
        (model: helpdesk.ticket, res_id: helpdesk.ticket.id)
        """

        message = self.Message.with_context(
            default_message_type_mail="email_sent"
        ).create(self.message_values)

        self.assertEqual(message.message_type_mail, "email_sent")
        self.assertEqual(message.color_row, "#FFFFFF")
        self.assertEqual(message.color_background_row, "#FF0000")

    def test_create_email_sent_no_context(self):
        """
        Check that a sent email message from the default company email
        is flagged as email_sent in the helpdesk_ticket module.
        (model: helpdesk.ticket, res_id: helpdesk.ticket.id)"""
        message_values = self.message_values.copy()
        message_values.update({"email_from": self.env.user.company_id.email})
        message = self.Message.create(message_values)

        self.assertEqual(message.message_type_mail, "email_sent")
        self.assertEqual(message.color_row, "#FFFFFF")
        self.assertEqual(message.color_background_row, "#FF0000")

    def test_create_comment(self):
        """Check that a comment message is configured correctly."""

        self.message_values["message_type"] = "comment"
        message = self.Message.create(self.message_values)

        self.assertEqual(message.message_type_mail, "note")
        self.assertEqual(message.color_row, "#000000")
        self.assertEqual(message.color_background_row, "#23FF00")
