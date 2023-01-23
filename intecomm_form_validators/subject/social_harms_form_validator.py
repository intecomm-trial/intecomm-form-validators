from edc_constants.constants import YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class SocialHarmsFormValidator(CrfFormValidatorMixin, FormValidator):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        for prefix in ["partner", "family", "friend", "coworker"]:
            self.applicable_if(YES, field=f"{prefix}", field_applicable=f"{prefix}_disclosure")

        for prefix in ["partner", "family", "friend", "coworker"]:
            self.applicable_if(
                YES, field=f"{prefix}_impact", field_applicable=f"{prefix}_impact_severity"
            )
            self.applicable_if(
                YES, field=f"{prefix}_impact", field_applicable=f"{prefix}_impact_status"
            )
            self.applicable_if(
                YES, field=f"{prefix}_impact", field_applicable=f"{prefix}_impact_help"
            )
            self.applicable_if(
                YES, field=f"{prefix}_impact", field_applicable=f"{prefix}_impact_referral"
            )

        for prefix in ["healthcare", "other_service", "employment", "insurance", "other"]:
            if prefix in ["other_service", "other"]:
                self.required_if(
                    YES,
                    field=f"{prefix}_impact",
                    field_required=f"{prefix}_impact_description",
                )
            self.applicable_if(
                YES, field=f"{prefix}_impact", field_applicable=f"{prefix}_impact_severity"
            )
            self.applicable_if(
                YES, field=f"{prefix}_impact", field_applicable=f"{prefix}_impact_status"
            )
            self.applicable_if(
                YES, field=f"{prefix}_impact", field_applicable=f"{prefix}_impact_help"
            )
            self.applicable_if(
                YES, field=f"{prefix}_impact", field_applicable=f"{prefix}_impact_referral"
            )
