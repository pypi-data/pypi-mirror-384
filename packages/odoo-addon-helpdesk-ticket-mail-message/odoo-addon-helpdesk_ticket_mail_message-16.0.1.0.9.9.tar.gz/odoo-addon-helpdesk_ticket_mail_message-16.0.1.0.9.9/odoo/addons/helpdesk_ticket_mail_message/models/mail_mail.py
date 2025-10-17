from odoo import models, fields
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools.translate import _
import logging


_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def send(self, auto_commit=False, raise_exception=False):
        """
        Override mail_mail send method to avoid sending scheduled emails
        before their scheduled date since some methods might call send() directly
        instead of using the mail queue process method.
        """
        for mail_server_id, smtp_from, batch_ids in self._split_by_mail_configuration():
            smtp_session = None
            try:
                smtp_session = self.env["ir.mail_server"].connect(
                    mail_server_id=mail_server_id, smtp_from=smtp_from
                )
            except Exception as exc:
                if raise_exception:
                    # To be consistent and backward compatible with mail_mail.send() raised
                    # exceptions, it is encapsulated into an Odoo MailDeliveryException
                    raise MailDeliveryException(
                        _("Unable to connect to SMTP Server"), exc
                    )
                else:
                    batch = self.browse(batch_ids)
                    batch.write({"state": "exception", "failure_reason": exc})
                    batch._postprocess_sent_message(
                        success_pids=[], failure_type="mail_smtp"
                    )
            else:
                batch = self.browse(batch_ids).filtered(
                    lambda m: m.scheduled_date is False
                    or m.scheduled_date <= fields.Datetime.now()
                )
                batch._send(
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session,
                )
                _logger.info(
                    "Sent batch %s emails via mail server ID #%s",
                    len(batch_ids),
                    mail_server_id,
                )
            finally:
                if smtp_session:
                    smtp_session.quit()
