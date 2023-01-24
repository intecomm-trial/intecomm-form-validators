from unittest.mock import patch

from django.core.exceptions import ValidationError
from edc_constants.constants import COMPLETE, YES
from edc_form_validators.tests.mixins import FormValidatorTestMixin

from intecomm_form_validators.subject import IndicatorsFormValidator as Base

from ..mock_models import IndicatorsMockModel
from ..test_case_mixin import TestCaseMixin


class IndicatorsFormValidator(FormValidatorTestMixin, Base):
    pass


class IndicatorsTests(TestCaseMixin):
    def setUp(self) -> None:
        super().setUp()
        is_baseline_patcher = patch(
            "intecomm_form_validators.subject.indicators_form_validator.is_baseline"
        )
        self.addCleanup(is_baseline_patcher.stop)
        self.mock_is_baseline = is_baseline_patcher.start()

        raise_missing_clinical_review_patcher = patch(
            "edc_dx_review.utils.raise_if_clinical_review_does_not_exist"
        )
        self.addCleanup(raise_missing_clinical_review_patcher.stop)
        self.raise_missing_clinical_review = raise_missing_clinical_review_patcher.start()

    def get_cleaned_data(self) -> dict:
        cleaned_data = dict(
            weight=60.0,
            height=182.88,
            waist=None,
            hip=None,
            r1_taken=YES,
            r1_reason_not_taken="",
            sys_blood_pressure_r1=120,
            dia_blood_pressure_r1=80,
            r2_taken=YES,
            r2_reason_not_taken="",
            sys_blood_pressure_r2=119,
            dia_blood_pressure_r2=79,
            crf_status=COMPLETE,
            crf_status_comments="",
        )
        return cleaned_data

    def test_cleaned_data_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data()
        form_validator = IndicatorsFormValidator(
            cleaned_data=cleaned_data, model=IndicatorsMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cleaned_data_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data()
        form_validator = IndicatorsFormValidator(
            cleaned_data=cleaned_data, model=IndicatorsMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missing_weight_at_baseline_raises(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"weight": None})
        form_validator = IndicatorsFormValidator(
            cleaned_data=cleaned_data, model=IndicatorsMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("weight", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("weight")),
        )

    def test_missing_weight_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"weight": None})
        form_validator = IndicatorsFormValidator(
            cleaned_data=cleaned_data, model=IndicatorsMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missing_height_at_baseline_raises(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"height": None})
        form_validator = IndicatorsFormValidator(
            cleaned_data=cleaned_data, model=IndicatorsMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("height", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("height")),
        )

    def test_missing_height_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"height": None})
        form_validator = IndicatorsFormValidator(
            cleaned_data=cleaned_data, model=IndicatorsMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
