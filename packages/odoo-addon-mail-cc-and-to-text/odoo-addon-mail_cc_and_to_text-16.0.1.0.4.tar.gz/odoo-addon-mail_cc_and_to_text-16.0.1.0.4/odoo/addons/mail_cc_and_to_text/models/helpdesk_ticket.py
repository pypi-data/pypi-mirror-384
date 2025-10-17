from odoo import api, models, fields, _


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    original_email_to = fields.Char(
        string=_("Original Email To"),
        help=_("The original email address the ticket was sent to."),
        copy=False,
    )
    delivered_to = fields.Char(
        string=_("Delivered To"),
        help=_("The email address the ticket was actually delivered to."),
        copy=False,
    )

    @api.model
    def message_new(self, msg, custom_values=None):
        """
        Override message_new from mail gateway so we can store the original 'to' email
        """
        ticket = super().message_new(msg, custom_values)

        ticket.original_email_to = msg.get("to", False)
        return ticket
