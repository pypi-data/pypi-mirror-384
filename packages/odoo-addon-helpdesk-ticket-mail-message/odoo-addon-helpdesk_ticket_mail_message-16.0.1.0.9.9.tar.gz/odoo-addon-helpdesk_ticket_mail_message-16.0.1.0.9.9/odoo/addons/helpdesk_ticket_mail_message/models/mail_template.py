from odoo import models, fields


class MailTemplate(models.Model):
    _inherit = "mail.template"

    helpdesk_ticket_tag_ids = fields.Many2many(
        "helpdesk.ticket.tag", help="Helpdesk Tags related to this template."
    )

    def generate_email(self, res_ids, fields):
        """
        Generate email for the given record ids and fields override to force the language
        instead of relying on the ticket's partner language for helpdesk tickets.
        """
        model = self._context.get("active_model") or self._context.get(
            "params", {}
        ).get("model")
        if model == "helpdesk.ticket":
            lang = self._context.get("lang") or self.env.lang
            if lang:
                self = self.with_context(lang=lang)
                self.lang = lang

        return super().generate_email(res_ids, fields)
