from __future__ import annotations

from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from django import forms
from django_mock_queries.query import MockSet
from edc_constants.constants import NO, OTHER, YES
from edc_dx_review.constants import DIET_LIFESTYLE, DRUGS, INSULIN
from edc_reportable import MILLIMOLES_PER_LITER
from edc_utils import get_utcnow

from intecomm_form_validators.subject import DmInitialReviewFormValidator as DmBase

from ..mock_models import (
    AppointmentMockModel,
    DmInitialReviewMockModel,
    DmTreatmentsMockModel,
    SubjectVisitMockModel,
)
from ..test_case_mixin import TestCaseMixin


class InitialReviewTests(TestCaseMixin):
    @staticmethod
    def get_form_validator_cls():
        class DmInitialReviewFormValidator(DmBase):
            pass

        return DmInitialReviewFormValidator

    @patch(
        "intecomm_form_validators.subject.dm_initial_review_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_cannot_enter_ago_and_exact_date(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "dx_date": today(),
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dx_ago", cm.exception.error_dict)

    @patch(
        "intecomm_form_validators.subject.dm_initial_review_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_if_managed_by_drugs_required_rx_init_ago(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        for managed_by in [DRUGS, INSULIN]:
            with self.subTest(managed_by=managed_by):
                cleaned_data = {
                    "subject_visit": subject_visit,
                    "report_datetime": get_utcnow(),
                    "dx_ago": "2y",
                    "managed_by": MockSet(DmTreatmentsMockModel(name=managed_by)).filter(
                        name=managed_by
                    ),
                }
                form_validator = self.get_form_validator_cls()(
                    cleaned_data=cleaned_data,
                    instance=dm_initial_review,
                    model=DmInitialReviewMockModel,
                )
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("Complete the treatment date", str(cm.exception))

    @patch(
        "intecomm_form_validators.subject.dm_initial_review_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_if_managed_by_lifestyle(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(DmTreatmentsMockModel(name=DIET_LIFESTYLE)).filter(
                name=DIET_LIFESTYLE
            ),
            "rx_init_ago": "blah",
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_ago", cm.exception.error_dict)
        self.assertIn("This field is not required", str(cm.exception))

    @patch(
        "intecomm_form_validators.subject.dm_initial_review_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_if_managed_by_other(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(DmTreatmentsMockModel(name=OTHER)).filter(name=OTHER),
            "rx_init_ago": None,
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

    @patch(
        "intecomm_form_validators.subject.dm_initial_review_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_if_managed_by_drug_med_started_after_dx(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(DmTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
            "rx_init_ago": "3y",
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Treatment date must be on or after", str(cm.exception))

        cleaned_data.update(rx_init_ago="2y")
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

        cleaned_data.update(rx_init_ago="1y")
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    @patch(
        "intecomm_form_validators.subject.dm_initial_review_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_glucose_not_tested_glucose_fasting_not_applicable(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(DmTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
            "rx_init_ago": "2y",
            "glucose_performed": NO,
            "glucose_fasting": YES,
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("glucose_fasting", cm.exception.error_dict)
        self.assertIn("not applicable", str(cm.exception))

    @patch(
        "intecomm_form_validators.subject.dm_initial_review_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_glucose_tested_requires_fasting_duration(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(DmTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
            "rx_init_ago": "2y",
            "glucose_performed": YES,
            "glucose_fasting": YES,
            "glucose_fasting_duration_str": None,
            "glucose_date": None,
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=dm_initial_review,
            model=DmInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("glucose_fasting_duration_str", cm.exception.error_dict)

    @patch(
        "intecomm_form_validators.subject.dm_initial_review_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_glucose_tested_requires_date(self, mock_func):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        dm_initial_review = DmInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(DmTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
            "rx_init_ago": "2y",
            "glucose_performed": YES,
            "glucose_fasting": YES,
            "glucose_fasting_duration_str": "8h",
            "glucose_date": None,
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
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(DmTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
            "rx_init_ago": "2y",
            "glucose_fasting": YES,
            "glucose_fasting_duration_str": "8h",
            "glucose_performed": YES,
            "glucose_value": 8.3,
            "glucose_quantifier": "=",
            "glucose_units": MILLIMOLES_PER_LITER,
        }

        for rdelta in [
            relativedelta(months=0),
        ]:
            cleaned_data.update(glucose_date=get_utcnow() + rdelta)
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
            relativedelta(years=-2),
            relativedelta(months=-7),
            relativedelta(months=2),
            relativedelta(months=3),
        ]:
            cleaned_data.update(glucose_date=get_utcnow() + rdelta)
            with self.subTest(rdelta=rdelta):
                form_validator = self.get_form_validator_cls()(
                    cleaned_data=cleaned_data,
                    instance=dm_initial_review,
                    model=DmInitialReviewMockModel,
                )
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("glucose_date", cm.exception.error_dict)
