from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from django import forms
from edc_constants.constants import OTHER, YES
from edc_dx_review.constants import DIET_LIFESTYLE, DRUGS, INSULIN
from edc_reportable import MILLIMOLES_PER_LITER

from intecomm_form_validators.subject import DmInitialReviewFormValidator as DmBase

from ..mock_models import (
    AppointmentMockModel,
    DmInitialReviewMockModel,
    SubjectVisitMockModel,
)
from ..test_case_mixin import TestCaseMixin


class InitialReviewTests(TestCaseMixin):
    @staticmethod
    def get_form_validator_cls():
        class DmInitialReviewFormValidator(DmBase):
            pass

        return DmInitialReviewFormValidator

    @patch("edc_dx_review.utils.raise_if_clinical_review_does_not_exist")
    def test_cannot_enter_ago_and_exact_date(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {"subject_visit": subject_visit, "dx_ago": "2y", "dx_date": today()}
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dx_ago", cm.exception.error_dict)

    @patch("edc_dx_review.utils.raise_if_clinical_review_does_not_exist")
    def test_if_managed_by_drugs_required_med_start_ago(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        for managed_by in [DRUGS, INSULIN]:
            with self.subTest(managed_by=managed_by):
                cleaned_data = {
                    "subject_visit": subject_visit,
                    "dx_ago": "2y",
                    "managed_by": managed_by,
                }
                form_validator = self.get_form_validator_cls()(
                    cleaned_data=cleaned_data,
                    instance=dm_initial_review,
                    model=DmInitialReviewMockModel,
                )
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("med_start_ago", cm.exception.error_dict)

    @patch("edc_dx_review.utils.raise_if_clinical_review_does_not_exist")
    def test_if_managed_by_lifestyle(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "dx_ago": "2y",
            "managed_by": DIET_LIFESTYLE,
            "med_start_ago": "blah",
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("med_start_ago", cm.exception.error_dict)

    @patch("edc_dx_review.utils.raise_if_clinical_review_does_not_exist")
    def test_if_managed_by_other(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "dx_ago": "2y",
            "managed_by": OTHER,
            "med_start_ago": None,
            "managed_by_other": None,
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("managed_by_other", cm.exception.error_dict)

    @patch("edc_dx_review.utils.raise_if_clinical_review_does_not_exist")
    def test_if_managed_by_drug_med_started_after_dx(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": datetime.today(),
            "dx_ago": "2y",
            "managed_by": DRUGS,
            "med_start_ago": "3y",
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("med_start_ago", cm.exception.error_dict)

        cleaned_data.update(med_start_ago="2y")
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

        cleaned_data.update(med_start_ago="1y")
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    @patch("edc_dx_review.utils.raise_if_clinical_review_does_not_exist")
    def test_glucose_tested_requires_date(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": datetime.today(),
            "dx_ago": "2y",
            "managed_by": DRUGS,
            "med_start_ago": "2y",
            "glucose_performed": YES,
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("glucose_date", cm.exception.error_dict)

        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": datetime.today(),
            "dx_ago": "2y",
            "managed_by": DRUGS,
            "med_start_ago": "2y",
            "fasting": YES,
            "glucose_performed": YES,
            "glucose_value": 8.3,
            "glucose_quantifier": "=",
            "glucose_units": MILLIMOLES_PER_LITER,
        }

        for rdelta in [
            relativedelta(months=0),
        ]:
            cleaned_data.update(glucose_date=datetime.today() + rdelta)
            with self.subTest(rdelta=rdelta):
                form_validator = self.get_form_validator_cls()(
                    cleaned_data=cleaned_data,
                    instance=dm_initial_review,
                    model=DmInitialReviewMockModel,
                )
                try:
                    form_validator.validate()
                except forms.ValidationError:
                    self.fail("ValidationError unexpectedly raised")

        for rdelta in [
            relativedelta(years=-1),
            relativedelta(months=-7),
            relativedelta(months=2),
            relativedelta(months=1),
        ]:
            cleaned_data.update(glucose_date=datetime.today() + rdelta)
            with self.subTest(rdelta=rdelta):
                form_validator = self.get_form_validator_cls()(
                    cleaned_data=cleaned_data,
                    instance=dm_initial_review,
                    model=DmInitialReviewMockModel,
                )
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("glucose_date", cm.exception.error_dict)
