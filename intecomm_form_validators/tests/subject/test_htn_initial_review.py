from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from django import forms
from django_mock_queries.query import MockSet
from edc_constants.constants import COMPLETE, OTHER
from edc_dx_review.constants import DIET_LIFESTYLE, DRUGS
from edc_utils import get_utcnow

from intecomm_form_validators.subject import HtnInitialReviewFormValidator as HtnBase

from ..mock_models import (
    AppointmentMockModel,
    HtnInitialReviewMockModel,
    HtnTreatmentsMockModel,
    SubjectVisitMockModel,
)
from ..test_case_mixin import TestCaseMixin


class HtnInitialReviewTests(TestCaseMixin):
    def setUp(self) -> None:
        super().setUp()
        raise_missing_clinical_review_patcher = patch(
            "intecomm_form_validators.subject.htn_initial_review_form_validator."
            "raise_if_clinical_review_does_not_exist"
        )
        self.addCleanup(raise_missing_clinical_review_patcher.stop)
        self.raise_missing_clinical_review = raise_missing_clinical_review_patcher.start()

        self.dx_date = get_utcnow() - relativedelta(days=60)
        self.rx_date = self.dx_date + relativedelta(days=3)

    @staticmethod
    def get_form_validator_cls():
        class HtnInitialReviewFormValidator(HtnBase):
            pass

        return HtnInitialReviewFormValidator

    def get_cleaned_data(self, report_datetime: datetime = None) -> dict:
        cleaned_data = dict(
            subject_visit=self.get_subject_visit(),
            report_datetime=report_datetime or get_utcnow(),
            dx_date=get_utcnow() - relativedelta(days=60),
            dx_ago="",
            managed_by=MockSet(HtnTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
            managed_by_other="",
            rx_init_date=self.rx_date,
            rx_init_ago=None,
            crf_status=COMPLETE,
            crf_status_comments="",
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cannot_enter_dx_ago_and_exact_date(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": today(),
                "dx_ago": "2y",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dx_ago", cm.exception.error_dict)
        self.assertIn(
            "'Date conflict. Do not provide a response here if diagnosis date is available.'",
            str(cm.exception.error_dict.get("dx_ago")),
        )

    def test_dx_date_only_ok(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": self.dx_date,
                "dx_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_dx_ago_only_ok(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": None,
                "dx_ago": "1y",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_dx_date_after_report_datetime_raises(self):
        htn_initial_review = HtnInitialReviewMockModel()
        report_datetime = get_utcnow() - relativedelta(days=30)
        cleaned_data = self.get_cleaned_data(report_datetime=report_datetime)
        cleaned_data.update(
            {
                "dx_date": report_datetime + relativedelta(days=1),
                "dx_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dx_date", cm.exception.error_dict)
        self.assertIn(
            "Diagnosis date must be on or before ",
            str(cm.exception.error_dict.get("dx_date")),
        )

    def test_invalid_dx_ago_raises(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": None,
                "dx_ago": "1dx",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dx_ago", cm.exception.error_dict)
        self.assertIn(
            "Expected format ",
            str(cm.exception.error_dict.get("dx_ago")),
        )

    def test_rx_init_date_required_if_managed_by_drugs(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "managed_by": MockSet(HtnTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
                "rx_init_date": None,
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Complete the treatment date", str(cm.exception))

        cleaned_data.update(
            {
                "managed_by": MockSet(HtnTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
                "rx_init_date": None,
                "rx_init_ago": "14d",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        cleaned_data.update(
            {
                "managed_by": MockSet(HtnTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
                "rx_init_date": get_utcnow() - relativedelta(days=7),
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_rx_init_date_not_required_if_managed_by_diet_lifestyle(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "managed_by": MockSet(HtnTreatmentsMockModel(name=DIET_LIFESTYLE)).filter(
                    name=DIET_LIFESTYLE
                ),
                "rx_init_date": None,
                "rx_init_ago": "1y",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertNotIn("Complete the treatment date", str(cm.exception))
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("rx_init_ago")),
        )

        cleaned_data.update(
            {
                "managed_by": MockSet(HtnTreatmentsMockModel(name=DIET_LIFESTYLE)).filter(
                    name=DIET_LIFESTYLE
                ),
                "rx_init_date": get_utcnow() - relativedelta(days=7),
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertNotIn("Complete the treatment date", str(cm.exception))
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("rx_init_date")),
        )

        cleaned_data.update(
            {
                "rx_init_date": None,
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_rx_init_date_with_managed_by_drugs_plus_another_ok(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "managed_by": MockSet(
                    HtnTreatmentsMockModel(name=DRUGS),
                    HtnTreatmentsMockModel(name=DIET_LIFESTYLE),
                ),
                "rx_init_date": None,
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Complete the treatment date.", str(cm.exception))

        cleaned_data.update(
            {
                "managed_by": MockSet(
                    HtnTreatmentsMockModel(name=DRUGS),
                    HtnTreatmentsMockModel(name=DIET_LIFESTYLE),
                    HtnTreatmentsMockModel(name=OTHER),
                ),
                "managed_by_other": "Some other management",
                "rx_init_date": None,
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Complete the treatment date.", str(cm.exception))

        cleaned_data.update(
            {
                "rx_init_date": None,
                "rx_init_ago": "14d",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        cleaned_data.update(
            {
                "rx_init_date": get_utcnow() - relativedelta(days=7),
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_rx_date_after_report_datetime_raises(self):
        htn_initial_review = HtnInitialReviewMockModel()
        report_datetime = get_utcnow() - relativedelta(days=30)
        cleaned_data = self.get_cleaned_data(report_datetime=report_datetime)
        cleaned_data.update(
            {
                "dx_date": report_datetime - relativedelta(days=7),
                "dx_ago": "",
                "rx_init_date": report_datetime + relativedelta(days=1),
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_date", cm.exception.error_dict)
        self.assertIn(
            "Cannot be after report date",
            str(cm.exception.error_dict.get("rx_init_date")),
        )

    def test_invalid_rx_init_ago_raises(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "managed_by": MockSet(HtnTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
                "rx_init_date": None,
                "rx_init_ago": "1yxxx",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_ago", cm.exception.error_dict)
        self.assertIn(
            "Expected format ",
            str(cm.exception.error_dict.get("rx_init_ago")),
        )

    def test_rx_init_without_dx_date_raises(self):
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": None,
                "dx_ago": "",
                "managed_by": MockSet(HtnTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
                "rx_init_date": get_utcnow(),
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Complete the diagnosis date", str(cm.exception))

    def test_if_managed_by_lifestyle(self):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(HtnTreatmentsMockModel(name=DIET_LIFESTYLE)).filter(
                name=DIET_LIFESTYLE
            ),
            "rx_init_ago": "blah",
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_ago", cm.exception.error_dict)

    def test_if_managed_by_other(self):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(HtnTreatmentsMockModel(name=OTHER)).filter(name=OTHER),
            "rx_init_ago": None,
            "managed_by_other": None,
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("managed_by_other", cm.exception.error_dict)

    def test_if_managed_by_drug_rx_init_after_dx(self):
        appointment = AppointmentMockModel()
        subject_visit = SubjectVisitMockModel(appointment)
        htn_initial_review = HtnInitialReviewMockModel()
        cleaned_data = {
            "subject_visit": subject_visit,
            "report_datetime": get_utcnow(),
            "dx_ago": "2y",
            "managed_by": MockSet(HtnTreatmentsMockModel(name=DRUGS)).filter(name=DRUGS),
            "rx_init_ago": "3y",
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_ago", cm.exception.error_dict)

        cleaned_data.update(rx_init_ago="2y")
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

        cleaned_data.update(rx_init_ago="1y")
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=htn_initial_review,
            model=HtnInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")
