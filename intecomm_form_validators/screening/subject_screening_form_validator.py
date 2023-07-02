from __future__ import annotations

from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.apps import apps as django_apps
from edc_consent.utils import get_consent_for_period_or_raise
from edc_constants.constants import MALE, NO, YES
from edc_form_validators import INVALID_ERROR, FormValidator
from edc_model import InvalidFormat, duration_to_date

INVALID_DURATION_IN_CARE = "invalid_duration_in_care"


class SubjectScreeningFormValidator(FormValidator):
    def clean(self):
        if not self.patient_log_identifier:
            self.raise_validation_error("Select a Patient log", error_code=INVALID_ERROR)
        self.get_consent_for_period_or_raise()

        if (
            self.cleaned_data.get("consent_ability")
            and self.cleaned_data.get("consent_ability") == NO
        ):
            self.raise_validation_error(
                {
                    "consent_ability": (
                        "You may NOT screen this subject without their verbal consent."
                    )
                },
                INVALID_ERROR,
            )

        self.required_if(YES, field="in_care_6m", field_required="in_care_duration")
        self.duration_in_care_is_6m_or_more_or_raise()

        self.validate_hiv_section()
        self.validate_dm_section()
        self.validate_htn_section()

        self.not_applicable_if(
            MALE, field="gender", field_applicable="pregnant", inverse=False
        )

        self.validate_suitability_for_study()

    @property
    def report_datetime(self):
        return self.cleaned_data.get("report_datetime")

    def get_consent_for_period_or_raise(self):
        return get_consent_for_period_or_raise(self.report_datetime)

    def duration_in_care_is_6m_or_more_or_raise(self, fieldname: str = None) -> None:
        dt: date | datetime | None = None
        fieldname = fieldname or "in_care_duration"
        in_care_duration = self.cleaned_data.get(fieldname)
        report_datetime = self.cleaned_data.get("report_datetime")
        if report_datetime and in_care_duration:
            try:
                dt = duration_to_date(in_care_duration, report_datetime)
            except InvalidFormat as e:
                self.raise_validation_error({fieldname: f"Invalid format. {e}"}, INVALID_ERROR)
            if dt + relativedelta(months=6) > report_datetime:
                self.raise_validation_error(
                    {fieldname: "Expected at least 6m from the report date"},
                    INVALID_DURATION_IN_CARE,
                )

    def validate_hiv_section(self):
        self.applicable_if(YES, field="hiv_dx", field_applicable="hiv_dx_6m")
        self.required_if(YES, field="hiv_dx_6m", field_required="hiv_dx_ago")
        self.duration_in_care_is_6m_or_more_or_raise("hiv_dx_ago")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_unchanged_3m")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_stable")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_adherent")

    def validate_dm_section(self):
        self.applicable_if(YES, field="dm_dx", field_applicable="dm_dx_6m")
        self.required_if(YES, field="dm_dx_6m", field_required="dm_dx_ago")
        self.duration_in_care_is_6m_or_more_or_raise("dm_dx_ago")
        self.applicable_if(YES, field="dm_dx", field_applicable="dm_complications")

    def validate_htn_section(self):
        self.applicable_if(YES, field="htn_dx", field_applicable="htn_dx_6m")
        self.required_if(YES, field="htn_dx_6m", field_required="htn_dx_ago")
        self.duration_in_care_is_6m_or_more_or_raise("htn_dx_ago")
        self.applicable_if(YES, field="htn_dx", field_applicable="htn_complications")

    def validate_suitability_for_study(self):
        self.required_if(
            YES, field="unsuitable_for_study", field_required="reasons_unsuitable"
        )
        self.applicable_if(
            YES, field="unsuitable_for_study", field_applicable="unsuitable_agreed"
        )
        if self.cleaned_data.get("unsuitable_agreed") == NO:
            self.raise_validation_error(
                {
                    "unsuitable_agreed": "The study coordinator MUST agree "
                    "with your assessment. Please discuss before continuing."
                },
                INVALID_ERROR,
            )

    @property
    def patient_log_identifier(self):
        return (
            self.cleaned_data.get("patient_log_identifier")
            or self.instance.patient_log_identifier
        )

    @property
    def patient_log_model_cls(self):
        return django_apps.get_model("intecomm_screening.patientlog")
