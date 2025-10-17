# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
import email

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_process(
        self,
        model,
        message,
        custom_values=None,
        save_original=False,
        strip_attachments=False,
        thread_id=None,
    ):
        thread_id = super(MailThread, self).message_process(
            model, message, custom_values, save_original, strip_attachments, thread_id
        )
        # extract message bytes - we are forced to pass the message as binary because
        # we don't know its encoding until we parse its headers and hence can't
        # convert it to utf-8 for transport between the mailgate script and here.
        if isinstance(message, xmlrpclib.Binary):
            message = bytes(message.data)
        if isinstance(message, str):
            message = message.encode("utf-8")
        message = email.message_from_bytes(message, policy=email.policy.SMTP)

        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg_dict = self.message_parse(message, save_original=save_original)

        mail_message = self.env["mail.message"].search(
            [("message_id", "=", msg_dict.get("message_id"))]
        )
        if mail_message:
            for header in message._headers:
                if header[0].lower() == "delivered-to":
                    mail_message.delivered_to = header[1]

                    ticket = self.env[mail_message.model].browse(mail_message.res_id)
                    if ticket and mail_message.model == "helpdesk.ticket":
                        ticket.delivered_to = header[1]

                    break

        return thread_id
