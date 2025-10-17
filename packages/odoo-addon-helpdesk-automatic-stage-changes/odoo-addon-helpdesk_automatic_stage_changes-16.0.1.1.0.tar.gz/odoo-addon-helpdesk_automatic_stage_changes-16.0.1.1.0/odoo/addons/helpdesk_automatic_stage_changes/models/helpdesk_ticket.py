from odoo import models, fields, api, _


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    action_user_odoo = fields.Selection(
        selection=[
            ("0", _("Open new ticket")),
            ("1", _("Change stage")),
        ],
        string="Action when a user responds",
    )

    change_stage_to_id = fields.Many2one(
        "helpdesk.ticket.stage", string="Change stage to"
    )

    when_odoo_responds_change_stage_to_id = fields.Many2one(
        "helpdesk.ticket.stage", string="Change stage to (When Odoo responds)"
    )

    @api.model
    def create(self, vals):
        """
        Update stage values when creating the ticket
        """
        ticket = super().create(vals)
        if ticket.stage_id:
            stage_obj = self.env["helpdesk.ticket.stage"].browse([ticket.stage_id.id])
            ticket.write(
                {
                    "action_user_odoo": stage_obj.action_user_odoo,
                    "change_stage_to_id": stage_obj.change_stage_to_id.id,
                    "when_odoo_responds_change_stage_to_id": stage_obj.when_odoo_responds_change_stage_to_id.id,  # noqa: E501
                    "color_row": stage_obj.color_row,
                    "color_background_row": stage_obj.color_background_row,
                }
            )
        return ticket

    def write(self, vals):
        """
        Update stage values when updating the ticket
        """
        if vals.get("stage_id"):
            stage_obj = self.env["helpdesk.ticket.stage"].browse([vals["stage_id"]])
            vals["action_user_odoo"] = stage_obj.action_user_odoo
            vals["change_stage_to_id"] = stage_obj.change_stage_to_id.id
            vals[
                "when_odoo_responds_change_stage_to_id"
            ] = stage_obj.when_odoo_responds_change_stage_to_id.id
            vals["color_row"] = stage_obj.color_row
            vals["color_background_row"] = stage_obj.color_background_row

        return super().write(vals)

    def mail_compose_message_action(self):
        action = super(HelpdeskTicket, self).mail_compose_message_action()
        action["context"].update(
            {
                "default_when_odoo_responds_change_stage_to_id": self.when_odoo_responds_change_stage_to_id  # noqa: E501
                and self.when_odoo_responds_change_stage_to_id.id
                or False,
            }
        )
        return action
