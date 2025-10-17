# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from . import models
from . import wizard
from odoo import api, SUPERUSER_ID


def post_install_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    menssages = env["mail.message"]
    tickets = env["helpdesk.ticket"]

    msgs = menssages.search(
        [
            ("model", "=", "helpdesk.ticket"),
            ("message_type", "in", ["email", "comment"]),
        ]
    )
    for msg in msgs:
        if msg.res_id:
            ticket = tickets.browse(msg.res_id)
            if ticket:
                if msg.message_type == "email":
                    if (
                        msg.email_from
                        and ticket.partner_email
                        and ticket.partner_email in msg.email_from
                    ):
                        msg.update(
                            {
                                "message_type_mail": "email_received",
                                "color_row": "#FFFFFF",
                                "color_background_row": "#000000",
                            }
                        )
                    else:
                        msg.update(
                            {
                                "message_type_mail": "email_sent",
                                "color_row": "#FFFFFF",
                                "color_background_row": "#FF0000",
                            }
                        )
                elif msg.message_type == "comment":
                    msg.update(
                        {
                            "message_type_mail": "note",
                            "color_row": "#000000",
                            "color_background_row": "#23FF00",
                        }
                    )
