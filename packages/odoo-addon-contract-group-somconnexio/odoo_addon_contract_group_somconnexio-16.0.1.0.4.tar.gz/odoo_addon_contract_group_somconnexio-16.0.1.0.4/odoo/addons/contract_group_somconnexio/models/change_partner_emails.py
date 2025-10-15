from odoo import _, models
from odoo.exceptions import ValidationError


class ChangePartnerEmails(models.AbstractModel):
    _inherit = "change.partner.emails"

    def change_contracts_emails(
        self,
        partner,
        contracts,
        emails,
        activity_args,
        change_contract_group=False,
        contract_group_id=None,
        create_contract_group=False,
    ):
        for contract in contracts:
            # Validation
            if change_contract_group:
                contract_group_id = self._validate_contract_group(
                    contract, emails, contract_group_id, create_contract_group
                )
            else:
                self._validate_change_without_contract_group(
                    contract.contract_group_id, contracts
                )
            # Post messages
            message_partner = _("Email changed ({} --> {}) in partner's contract '{}'")
            partner.message_post(
                message_partner.format(
                    ", ".join([email.email for email in contract.email_ids]),
                    ", ".join([email.email for email in emails]),
                    contract.name,
                )
            )
            message_contract = _("Contract email changed ({} --> {})")
            contract.message_post(
                message_contract.format(
                    ", ".join([email.email for email in contract.email_ids]),
                    ", ".join([email.email for email in emails]),
                )
            )
            # Update contracts
            vals = {
                "email_ids": [(6, 0, [email.id for email in emails])],
            }
            if contract_group_id:
                vals.update({"contract_group_id": contract_group_id.id})
            contract.write(vals)
            # Create activity
            self._create_activity(
                contract.id,
                activity_args,
            )

        return True

    def _validate_contract_group(
        self, contract, emails, contract_group_id=None, create_contract_group=False
    ):
        if not contract_group_id:
            contract_group_id = self.env[
                "contract.group"
            ].get_or_create_contract_group_id(
                contract,
                email_ids=emails,
                new_group=create_contract_group,
            )
        (
            validation_result,
            validation_message,
        ) = contract_group_id.validate_contract_to_group(contract, email_ids=emails)
        if not validation_result and not create_contract_group:
            raise ValidationError(validation_message)
        return contract_group_id

    def _validate_change_without_contract_group(self, contract_group_id, contracts):
        """Check if all the contracts in the contract_group_id are in
        the contracts list"""
        if not contract_group_id.contract_ids:
            return
        if not contracts:
            return
        if all(
            contract in contracts
            for contract in contract_group_id.get_active_contracts()
        ):
            return
        raise ValidationError(
            _(
                "You need to select all the contracts in the contract group "
                "'{}' to change the emails/iban of all the contracts.".format(
                    contract_group_id.code
                )
            )
        )
