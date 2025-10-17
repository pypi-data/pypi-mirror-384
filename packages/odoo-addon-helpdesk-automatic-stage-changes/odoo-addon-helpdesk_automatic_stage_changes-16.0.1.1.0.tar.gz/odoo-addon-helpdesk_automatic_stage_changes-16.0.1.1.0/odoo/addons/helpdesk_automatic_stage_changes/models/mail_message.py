import base64

from odoo import api, models


class Message(models.Model):
    _inherit = "mail.message"

    @api.model
    def create(self, values):
        message = super(Message, self).create(values)
        if values.get("model") and values.get("res_id"):
            if values.get("model") == "helpdesk.ticket":
                ticket = self.env["helpdesk.ticket"].browse(values.get("res_id"))

                if (
                    values.get("email_from")
                    and ticket
                    and ticket.partner_email
                    and ticket.partner_email in values.get("email_from")
                    and values.get("message_type") == "email"
                ):
                    if ticket.action_user_odoo == "0":
                        vals = {
                            "partner_name": ticket.partner_name,
                            "company_id": ticket.company_id.id,
                            "category_id": ticket.category_id.id,
                            "partner_email": ticket.partner_email,
                            "description": values.get("body"),
                            "name": ticket.name,
                            "attachment_ids": False,
                            "channel_id": ticket.channel_id.id,
                            "partner_id": ticket.partner_id.id,
                        }
                        new_ticket = self.env["helpdesk.ticket"].sudo().create(vals)
                        new_ticket.message_subscribe(
                            partner_ids=self.env.user.partner_id.ids
                        )
                        if values.get("attachment_ids"):
                            for c_file in values.get("attachment_ids"):
                                data = c_file.read()
                                if c_file.filename:
                                    self.env["ir.attachment"].sudo().create(
                                        {
                                            "name": c_file.filename,
                                            "datas": base64.b64encode(data),
                                            "datas_fname": c_file.filename,
                                            "res_model": "helpdesk.ticket",
                                            "res_id": new_ticket.id,
                                        }
                                    )
                    elif ticket.action_user_odoo == "1" and ticket.change_stage_to_id:
                        ticket.write({"stage_id": ticket.change_stage_to_id.id})
        return message

    def _default_when_odoo_responds(self, ticket):
        return {
            "default_when_odoo_responds_change_stage_to_id": ticket.when_odoo_responds_change_stage_to_id  # noqa: E501
            and ticket.when_odoo_responds_change_stage_to_id.id
            or False,
        }

    def mail_compose_message_action(self):
        action = super(Message, self).mail_compose_message_action()
        ctx = action["context"]
        if self.model == "helpdesk.ticket" and self.res_id:
            ticket = self.env["helpdesk.ticket"].browse(self.res_id)
            ctx.update({**self._default_when_odoo_responds(ticket)})
        action["context"] = ctx
        return action

    def mail_compose_message_action_all(self):
        action = super(Message, self).mail_compose_message_action_all()
        ctx = action["context"]
        if self.model == "helpdesk.ticket":
            ticket = self.env["helpdesk.ticket"].browse(self.res_id)
            ctx.update({**self._default_when_odoo_responds(ticket)})
        action["context"] = ctx
        return action

    def mail_compose_message_action_resend(self):
        action = super(Message, self).mail_compose_message_action_resend()
        ctx = action["context"]
        if self.model == "helpdesk.ticket":
            ticket = self.env["helpdesk.ticket"].browse(self.res_id)
            ctx.update({**self._default_when_odoo_responds(ticket)})
        action["context"] = ctx
        return action
