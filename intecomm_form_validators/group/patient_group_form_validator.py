from decimal import Decimal

from django.urls import reverse
from django.utils.html import format_html
from edc_constants.constants import COMPLETE, YES
from edc_form_validators import FormValidator

from ..utils import calculate_ratio

INVALID_PATIENT_COUNT = "INVALID_PATIENT_COUNT"
INVALID_RANDOMIZE = "INVALID_RANDOMIZE"
INVALID_PATIENT = "INVALID_PATIENT"
INVALID_CONDITION_RATIO = "INVALID_CONDITION_RATIO"


class PatientGroupFormValidator(FormValidator):

    group_count_min = 14

    def clean(self):

        self.block_changes_if_randomized()

        self.confirm_group_size_or_raise()

        if (
            self.cleaned_data.get("status") != COMPLETE
            and self.cleaned_data.get("randomize") == YES
        ):
            self.raise_validation_error(
                {"randomize": "Invalid. Group is not complete"}, INVALID_RANDOMIZE
            )

        if self.cleaned_data.get("status") == COMPLETE:
            self.review_patients()

    def review_patients(self):
        for patient_log in self.cleaned_data.get("patients"):
            if patient_log.stable != YES:
                errmsg = format_html(
                    "Patient is not known to be stable and in-care. "
                    f'See <a href="{self.patient_log_url(patient_log)}">{patient_log}</a>'
                )
                self.raise_validation_error(errmsg, INVALID_PATIENT)
            if not patient_log.screening_identifier:
                errmsg = format_html(
                    "Patient has not been screened for eligibility. "
                    f'See <a href="{self.patient_log_changelist_url(patient_log.id)}">'
                    f"{patient_log}</a>"
                )
                self.raise_validation_error(errmsg, INVALID_PATIENT)
            if not patient_log.subject_identifier:
                errmsg = format_html(
                    "Patient has not consented. "
                    f'See <a href="{self.patient_log_changelist_url(patient_log.id)}">'
                    f"{patient_log}</a>"
                )
                self.raise_validation_error(errmsg, INVALID_PATIENT)
        self.validate_patient_group_ratio()

    @staticmethod
    def patient_log_url(patient_log) -> str:
        return reverse(
            "intecomm_screening_admin:intecomm_screening_patientlog_change",
            args=(patient_log.id,),
        )

    @staticmethod
    def patient_log_changelist_url(search_term) -> str:
        url = reverse(
            "intecomm_screening_admin:intecomm_screening_patientlog_changelist",
        )
        return f"{url}?q={search_term}"

    def validate_patient_group_ratio(self):
        if self.cleaned_data.get("status") and self.cleaned_data.get("status") == COMPLETE:
            ncd, hiv, ratio = calculate_ratio(self.cleaned_data.get("patients"))
            if not (Decimal("2.00") <= ratio <= Decimal("2.70")):
                group_name = self.cleaned_data.get("name")
                errmsg = format_html(
                    "Ratio NDC:HIV not met. Expected at least 2:1. "
                    f"Got {int(ncd)}:{int(hiv)}. "
                    f'See group <a href="{self.patient_log_changelist_url(group_name)}">'
                    f"{group_name}</a>",
                )
                self.raise_validation_error(errmsg, INVALID_CONDITION_RATIO)

    def block_changes_if_randomized(self):
        if self.instance.randomized:
            self.raise_validation_error(
                "A randomized group may not be changed", INVALID_RANDOMIZE
            )

    def confirm_group_size_or_raise(self):
        """Confirm at least 14 if complete."""
        if (
            self.cleaned_data.get("status") == COMPLETE
            and self.cleaned_data.get("patients").count() < self.group_count_min
        ):
            self.raise_validation_error(
                {
                    "status": f"Invalid. Must have at least { self.group_count_min} patients. "
                    f"Got {self.cleaned_data.get('patients').count()}."
                },
                INVALID_PATIENT_COUNT,
            )
