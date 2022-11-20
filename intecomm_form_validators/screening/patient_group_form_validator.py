from django.utils.html import format_html
from edc_constants.constants import COMPLETE, NEW, YES
from edc_form_validators import FormValidator

from ..constants import RECRUITING
from ..utils import (
    PatientGroupRatioError,
    PatientGroupSizeError,
    PatientNotConsentedError,
    PatientNotScreenedError,
    PatientNotStableError,
    confirm_patient_group_size_or_raise,
    confirm_patients_stable_and_screened_and_consented_or_raise,
    verify_patient_group_ratio_raise,
)

INVALID_PATIENT_COUNT = "INVALID_PATIENT_COUNT"
INVALID_RANDOMIZE = "INVALID_RANDOMIZE"
INVALID_PATIENT = "INVALID_PATIENT"
INVALID_CONDITION_RATIO = "INVALID_CONDITION_RATIO"
INVALID_STATUS = "INVALID_STATUS"


class PatientGroupScreeningFormValidator(FormValidator):

    group_count_min = 14

    def clean(self):

        self.block_changes_if_already_randomized()

        if self.cleaned_data.get("status") and self.cleaned_data.get("status") not in [
            NEW,
            RECRUITING,
            COMPLETE,
        ]:
            self.raise_validation_error({"status": "Invalid selection"}, INVALID_STATUS)

        if (
            self.cleaned_data.get("status") != COMPLETE
            and self.cleaned_data.get("randomize_now") == YES
        ):
            self.raise_validation_error(
                {"randomize_now": "Invalid. Group is not complete"}, INVALID_RANDOMIZE
            )

        if self.cleaned_data.get("status") == COMPLETE:
            self.confirm_patients_stable_and_screened_and_consented_or_raise()
            self.confirm_patient_group_size_or_raise()
            self.verify_patient_group_ratio_raise()

        if (
            self.cleaned_data.get("randomize_now") == YES
            and self.cleaned_data.get("confirm_randomize_now") != "RANDOMIZE"
        ):
            self.raise_validation_error(
                {
                    "confirm_randomize_now": (
                        "If you wish to randomize this group, please confirm"
                    )
                },
                INVALID_RANDOMIZE,
            )

    def block_changes_if_already_randomized(self):
        if self.instance.randomized:
            self.raise_validation_error(
                "A randomized group may not be changed", INVALID_RANDOMIZE
            )

    def confirm_patient_group_size_or_raise(self):
        try:
            confirm_patient_group_size_or_raise(
                enforce_group_size_min=self.cleaned_data.get("enforce_group_size_min"),
                patients=self.cleaned_data.get("patients") or self.instance.patients,
            )
        except PatientGroupSizeError as e:
            self.raise_validation_error({"__all__": str(e)}, INVALID_PATIENT_COUNT)

    def confirm_patients_stable_and_screened_and_consented_or_raise(self):
        try:
            confirm_patients_stable_and_screened_and_consented_or_raise(
                patients=self.cleaned_data.get("patients") or self.instance.patients
            )
        except (PatientNotStableError, PatientNotScreenedError, PatientNotConsentedError) as e:
            self.raise_validation_error({"__all__": str(e)}, INVALID_PATIENT)

    def verify_patient_group_ratio_raise(self):
        if self.cleaned_data.get("enforce_ratio") is None or self.cleaned_data.get(
            "enforce_ratio"
        ):
            try:
                verify_patient_group_ratio_raise(
                    patients=self.cleaned_data.get("patients") or self.instance.patients
                )
            except PatientGroupRatioError as e:
                group_name = self.cleaned_data.get("name")
                errmsg = format_html(
                    f'See group <a href="{self.instance.get_changelist_url(group_name)}">'
                    f"{group_name}</a>",
                )
                self.raise_validation_error(
                    {"__all__": f"{e} {errmsg}"}, INVALID_CONDITION_RATIO
                )

    def block_changes_if_randomized(self):
        if self.instance.randomized:
            self.raise_validation_error(
                "A randomized group may not be changed", INVALID_RANDOMIZE
            )
