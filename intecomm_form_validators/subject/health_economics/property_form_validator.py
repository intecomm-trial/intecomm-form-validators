from edc_constants.constants import YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import FormValidator


class HealthEconomicsPropertyFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        self.applicable_if(YES, field="land_owner", field_applicable="land_value_known")
        self.required_if(YES, field="land_value_known", field_required="land_value")
        self.applicable_if(
            YES, field="land_additional", field_applicable="land_additional_known"
        )
        self.required_if(
            YES, field="land_additional_known", field_required="land_additional_value"
        )
