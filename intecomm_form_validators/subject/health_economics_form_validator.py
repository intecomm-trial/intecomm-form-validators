from django import forms
from django.apps import apps as django_apps
from django.utils.translation import gettext_lazy as _
from edc_constants.constants import (
    FREE_OF_CHARGE,
    INSURANCE,
    OTHER,
    OWN_CASH,
    PATIENT_CLUB,
    RELATIVE,
    YES,
)
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx.form_validators import DiagnosisFormValidatorMixin
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class HealthEconomicsFormValidator(
    DiagnosisFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    drug_pay_sources_model = "intecomm_lists.DrugPaySources"

    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))

        self.clean_education()

        self.clean_recv_drugs_by_duration("month")

        self.clean_recv_drugs_by_duration("today")

        self.required_if(YES, field="health_insurance", field_required="health_insurance_cost")

        self.required_if(YES, field="patient_club", field_required="patient_club_cost")

    @property
    def drug_pay_sources_model_cls(self):
        return django_apps.get_model(self.drug_pay_sources_model)

    def clean_education(self):
        cond = (
            self.cleaned_data.get("education_in_years") is not None
            and self.cleaned_data.get("education_in_years") > 0
        )

        if cond and self.cleaned_data.get("education_in_years") > self.age_in_years:
            msg = _(
                "Cannot exceed subject's age. Got subject is %(age_in_years)s years old."
            ) % {"age_in_years": self.age_in_years}
            raise forms.ValidationError({"education_in_years": msg})

        self.required_if_true(cond, field_required="education_certificate")

        self.applicable_if_true(cond, field_applicable="primary_school")
        self.required_if(
            YES,
            field="primary_school",
            field_required="primary_school_in_years",
            field_required_evaluate_as_int=True,
        )
        self.applicable_if_true(cond, field_applicable="secondary_school")
        self.required_if(
            YES,
            field="secondary_school",
            field_required="secondary_school_in_years",
            field_required_evaluate_as_int=True,
        )
        self.applicable_if_true(cond, field_applicable="higher_education")
        self.required_if(
            YES,
            field="higher_education",
            field_required="higher_education_in_years",
            field_required_evaluate_as_int=True,
        )

    def clean_recv_drugs_by_duration(self, duration):
        conditions = [
            ("dm", "diabetes"),
            ("htn", "hypertension"),
            ("hiv", "HIV"),
            ("other", None),
        ]
        diagnoses = self.get_diagnoses()
        for cond, label in conditions:
            if cond == "other":
                self.applicable_if(
                    YES,
                    field=f"received_rx_{duration}",
                    field_applicable=f"rx_{cond}_{duration}",
                )
            else:
                if self.cleaned_data.get(f"received_rx_{duration}") == YES:
                    self.applicable_if_diagnosed(
                        diagnoses=diagnoses,
                        prefix=f"{cond}_dx",
                        field_applicable=f"rx_{cond}_{duration}",
                        label=label,
                    )
                else:
                    self.applicable_if(
                        YES,
                        field=f"received_rx_{duration}",
                        field_applicable=f"rx_{cond}_{duration}",
                    )

            self.m2m_required_if(
                response=YES,
                field=f"rx_{cond}_{duration}",
                m2m_field=f"rx_{cond}_paid_{duration}",
            )
            self.m2m_single_selection_if(
                FREE_OF_CHARGE, m2m_field=f"rx_{cond}_paid_{duration}"
            )
            self.m2m_other_specify(
                OTHER,
                m2m_field=f"rx_{cond}_paid_{duration}",
                field_other=f"rx_{cond}_paid_{duration}_other",
            )
            self.m2m_other_specify(
                *[
                    obj.name
                    for obj in (
                        # NOTE: Must align with choices in intecomm_lists.models.DrugPaySources
                        (OWN_CASH, INSURANCE, PATIENT_CLUB, RELATIVE, FREE_OF_CHARGE, OTHER)
                    )
                    if obj.name != FREE_OF_CHARGE
                ],
                m2m_field=f"rx_{cond}_paid_{duration}",
                field_other=f"rx_{cond}_cost_{duration}",
                field_other_evaluate_as_int=True,
            )
