from typing import Tuple

from django.urls import reverse
from django.utils.html import format_html
from edc_constants.constants import COMPLETE, DM, HIV, HTN, YES
from edc_form_validators import FormValidator

INVALID_PATIENT_COUNT = "INVALID_PATIENT_COUNT"
INVALID_RANDOMIZE = "INVALID_RANDOMIZE"
INVALID_PATIENT = "INVALID_PATIENT"
INVALID_CONDITION_RATIO = "INVALID_CONDITION_RATIO"


def calculate_ratio(patients) -> Tuple[float, float]:
    ncd = 0.0
    hiv = 0.0
    for patient_log in patients:
        if patient_log.conditions.filter(name__in=[DM, HTN]).exists():
            ncd += 1.0
        if patient_log.conditions.filter(name__in=[HIV]).exists():
            hiv += 1.0
    return ncd, hiv


class PatientGroupFormValidator(FormValidator):
    def clean(self):

        self.block_changes_if_randomized()
        self.confirm_group_size_or_raise()

        # confirm complete cannot be changed if randomized
        if self.cleaned_data.get("status") != COMPLETE and self.instance.randomized:
            self.raise_validation_error(
                {"status": "Invalid. Group has already been randomized"}, INVALID_RANDOMIZE
            )
        if self.cleaned_data.get("randomize") != YES and self.instance.randomized:
            self.raise_validation_error(
                {"randomize": "Invalid. Group has already been randomized"}, INVALID_RANDOMIZE
            )

        # confirm complete before randomize == YES
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
        ncd = 0.0
        hiv = 0.0
        for patient_log in self.cleaned_data.get("patients"):
            patient_log_url = reverse(
                "intecomm_screening_admin:intecomm_screening_patientlog_change",
                args=(patient_log.id,),
            )
            if patient_log.stable != YES:
                errmsg = format_html(
                    "Patient is not known to be stable and in-care. "
                    f'See <a href="{patient_log_url}">{patient_log}</a>'
                )
                self.raise_validation_error(errmsg, INVALID_PATIENT)
            if not patient_log.screening_identifier:
                errmsg = format_html(
                    "Patient has not been screened for eligibility. "
                    f'See <a href="{patient_log_url}">{patient_log}</a>'
                )
                self.raise_validation_error(errmsg, INVALID_PATIENT)
            if not patient_log.subject_identifier:
                errmsg = format_html(
                    "Patient has not consented. "
                    f'See <a href="{patient_log_url}">{patient_log}</a>'
                )
                self.raise_validation_error(errmsg, INVALID_PATIENT)
        ncd, hiv = calculate_ratio(self.cleaned_data.get("patients"))
        ratio = ncd / hiv
        group_name = self.cleaned_data.get("name")
        if not (2.0 <= ratio <= 2.7):
            url = reverse("intecomm_screening_admin:intecomm_screening_patientlog_changelist")
            url = f"{url}?q={group_name}"
            errmsg = format_html(
                f"Ratio NDC:HIV not met. Expected at least 2:1. Got {int(ncd)}:{int(hiv)}. "
                f'See group <a href="{url}">{group_name}</a>',
            )
            self.raise_validation_error(errmsg, INVALID_CONDITION_RATIO)

    def block_changes_if_randomized(self):
        if self.instance.randomized:
            self.raise_validation_error(
                "A randomized group may not be changed", INVALID_RANDOMIZE
            )

    def confirm_group_size_or_raise(self):
        """Confirm at least 8 if complete."""
        if (
            self.cleaned_data.get("status") == COMPLETE
            and self.cleaned_data.get("patients").count() < 8
        ):
            self.raise_validation_error(
                {"status": "Invalid. Must have at least 8 patients"}, INVALID_PATIENT_COUNT
            )

    def check_ratio_or_raise(self, patient_log, ncd, hiv):
        # check ratio
        if patient_log.conditions.filter(name__in=[DM, HTN]).exists():
            ncd += 1.0
        if patient_log.conditions.filter(name__in=[HIV]).exists():
            hiv += 1.0
        return ncd, hiv
