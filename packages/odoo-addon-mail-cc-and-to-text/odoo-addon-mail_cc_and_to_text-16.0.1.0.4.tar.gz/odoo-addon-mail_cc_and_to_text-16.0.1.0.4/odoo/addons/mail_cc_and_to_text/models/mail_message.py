from odoo import models, fields, _


class MailMessage(models.Model):
    _inherit = "mail.message"

    delivered_to = fields.Char(
        string=_("Delivered To"),
        help=_("The email address the message was actually delivered to."),
        copy=False,
    )
