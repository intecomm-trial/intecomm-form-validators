from edc_constants.constants import YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_visit_schedule.utils import raise_if_baseline


class ClinicalReviewFormValidator(CrfFormValidator):
    def clean(self):
        raise_if_baseline(self.cleaned_data.get("subject_visit"))
        self.required_if(
            YES,
            field="health_insurance",
            field_required="health_insurance_monthly_pay",
        )
        self.required_if(
            YES,
            field="patient_club",
            field_required="patient_club_monthly_pay",
        )
