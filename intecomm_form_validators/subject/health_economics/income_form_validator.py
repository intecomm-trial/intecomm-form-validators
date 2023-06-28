from edc_constants.constants import MONTHLY, WEEKLY, YEARLY, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_crf.utils import raise_if_crf_does_not_exist
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class HealthEconomicsIncomeFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicshouseholdhead",
        )
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicspatient",
        )
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicsassets",
        )
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicsproperty",
        )

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

        self.validate_other_specify(field="external_remittance_currency")
        self.required_if(YES, field="more_sources", field_required="more_sources_other")
        self.required_if(YES, field="household_debt", field_required="household_debt_value")
