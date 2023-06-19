from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from django import forms
from edc_constants.constants import COMPLETE, EQ, NO, NOT_APPLICABLE, YES
from edc_dx_review.constants import THIS_CLINIC
from edc_utils import get_utcnow

from intecomm_form_validators.subject import HivInitialReviewFormValidator as HivBase

from ..mock_models import HivInitialReviewMockModel
from ..test_case_mixin import TestCaseMixin


class HivInitialReviewTests(TestCaseMixin):
    def setUp(self) -> None:
        super().setUp()
        raise_missing_clinical_review_patcher = patch(
            "intecomm_form_validators.subject.hiv_initial_review_form_validator."
            "raise_if_clinical_review_does_not_exist"
        )
        self.addCleanup(raise_missing_clinical_review_patcher.stop)
        self.raise_missing_clinical_review = raise_missing_clinical_review_patcher.start()

        self.dx_date = get_utcnow() - relativedelta(days=60)
        self.rx_date = self.dx_date + relativedelta(days=3)

    @staticmethod
    def get_form_validator_cls():
        class HivInitialReviewFormValidator(HivBase):
            pass

        return HivInitialReviewFormValidator

    def get_cleaned_data(self, report_datetime: datetime = None) -> dict:
        cleaned_data = dict(
            subject_visit=self.get_subject_visit(),
            report_datetime=report_datetime or get_utcnow(),
            dx_date=get_utcnow() - relativedelta(days=60),
            dx_ago="",
            receives_care=YES,
            clinic=THIS_CLINIC,
            clinic_other="",
            rx_init=YES,
            rx_init_date=self.rx_date,
            rx_init_ago="",
            has_vl=NO,
            drawn_date=None,
            vl=None,
            vl_quantifier=NOT_APPLICABLE,
            has_cd4=NO,
            cd4=None,
            cd4_date=None,
            crf_status=COMPLETE,
            crf_status_comments="",
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cannot_enter_dx_ago_and_exact_date(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": today(),
                "dx_ago": "2y",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dx_ago", cm.exception.error_dict)
        self.assertIn(
            "'Date conflict. Do not provide a response here if diagnosis date is available.'",
            str(cm.exception.error_dict.get("dx_ago")),
        )

    def test_dx_date_only_ok(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": self.dx_date,
                "dx_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_dx_ago_only_ok(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": None,
                "dx_ago": "1y",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_dx_date_after_report_datetime_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
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
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dx_date", cm.exception.error_dict)
        self.assertIn(
            "Diagnosis date must be on or before ",
            str(cm.exception.error_dict.get("dx_date")),
        )

    def test_invalid_dx_ago_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": None,
                "dx_ago": "1dx",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dx_ago", cm.exception.error_dict)
        self.assertIn(
            "Expected format ",
            str(cm.exception.error_dict.get("dx_ago")),
        )

    def test_rx_init_requires_rx_init_date(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "rx_init": YES,
                "rx_init_date": None,
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Complete the treatment date", str(cm.exception))

        cleaned_data.update(
            {
                "rx_init": YES,
                "rx_init_date": None,
                "rx_init_ago": "14d",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        cleaned_data.update(
            {
                "rx_init": YES,
                "rx_init_date": get_utcnow() - relativedelta(days=7),
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_rx_date_after_report_datetime_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
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
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_date", cm.exception.error_dict)
        self.assertIn(
            "Cannot be after report date",
            str(cm.exception.error_dict.get("rx_init_date")),
        )

    def test_invalid_rx_init_ago_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "rx_init": YES,
                "rx_init_date": None,
                "rx_init_ago": "1yxxx",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_ago", cm.exception.error_dict)
        self.assertIn(
            "Expected format ",
            str(cm.exception.error_dict.get("rx_init_ago")),
        )

    def test_rx_init_without_dx_date_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "dx_date": None,
                "dx_ago": "",
                "rx_init": YES,
                "rx_init_date": get_utcnow(),
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Complete the diagnosis date", str(cm.exception))

    def test_rx_init_and_rx_init_after_dx(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "rx_init": YES,
                "rx_init_date": None,
                "rx_init_ago": "3y",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_ago", cm.exception.error_dict)

        cleaned_data.update(rx_init_ago="2y")
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        cleaned_data.update(rx_init_ago="1y")
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_rx_init_not_applicable_if_receives_care_no(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "receives_care": NO,
                "clinic": NOT_APPLICABLE,
                "rx_init": YES,
                "rx_init_date": None,
                "rx_init_ago": "3y",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init", cm.exception.error_dict)
        self.assertIn(
            "This field is not applicable.",
            str(cm.exception.error_dict.get("rx_init")),
        )

    def test_rx_init_applicable_if_receives_care_yes(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "receives_care": YES,
                "clinic": THIS_CLINIC,
                "rx_init": NOT_APPLICABLE,
                "rx_init_date": None,
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("rx_init")),
        )

    def test_rx_init_no_without_date_ok(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "receives_care": YES,
                "clinic": THIS_CLINIC,
                "rx_init": NO,
                "rx_init_date": None,
                "rx_init_ago": "",
                "has_vl": NOT_APPLICABLE,
                "has_cd4": NOT_APPLICABLE,
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_rx_init_yes_with_rx_init_date_ok(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "receives_care": YES,
                "clinic": THIS_CLINIC,
                "rx_init": YES,
                "rx_init_date": get_utcnow() - relativedelta(years=1),
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_rx_init_yes_with_rx_init_ago_ok(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "receives_care": YES,
                "clinic": THIS_CLINIC,
                "rx_init": YES,
                "rx_init_date": None,
                "rx_init_ago": "1y6m",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_rx_init_no_with_rx_init_date_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "rx_init": NO,
                "rx_init_date": get_utcnow() - relativedelta(years=1),
                "rx_init_ago": "",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_date", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("rx_init_date")),
        )

    def test_rx_init_no_with_rx_init_ago_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "rx_init": NO,
                "rx_init_date": None,
                "rx_init_ago": "1y",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("rx_init_ago", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("rx_init_ago")),
        )

    def test_vl_drawn_date_before_hiv_dx_date_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        report_datetime = get_utcnow()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "has_vl": YES,
                "drawn_date": report_datetime.date() - relativedelta(years=2, days=1),
                "vl": 200,
                "vl_quantifier": EQ,
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("drawn_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Cannot be before HIV diagnosis.",
            str(cm.exception.error_dict.get("drawn_date")),
        )

        cleaned_data.update({"drawn_date": report_datetime.date() - relativedelta(years=2)})
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        cleaned_data.update(
            {
                "dx_date": report_datetime.date() - relativedelta(years=1),
                "dx_ago": "",
                "drawn_date": report_datetime.date() - relativedelta(years=1, days=1),
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("drawn_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Cannot be before HIV diagnosis.",
            str(cm.exception.error_dict.get("drawn_date")),
        )

        cleaned_data.update({"drawn_date": report_datetime.date() - relativedelta(years=1)})
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cd4_date_before_hiv_dx_date_raises(self):
        hiv_initial_review = HivInitialReviewMockModel()
        cleaned_data = self.get_cleaned_data()
        report_datetime = get_utcnow()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "dx_date": None,
                "dx_ago": "2y",
                "has_cd4": YES,
                "cd4": 100,
                "cd4_date": report_datetime.date() - relativedelta(years=2, days=1),
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cd4_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Cannot be before HIV diagnosis.",
            str(cm.exception.error_dict.get("cd4_date")),
        )

        cleaned_data.update({"cd4_date": report_datetime.date() - relativedelta(years=2)})
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        cleaned_data.update(
            {
                "dx_date": report_datetime.date() - relativedelta(years=1),
                "dx_ago": "",
                "cd4_date": report_datetime.date() - relativedelta(years=1, days=1),
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cd4_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Cannot be before HIV diagnosis.",
            str(cm.exception.error_dict.get("cd4_date")),
        )

        cleaned_data.update({"cd4_date": report_datetime.date() - relativedelta(years=1)})
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=hiv_initial_review,
            model=HivInitialReviewMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
