from edc_constants.constants import MONTHLY, WEEKLY, YEARLY, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import FormValidator


class HealthEconomicsIncomeFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        for fld in [
            "wages",
            "selling",
            "rental_income",
            "pension",
            "ngo_assistance",
            "interest",
            "internal_remittance",
            "external_remittance",
        ]:
            self.applicable_if(YES, field=fld, field_applicable=f"{fld}_value_known")
            self.required_if(
                WEEKLY,
                MONTHLY,
                YEARLY,
                field=f"{fld}_value_known",
                field_required=f"{fld}_value",
            )

        self.validate_other_specify(field="external_remit_currency")
        self.required_if(YES, field="more_sources", field_required="more_sources_other")
        self.required_if(YES, field="household_debt", field_required="household_debt_value")
