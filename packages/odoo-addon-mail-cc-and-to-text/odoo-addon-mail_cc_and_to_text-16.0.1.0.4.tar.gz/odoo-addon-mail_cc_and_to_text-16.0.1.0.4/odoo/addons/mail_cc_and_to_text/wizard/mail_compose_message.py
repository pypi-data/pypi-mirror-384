# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    email_to = fields.Char("To", help="Message recipients (emails)")
    email_cc = fields.Char("Cc", help="Carbon copy message recipients")

    def get_mail_values(self, res_ids):
        results = super(MailComposeMessage, self).get_mail_values(res_ids)
        if self.composition_mode == "mass_mail":
            for res_id in res_ids:
                results[res_id].update(
                    {
                        "email_cc": self.email_cc,
                        "email_to": self.email_to,
                    }
                )
        return results
