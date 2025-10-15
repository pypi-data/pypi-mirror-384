from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ContractIbanChangeWizard(models.TransientModel):
    _inherit = "contract.iban.change.wizard"

    change_contract_group = fields.Boolean(
        string="Change Contract Group",
        help="If checked, the contract group will be changed "
        "to the selected contract group.",
    )
    available_contract_group_ids = fields.One2many(
        "contract.group",
        string="Available Contract Groups",
        compute="_compute_available_contract_group_ids",
    )
    contract_group_id = fields.Many2one(
        "contract.group",
        string="Contract Group",
        help="The contract groups that are available for the selected contracts. "
        "Keep empty to create a new contract group.",
    )

    @api.onchange("account_banking_mandate_id", "contract_ids")
    def _compute_available_contract_group_ids(self):
        if not self.contract_ids or not self.account_banking_mandate_id:
            self.available_contract_group_ids = []
            return

        self.available_contract_group_ids = (
            self.env["contract.group"]
            .search([("partner_id", "=", self.contract_ids[0].partner_id.id)])
            .filtered(
                lambda x: x.validate_contract_to_group(
                    self.contract_ids[0], mandate_id=self.account_banking_mandate_id
                )[0]
            )
        )

    def _data_to_update_contracts(self):
        data = super()._data_to_update_contracts()
        if not self.change_contract_group:
            self._validate_change_without_contract_group(self.contract_ids)
            return data
        if not self.contract_group_id:
            self.contract_group_id = self.env[
                "contract.group"
            ].get_or_create_contract_group_id(
                self.contract_ids[0],
                new_group=True,
            )
        for contract in self.contract_ids:
            valid, error_message = self.contract_group_id.validate_contract_to_group(
                contract,
                self.account_banking_mandate_id,
            )
            if not valid:
                raise ValidationError(error_message)
        data.update({"contract_group_id": self.contract_group_id.id})
        return data

    def _validate_change_without_contract_group(self, contracts):
        """Check if all the contracts in the contract_group_id are in
        the contracts list"""
        if not contracts:
            return
        contract_groups = self.contract_ids.mapped("contract_group_id")
        for contract_group in contract_groups:
            if not [
                contract
                for contract in contract_group.get_active_contracts()
                if contract not in self.contract_ids
            ]:
                continue
            raise ValidationError(
                _(
                    "You need to select all the contracts in the contract group "
                    "'{}' to change the IBAN of all the contracts.".format(
                        contract_group.code
                    )
                )
            )
