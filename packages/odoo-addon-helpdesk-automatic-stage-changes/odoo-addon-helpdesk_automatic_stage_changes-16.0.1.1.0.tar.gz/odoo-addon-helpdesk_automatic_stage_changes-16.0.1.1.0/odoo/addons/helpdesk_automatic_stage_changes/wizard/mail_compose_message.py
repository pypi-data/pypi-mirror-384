from odoo import models, fields, api


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    when_odoo_responds_change_stage_to_id = fields.Many2one(
        "helpdesk.ticket.stage", string="Change stage to (When Odoo responds)"
    )

    @api.model
    def default_get(self, fields):
        # TODO -> Review, apparently, if self._context.get("default_subject") is set,
        # result["subject"] is already copied from it, so the following line is redundant
        result = super(MailComposeMessage, self).default_get(fields)
        if result.get("composition_mode") and result["composition_mode"] == "comment":
            result["subject"] = self._context.get("default_subject", result["subject"])

        return result

    def action_send_mail(self):
        if (
            self.model == "helpdesk.ticket"
            and self.when_odoo_responds_change_stage_to_id
            and self.composition_mode == "mass_mail"
        ):
            ticket = self.env[self.model].browse(self.res_id)
            vals = {
                "when_odoo_responds_change_stage_to_id": self.when_odoo_responds_change_stage_to_id.id,  # noqa: E501
                "stage_id": self.when_odoo_responds_change_stage_to_id.id,
            }
            ticket.write(vals)
        return super(MailComposeMessage, self).action_send_mail()
