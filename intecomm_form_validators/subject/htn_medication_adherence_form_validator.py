from edc_adherence.choices import MISSED_PILLS
from edc_adherence.form_validator_mixin import MedicationAdherenceFormValidatorMixin
from edc_constants.constants import NEVER, OTHER
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import FormValidator


class HtnMedicationAdherenceFormValidator(
    MedicationAdherenceFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        self.confirm_visual_scores_match()

        self.required_if(
            *[t[0] for t in MISSED_PILLS if t[0] != NEVER],
            field="last_missed_pill",
            field_required="meds_missed_in_days",
            field_required_evaluate_as_int=True,
        )

        self.require_m2m_if_missed_any_pills()
        self.missed_pill_reason_other_specify()

        self.required_if(
            *[t[0] for t in MISSED_PILLS if t[0] != NEVER],
            field="last_missed_pill",
            field_required="meds_shortage_in_days",
            field_required_evaluate_as_int=True,
        )

        if self.cleaned_data.get("last_missed_pill"):
            if self.cleaned_data.get("last_missed_pill") == NEVER:
                self.m2m_not_required("meds_shortage_reason")
            else:
                self.m2m_required("meds_shortage_reason")
        self.missed_pill_reason_other_specify()

        self.m2m_other_specify(
            OTHER,
            m2m_field="meds_shortage_reason",
            field_other="meds_shortage_reason_other",
        )
