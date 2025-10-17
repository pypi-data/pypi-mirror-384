from odoo.tests import tagged, common
from unittest.mock import patch


@tagged("post_install", "-at_install", "helpdesk_ticket_mail_message")
class TestMailComposeMessage(common.TransactionCase):
    def setUp(self):
        super(TestMailComposeMessage, self).setUp()
        self.helpdesk_ticket = self.env.ref("helpdesk_mgmt.helpdesk_ticket_1")
        self.MailComposeWizard = self.env["mail.compose.message"]
        self.template_id = self.env.ref(
            "helpdesk_ticket_mail_message.created_response_ticket_template"
        )
        self.mail_compose_data = {
            "composition_mode": "comment",
            "partner_ids": [(6, 0, [self.helpdesk_ticket.partner_id.id])],
            "template_id": self.template_id.id,
        }

    @patch(
        "odoo.addons.mail.wizard.mail_compose_message.MailComposer._onchange_template_id_wrapper"
    )
    def test__onchange_template_id_wrapper(self, mock_mail_onchange):
        """Check that original mail onchange wrapper is not called."""

        wizard = self.MailComposeWizard.create(self.mail_compose_data)

        wizard.with_context(
            skip_onchange_template_id=True
        )._onchange_template_id_wrapper()
        mock_mail_onchange.assert_not_called()

        wizard.with_context(
            skip_onchange_template_id=False
        )._onchange_template_id_wrapper()
        mock_mail_onchange.assert_called_once()
