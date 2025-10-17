from odoo import models, fields


class HelpdeskTicketTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    default_team_from_value = fields.Char(
        string="Default 'From' Email",
        help="Default email address used in the 'From' field when sending emails from tickets of this team.",  # noqa: E501
    )
