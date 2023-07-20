from __future__ import annotations

from unittest.mock import patch

from django import forms
from django.test import tag
from django_mock_queries.query import MockSet
from edc_constants.constants import COMPLETE, FEMALE, NO, NOT_APPLICABLE, OTHER, YES
from edc_he.constants import WIFE_HUSBAND
from edc_utils import get_utcnow

from intecomm_form_validators.subject import (
    HealthEconomicsHouseholdHeadFormValidator as Base,
)

from ..mock_models import HealthEconomicsHouseholdHeadMockModel, InsuranceTypesMockModel
from ..test_case_mixin import TestCaseMixin


class HealthEconomicsHouseholdHeadTests(TestCaseMixin):
    def setUp(self) -> None:
        super().setUp()
        raise_missing_clinical_review_patcher = patch(
            "intecomm_form_validators.subject.health_economics.household_head_form_validator."
            "raise_if_clinical_review_does_not_exist"
        )
        self.addCleanup(raise_missing_clinical_review_patcher.stop)
        self.raise_missing_clinical_review = raise_missing_clinical_review_patcher.start()

    @staticmethod
    def get_form_validator_cls():
        class HealthEconomicsHouseholdHeadFormValidator(Base):
            pass

        return HealthEconomicsHouseholdHeadFormValidator

    def get_cleaned_data(self, **kwargs) -> dict:
        cleaned_data = dict(
            subject_visit=self.get_subject_visit(),
            report_datetime=get_utcnow(),
            hh_count=5,
            hh_minors_count=1,
            hoh=YES,
            relationship_to_hoh=NOT_APPLICABLE,
            relationship_to_hoh_other=None,
            hoh_gender=FEMALE,
            hoh_age=25,
            hoh_religion=OTHER,
            hoh_religion_other="blah",
            hoh_ethnicity=OTHER,
            hoh_ethnicity_other="blah",
            hoh_education="",
            hoh_education_other=None,
            hoh_employment="",
            hoh_employment_type="",
            hoh_employment_type_other=None,
            hoh_marital_status=OTHER,
            hoh_marital_status_other="blah",
            hoh_insurance=MockSet(InsuranceTypesMockModel(name="NONE")),
            hoh_insurance_other=None,
            crf_status=COMPLETE,
            crf_status_comments="",
        )
        cleaned_data.update(**kwargs)
        return cleaned_data

    @tag("1")
    def test_cleaned_data_ok(self):
        instance = HealthEconomicsHouseholdHeadMockModel()
        cleaned_data = self.get_cleaned_data()
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=instance,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    @tag("1")
    def test_relationship_to_hoh_applicable_if_not_hoh(self):
        instance = HealthEconomicsHouseholdHeadMockModel()
        opts = dict(
            instance=instance,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        cleaned_data = self.get_cleaned_data(hoh=YES, relationship_to_hoh=None)
        form_validator = self.get_form_validator_cls()(cleaned_data=cleaned_data, **opts)
        with self.assertRaises(forms.ValidationError):
            form_validator.validate()
        self.assertIn("relationship_to_hoh", form_validator._errors)
        self.assertIn(
            "This field is not applicable",
            str(form_validator._errors.get("relationship_to_hoh")),
        )

        cleaned_data = self.get_cleaned_data(hoh=YES, relationship_to_hoh=NOT_APPLICABLE)
        form_validator = self.get_form_validator_cls()(cleaned_data=cleaned_data, **opts)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        cleaned_data.update(hoh=NO, relationship_to_hoh=None)
        form_validator = self.get_form_validator_cls()(cleaned_data=cleaned_data, **opts)
        with self.assertRaises(forms.ValidationError):
            form_validator.validate()
        self.assertIn("relationship_to_hoh", form_validator._errors)
        self.assertIn(
            "This field is applicable", str(form_validator._errors.get("relationship_to_hoh"))
        )

        cleaned_data.update(hoh=NO, relationship_to_hoh=NOT_APPLICABLE)
        form_validator = self.get_form_validator_cls()(cleaned_data=cleaned_data, **opts)
        with self.assertRaises(forms.ValidationError):
            form_validator.validate()
        self.assertIn("relationship_to_hoh", form_validator._errors)
        self.assertIn(
            "This field is applicable", str(form_validator._errors.get("relationship_to_hoh"))
        )

        cleaned_data.update(hoh=NO, relationship_to_hoh=WIFE_HUSBAND)
        form_validator = self.get_form_validator_cls()(cleaned_data=cleaned_data, **opts)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        cleaned_data.update(hoh=NO, relationship_to_hoh=OTHER)
        form_validator = self.get_form_validator_cls()(cleaned_data=cleaned_data, **opts)
        with self.assertRaises(forms.ValidationError):
            form_validator.validate()
        self.assertIn("relationship_to_hoh_other", form_validator._errors)

        cleaned_data.update(
            hoh=NO, relationship_to_hoh=OTHER, relationship_to_hoh_other="blah"
        )
        form_validator = self.get_form_validator_cls()(cleaned_data=cleaned_data, **opts)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    @tag("1")
    def test_hoh_religion_other(self):
        instance = HealthEconomicsHouseholdHeadMockModel()
        opts = dict(
            instance=instance,
            model=HealthEconomicsHouseholdHeadMockModel,
        )
        cleaned_data = self.get_cleaned_data(
            hoh=YES,
            relationship_to_hoh=NOT_APPLICABLE,
            hoh_religion=OTHER,
            hoh_religion_other=None,
        )
        form_validator = self.get_form_validator_cls()(cleaned_data=cleaned_data, **opts)
        with self.assertRaises(forms.ValidationError):
            form_validator.validate()
        self.assertIn("hoh_religion_other", form_validator._errors)
        self.assertIn(
            "This field is required",
            str(form_validator._errors.get("hoh_religion_other")),
        )
