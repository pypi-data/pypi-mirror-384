# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, fields, models


class StockStorageLocationSequence(models.Model):
    _name = "stock.storage.location.sequence"
    _description = "Sequence of locations to put-away the package type"
    _order = "sequence,id"

    package_type_id = fields.Many2one("stock.package.type", required=True)
    sequence = fields.Integer(required=True)
    location_id = fields.Many2one(
        "stock.location",
        required=True,
    )
    location_putaway_strategy = fields.Selection(
        related="location_id.pack_putaway_strategy"
    )
    location_sequence_cond_ids = fields.Many2many(
        string="Conditions",
        comodel_name="stock.storage.location.sequence.cond",
        relation="stock_location_sequence_cond_rel",
        help="All conditions have to match to apply the put-away strategy.",
    )

    def _format_package_type_message(self, last=False):
        self.ensure_one()
        # TODO improve ugly code
        type_matching_locations = self.location_id.get_storage_locations().filtered(
            lambda loc: self.package_type_id
            in loc.computed_storage_category_id.capacity_ids.mapped("package_type_id")
        )
        if type_matching_locations:
            # Get the selection description
            pack_storage_strat = None
            pack_storage_strat_selection = self.location_id._fields[
                "pack_putaway_strategy"
            ]._description_selection(self.env)
            for strat in pack_storage_strat_selection:
                if strat[0] == self.location_id.pack_putaway_strategy:
                    pack_storage_strat = strat[1]
                    break
            msg = (
                f' * <span style="color: green;">'
                f"{self.location_id.name} ({pack_storage_strat})</span>"
            )
            if last:
                # If last, we want to check if restrictions are defined on
                # capacities accepting this package type
                # TODO improve ugly code
                capacities = type_matching_locations.mapped(
                    "computed_storage_category_id.capacity_ids"
                ).filtered(
                    lambda lst, package_type=self.package_type_id: package_type
                    == lst.package_type_id
                    and not lst.storage_category_id.has_restrictions
                )
                if not capacities:
                    msg = _(
                        ' * <span style="color: orange;">{location} (WARNING: '
                        "restrictions are active on storage categories "
                        "matching this package type)</span>"
                    ).format(location=self.location_id.name)
        else:
            msg = _(
                ' * <span style="color: red;">{location} '
                "(WARNING: no suitable location matching package type)</span>"
            ).format(location=self.location_id.name)
        return msg

    def button_show_locations(self):
        xmlid = "stock.action_location_form"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [
            ("parent_path", "=ilike", f"{self.location_id.parent_path}%"),
            (
                "computed_storage_capacity_ids",
                "in",
                self.package_type_id.storage_category_capacity_ids.ids,
            ),
        ]
        return action

    def can_be_applied(self, putaway_location, quant, product):
        """Check if conditions are met."""
        self.ensure_one()
        for cond in self.location_sequence_cond_ids:
            if not cond.evaluate(self, putaway_location, quant, product):
                return False
        return True
