from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from django import forms
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import (
    COMPLETE,
    DONT_KNOW,
    NO,
    NONE,
    NOT_APPLICABLE,
    OTHER,
    YES,
)
from edc_utils import get_utcnow

from ...subject.health_economics import HealthEconomicsHouseholdHeadFormValidator
from ..mock_models import HealthEconomicsHouseholdHeadMockModel
from ..test_case_mixin import TestCaseMixin


class HeTests(TestCaseMixin):
    def get_cleaned_data(self, report_datetime: datetime = None) -> dict:
        cleaned_data = dict(
            subject_visit=self.get_subject_visit(
                visit_code="1000", visit_code_sequence=0, timepoint=0, schedule_name="schedule"
            ),
            report_datetime=report_datetime or get_utcnow(),
            crf_status=COMPLETE,
            crf_status_comments="",
        )
        return cleaned_data

    @patch(
        "intecomm_form_validators.subject.health_economics.household_head_form_validator"
        ".raise_if_clinical_review_does_not_exist"
    )
    def test_household_head(self, mock_func):
        mock_func.return_value = True
        household_head = HealthEconomicsHouseholdHeadMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(hoh=NO, relationship_to_hoh=NOT_APPLICABLE)
        form_validator = HealthEconomicsHouseholdHeadFormValidator(
            cleaned_data=cleaned_data,
            instance=household_head,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("relationship_to_hoh", str(cm.exception))

        cleaned_data.update(hoh=YES, relationship_to_hoh=NOT_APPLICABLE)
        cleaned_data.update(hoh_religion=OTHER, hoh_religion_other=None)
        form_validator = HealthEconomicsHouseholdHeadFormValidator(
            cleaned_data=cleaned_data,
            instance=household_head,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hoh_religion_other", cm.exception.error_dict)

        cleaned_data.update(hoh_religion=OTHER, hoh_religion_other="blah")
        cleaned_data.update(hoh_ethnicity=OTHER, hoh_ethnicity_other=None)
        form_validator = HealthEconomicsHouseholdHeadFormValidator(
            cleaned_data=cleaned_data,
            instance=household_head,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hoh_ethnicity_other", cm.exception.error_dict)

        cleaned_data.update(hoh_ethnicity=OTHER, hoh_ethnicity_other="blah")
        cleaned_data.update(hoh_education=OTHER, hoh_education_other=None)
        form_validator = HealthEconomicsHouseholdHeadFormValidator(
            cleaned_data=cleaned_data,
            instance=household_head,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hoh_education_other", cm.exception.error_dict)

        cleaned_data.update(hoh_education=OTHER, hoh_education_other="blah")
        cleaned_data.update(hoh_marital_status=OTHER, hoh_marital_status_other=None)
        form_validator = HealthEconomicsHouseholdHeadFormValidator(
            cleaned_data=cleaned_data,
            instance=household_head,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hoh_marital_status_other", cm.exception.error_dict)

        cleaned_data.update(hoh_marital_status=OTHER, hoh_marital_status_other="blah")
        cleaned_data.update(
            hoh_insurance=MockSet(MockModel(mock_name="InsuranceTypes", name=OTHER))
        )
        form_validator = HealthEconomicsHouseholdHeadFormValidator(
            cleaned_data=cleaned_data,
            instance=household_head,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hoh_insurance_other", cm.exception.error_dict)

        cleaned_data.update(
            hoh_insurance=MockSet(
                MockModel(mock_name="InsuranceTypes", name=DONT_KNOW),
                MockModel(mock_name="InsuranceTypes", name=OTHER),
            )
        )
        form_validator = HealthEconomicsHouseholdHeadFormValidator(
            cleaned_data=cleaned_data,
            instance=household_head,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Invalid combination", str(cm.exception))

        cleaned_data.update(
            hoh_insurance=MockSet(
                MockModel(mock_name="InsuranceTypes", name=NONE),
                MockModel(mock_name="InsuranceTypes", name=OTHER),
            )
        )
        form_validator = HealthEconomicsHouseholdHeadFormValidator(
            cleaned_data=cleaned_data,
            instance=household_head,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Invalid combination", str(cm.exception))
