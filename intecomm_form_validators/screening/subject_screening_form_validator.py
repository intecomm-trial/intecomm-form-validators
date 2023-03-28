from dateutil.relativedelta import relativedelta
from django.utils.html import format_html
from edc_constants.constants import DM, HIV, HTN, MALE, NO, YES
from edc_form_validators import INVALID_ERROR, FormValidator
from edc_model import InvalidFormat, duration_to_date
from edc_screening.form_validator_mixins import SubjectScreeningFormValidatorMixin

INVALID_DURATION_IN_CARE = "invalid_duration_in_care"


class SubjectScreeningFormValidator(SubjectScreeningFormValidatorMixin, FormValidator):
    def clean(self):
        self.validate_stable_in_care_on_patient_log()
        self.get_consent_for_period_or_raise()
        self.validate_gender_against_patient_log()
        self.validate_age_in_years_against_patient_log()

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

    def validate_stable_in_care_on_patient_log(self):
        if self.patient_log.stable != YES:
            link = (
                f'<a href="{self.patient_log.get_changelist_url()}?'
                f'q={str(self.patient_log.id)}">{self.patient_log}</a>'
            )
            errmsg = format_html(
                "Invalid. Patient is not known to be stable and in-care. "
                f"See patient log for {link}."
            )
            self.raise_validation_error(errmsg, error_code=INVALID_ERROR)

        pass

    def validate_gender_against_patient_log(self):
        if self.cleaned_data.get("gender") != self.patient_log.gender:
            self.raise_validation_error(
                {
                    "gender": (
                        f"Invalid. Expected {self.patient_log.get_gender_display()}. "
                        "See Patient Log."
                    )
                },
                INVALID_ERROR,
            )

        pass

    def validate_age_in_years_against_patient_log(self):
        if self.cleaned_data.get("age_in_years") != self.patient_log.age_in_years:
            self.raise_validation_error(
                {
                    "age_in_years": (
                        f"Invalid. Expected {self.patient_log.age_in_years}. "
                        "See Patient Log."
                    )
                },
                INVALID_ERROR,
            )

        pass

    def duration_in_care_is_6m_or_more_or_raise(self, fieldname: str = None) -> None:
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
        self.validate_condition(HIV, "hiv_dx")
        self.applicable_if(YES, field="hiv_dx", field_applicable="hiv_dx_6m")
        self.required_if(YES, field="hiv_dx_6m", field_required="hiv_dx_ago")
        self.duration_in_care_is_6m_or_more_or_raise("hiv_dx_ago")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_unchanged_3m")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_stable")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_adherent")

    def validate_dm_section(self):
        self.validate_condition(DM, "dm_dx")
        self.applicable_if(YES, field="dm_dx", field_applicable="dm_dx_6m")
        self.required_if(YES, field="dm_dx_6m", field_required="dm_dx_ago")
        self.duration_in_care_is_6m_or_more_or_raise("dm_dx_ago")
        self.applicable_if(YES, field="dm_dx", field_applicable="dm_complications")

    def validate_htn_section(self):
        self.validate_condition(HTN, "htn_dx")
        self.applicable_if(YES, field="htn_dx", field_applicable="htn_dx_6m")
        self.required_if(YES, field="htn_dx_6m", field_required="htn_dx_ago")
        self.duration_in_care_is_6m_or_more_or_raise("htn_dx_ago")
        self.applicable_if(YES, field="htn_dx", field_applicable="htn_complications")

    def validate_condition(self, name, field):
        conditions = self.patient_log.conditions
        if not self.patient_log.conditions:
            self.raise_validation_error(
                "No conditions (HIV/DM/HTN) have been indicated for this patient. See "
                "the Patient Log",
                INVALID_ERROR,
            )
        else:
            if not conditions.filter(name=name) and self.cleaned_data.get(field) == YES:
                self.raise_validation_error(
                    {
                        field: (
                            f"Invalid. {name.upper()} was not indicated "
                            "as a condition on the Patient Log"
                        ),
                    },
                    INVALID_ERROR,
                )
            elif conditions.filter(name=name) and self.cleaned_data.get(field) == NO:
                self.raise_validation_error(
                    {
                        field: (
                            f"Invalid. {name.upper()} was indicated "
                            "as a condition on the Patient Log"
                        ),
                    },
                    INVALID_ERROR,
                )

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
    def patient_log(self):
        if patient_log := self.cleaned_data.get("patient_log"):
            return patient_log
        return self.instance.patient_log
