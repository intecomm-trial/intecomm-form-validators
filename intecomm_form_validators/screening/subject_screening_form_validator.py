from edc_constants.constants import DM, HIV, HTN, MALE, NO, YES
from edc_form_validators import INVALID_ERROR, FormValidator
from edc_screening.form_validator_mixins import SubjectScreeningFormValidatorMixin


class SubjectScreeningFormValidator(SubjectScreeningFormValidatorMixin, FormValidator):
    def clean(self):
        self.get_consent_for_period_or_raise()
        self.validate_gender_against_patient_log()
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

        self.validate_hiv_section()
        self.validate_dm_section()
        self.validate_htn_section()

        self.not_applicable_if(
            MALE, field="gender", field_applicable="pregnant", inverse=False
        )

        self.required_if(
            YES, field="unsuitable_for_study", field_required="reasons_unsuitable"
        )

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

    def validate_hiv_section(self):
        self.validate_condition(HIV, "hiv_dx")
        self.applicable_if(YES, field="hiv_dx", field_applicable="hiv_dx_6m")
        self.required_if(YES, field="hiv_dx_6m", field_required="hiv_dx_ago")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_unchanged_3m")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_stable")
        self.applicable_if(YES, field="hiv_dx", field_applicable="art_adherent")

    def validate_dm_section(self):
        self.validate_condition(DM, "dm_dx")
        self.applicable_if(YES, field="dm_dx", field_applicable="dm_dx_6m")
        self.required_if(YES, field="dm_dx_6m", field_required="dm_dx_ago")
        self.applicable_if(YES, field="dm_dx", field_applicable="dm_complications")

    def validate_htn_section(self):
        self.validate_condition(HTN, "htn_dx")
        self.applicable_if(YES, field="htn_dx", field_applicable="htn_dx_6m")
        self.required_if(YES, field="htn_dx_6m", field_required="htn_dx_ago")
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

    @property
    def patient_log(self):
        if patient_log := self.cleaned_data.get("patient_log"):
            return patient_log
        return self.instance.patient_log
