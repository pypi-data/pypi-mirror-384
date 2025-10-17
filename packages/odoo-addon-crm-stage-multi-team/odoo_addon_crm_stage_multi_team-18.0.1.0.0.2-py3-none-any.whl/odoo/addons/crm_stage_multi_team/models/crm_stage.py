# Copyright 2025 Teacnativa - Eduardo Ezerouali
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import Command, fields, models


class CrmStage(models.Model):
    _inherit = "crm.stage"

    team_ids = fields.Many2many("crm.team", string="Sales Teams")

    def write(self, vals):
        for record in self:
            if record.team_id and record.team_id not in record.team_ids:
                vals["team_ids"] = [Command.set(record.team_id.ids)]
        res = super().write(vals)
        return res
