from unittest.mock import patch

from django.core.exceptions import ValidationError
from edc_constants.constants import COMPLETE, NO, YES
from edc_form_validators.tests.mixins import FormValidatorTestMixin

from intecomm_form_validators.subject import VitalsFormValidator as Base

from ..mock_models import VitalsMockModel
from ..test_case_mixin import TestCaseMixin


class VitalsFormValidator(FormValidatorTestMixin, Base):
    pass


class VitalsFormValidationTests(TestCaseMixin):
    def setUp(self) -> None:
        super().setUp()
        is_baseline_patcher = patch(
            "intecomm_form_validators.subject.vitals_form_validator.is_baseline"
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
            sys_blood_pressure_one=120,
            dia_blood_pressure_one=80,
            sys_blood_pressure_two=119,
            dia_blood_pressure_two=79,
            severe_htn=NO,
            heart_rate=58,
            respiratory_rate=None,
            temperature=37.5,
            crf_status=COMPLETE,
            crf_status_comments="",
        )
        return cleaned_data

    def test_cleaned_data_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data()
        form_validator = VitalsFormValidator(cleaned_data=cleaned_data, model=VitalsMockModel)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cleaned_data_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data()
        form_validator = VitalsFormValidator(cleaned_data=cleaned_data, model=VitalsMockModel)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missing_weight_at_baseline_raises(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"weight": None})
        form_validator = VitalsFormValidator(cleaned_data=cleaned_data, model=VitalsMockModel)
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
        form_validator = VitalsFormValidator(cleaned_data=cleaned_data, model=VitalsMockModel)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missing_height_at_baseline_raises(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"height": None})
        form_validator = VitalsFormValidator(cleaned_data=cleaned_data, model=VitalsMockModel)
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
        form_validator = VitalsFormValidator(cleaned_data=cleaned_data, model=VitalsMockModel)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_sys_lt_dia_blood_pressure_raises(self):
        self.mock_is_baseline.return_value = True
        for reading in ["one", "two"]:
            for sys_bp, dia_bp in [(80, 120), (90, 100), (99, 100)]:
                with self.subTest(reading=reading, sys_bp=sys_bp, dia_bp=dia_bp):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            f"sys_blood_pressure_{reading}": sys_bp,
                            f"dia_blood_pressure_{reading}": dia_bp,
                            "severe_htn": NO,
                        }
                    )
                    form_validator = VitalsFormValidator(
                        cleaned_data=cleaned_data, model=VitalsMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(f"dia_blood_pressure_{reading}", cm.exception.error_dict)
                    self.assertIn(
                        "Invalid. Diastolic must be less than systolic.",
                        str(cm.exception.error_dict.get(f"dia_blood_pressure_{reading}")),
                    )

    def test_sys_blood_pressure_indicates_severe_htn(self):
        for reading_one, reading_two in [
            (179, 181),
            (181, 179),
            (180, 180),
            (200, 160),
            (160, 200),
            (300, 120),
            (120, 300),
        ]:
            with self.subTest(reading_one=reading_one, reading_two=reading_two):
                self.mock_is_baseline.return_value = True
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "sys_blood_pressure_one": reading_one,
                        "sys_blood_pressure_two": reading_two,
                        "severe_htn": NO,
                    }
                )
                form_validator = VitalsFormValidator(
                    cleaned_data=cleaned_data, model=VitalsMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("severe_htn", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Patient has severe hypertension",
                    str(cm.exception.error_dict.get("severe_htn")),
                )

                cleaned_data.update({"severe_htn": YES})
                form_validator = VitalsFormValidator(
                    cleaned_data=cleaned_data, model=VitalsMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_dia_blood_pressure_indicates_severe_htn(self):
        for reading_one, reading_two in [
            (109, 111),
            (111, 109),
            (110, 110),
            (150, 81),
            (81, 150),
            (179, 81),
            (81, 179),
        ]:
            with self.subTest(reading_one=reading_one, reading_two=reading_two):
                self.mock_is_baseline.return_value = True
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "sys_blood_pressure_one": 180,
                        "dia_blood_pressure_one": reading_one,
                        "sys_blood_pressure_two": 180,
                        "dia_blood_pressure_two": reading_two,
                        "severe_htn": NO,
                    }
                )
                form_validator = VitalsFormValidator(
                    cleaned_data=cleaned_data, model=VitalsMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("severe_htn", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Patient has severe hypertension",
                    str(cm.exception.error_dict.get("severe_htn")),
                )

                cleaned_data.update({"severe_htn": YES})
                form_validator = VitalsFormValidator(
                    cleaned_data=cleaned_data, model=VitalsMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")
