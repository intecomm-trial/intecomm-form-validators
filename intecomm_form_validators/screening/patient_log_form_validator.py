from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from edc_constants.constants import NO, YES
from edc_form_validators import FormValidator
from edc_form_validators.base_form_validator import INVALID_ERROR
from edc_screening.utils import get_subject_screening_model_cls

from .patient_group_form_validator import INVALID_RANDOMIZE

INVALID_APPOINTMENT_DATE = "INVALID_APPOINTMENT_DATE"
INVALID_GROUP = "INVALID_GROUP"
INVALID_CHANGE_ALREADY_SCREENED = "INVALID_CHANGE_ALREADY_SCREENED"


class PatientLogFormValidator(FormValidator):
    def __init__(self, subject_screening=None, **kwargs) -> None:
        self._subject_screening = subject_screening
        super().__init__(**kwargs)

    @property
    def age_in_years(self) -> int | None:
        return self.cleaned_data.get("age_in_years")

    def clean(self):
        if (
            self.instance.id
            and self.instance.patientgroup_set.filter(randomized=True).exists()
        ):
            self.raise_validation_error(
                "A patient in a randomized group may not be changed", INVALID_RANDOMIZE
            )

        if self.subject_screening and self.subject_screening.gender != self.cleaned_data.get(
            "gender"
        ):
            self.raise_validation_error(
                "Patient has already screened. Gender may not change",
                INVALID_CHANGE_ALREADY_SCREENED,
            )
        if (
            self.subject_screening
            and self.subject_screening.initials != self.cleaned_data.get("initials")
        ):
            self.raise_validation_error(
                "Patient has already screened. Initials may not change",
                INVALID_CHANGE_ALREADY_SCREENED,
            )
        if (
            self.subject_screening
            and self.subject_screening.hospital_identifier
            != self.cleaned_data.get("hospital_identifier")
        ):
            self.raise_validation_error(
                "Patient has already screened. Heath Facility Identifier may not change",
                INVALID_CHANGE_ALREADY_SCREENED,
            )

        self.validate_age()

        if (
            self.subject_screening
            and self.cleaned_data.get("site")
            and self.subject_screening.site.id != self.cleaned_data.get("site").id
        ):
            self.raise_validation_error(
                "Patient has already screened. Site / Health Facility may not change",
                INVALID_CHANGE_ALREADY_SCREENED,
            )

        if (
            self.cleaned_data.get("last_appt_date")
            and self.cleaned_data.get("report_datetime")
            and self.cleaned_data.get("last_appt_date")
            > self.cleaned_data.get("report_datetime").date()
        ):
            self.raise_validation_error(
                {"last_appt_date": "Cannot be a future date"}, INVALID_APPOINTMENT_DATE
            )

        if (
            self.cleaned_data.get("next_appt_date")
            and self.cleaned_data.get("report_datetime")
            and self.cleaned_data.get("next_appt_date")
            < self.cleaned_data.get("report_datetime").date()
        ):
            self.raise_validation_error(
                {"next_appt_date": "Must be a future date"}, INVALID_APPOINTMENT_DATE
            )
        self.required_if(
            YES, field="first_health_talk", field_required="first_health_talk_date"
        )
        self.required_if(
            YES, field="second_health_talk", field_required="second_health_talk_date"
        )

        if self.subject_screening and self.cleaned_data.get("willing_to_screen") != YES:
            self.raise_validation_error(
                {"willing_to_screen": "Patient has already screened. Expected YES."},
                INVALID_ERROR,
            )

        self.applicable_if(
            NO, field="willing_to_screen", field_applicable="screening_refusal_reason"
        )
        self.validate_other_specify(
            field="screening_refusal_reason",
            other_specify_field="screening_refusal_reason_other",
        )

    @property
    def subject_screening(self):
        if not self._subject_screening:
            try:
                self._subject_screening = get_subject_screening_model_cls().objects.get(
                    screening_identifier=self.instance.screening_identifier
                )
            except ObjectDoesNotExist:
                self._subject_screening = None
        return self._subject_screening

    def validate_age(self) -> None:
        if self.age_in_years is not None and not (18 <= self.age_in_years < 110):
            self.raise_validation_error(
                {"age_in_years": "Invalid. Patient must be 18 years or older"},
                INVALID_ERROR,
            )
