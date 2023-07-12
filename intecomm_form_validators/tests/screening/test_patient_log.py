from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django import forms
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import FEMALE, MALE, NO, OTHER, YES
from edc_utils import get_utcnow

from intecomm_form_validators.screening import PatientLogFormValidator as Base

from ..mock_models import PatientGroupMockModel, PatientLogMockModel
from ..test_case_mixin import TestCaseMixin


class PatientLogTests(TestCaseMixin):
    @staticmethod
    def get_form_validator_cls(subject_screening=None):
        class PatientLogFormValidator(Base):
            @property
            def subject_screening(self):
                return subject_screening

        return PatientLogFormValidator

    def test_raises_if_last_appt_date_is_future(self):
        patient_group = PatientGroupMockModel(name="PARKSIDE", randomized=None)
        patient_log = PatientLogMockModel()
        cleaned_data = dict(
            name="ERIK",
            patient_group=patient_group,
            report_datetime=get_utcnow(),
            last_appt_date=(get_utcnow() + relativedelta(days=30)).date(),
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("last_appt_date", cm.exception.error_dict)
        cleaned_data.update(last_appt_date=(get_utcnow() - relativedelta(days=30)).date())
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_raises_if_next_appt_date_is_past(self):
        patient_group = PatientGroupMockModel(name="PARKSIDE", randomized=None)
        patient_log = PatientLogMockModel()
        cleaned_data = dict(
            name="ERIK",
            patient_group=patient_group,
            report_datetime=get_utcnow(),
            next_appt_date=(get_utcnow() - relativedelta(days=30)).date(),
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("next_appt_date", cm.exception.error_dict)

        cleaned_data.update(next_appt_date=(get_utcnow() + relativedelta(days=30)).date())
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_patient_log_matches_screening(self):
        patient_log = PatientLogMockModel(name="ERIK", willing_to_screen=YES)
        patient_group = PatientGroupMockModel(
            name="PARKSIDE", patients=MockSet(patient_log), randomized=None
        )
        data = [
            ("gender", "gender", MALE, MALE, "Gender", False),
            ("gender", "gender", FEMALE, MALE, "Gender", True),
            ("initials", "initials", "XX", "XX", "Initials", False),
            ("initials", "initials", "XX", "YY", "Initials", True),
            (
                "hospital_identifier",
                "hospital_identifier",
                "12345",
                "12345",
                "Identifier",
                False,
            ),
            (
                "hospital_identifier",
                "hospital_identifier",
                "12345",
                "54321",
                "Identifier",
                True,
            ),
            (
                "site",
                "site",
                MockModel(mock_name="Site", id=110),
                MockModel(mock_name="Site", id=110),
                "Site",
                False,
            ),
            (
                "site",
                "site",
                MockModel(mock_name="Site", id=110),
                MockModel(mock_name="Site", id=120),
                "Site",
                True,
            ),
        ]
        for values in data:
            screening_fld, log_fld, screening_value, log_value, word, should_raise = values
            with self.subTest(
                screening_fld=screening_fld,
                log_fld=log_fld,
                screening_value=screening_value,
                log_value=log_value,
                word=word,
                should_raise=should_raise,
            ):
                subject_screening = MockModel(
                    mock_name="SubjectScreening", **{screening_fld: screening_value}
                )
                cleaned_data = dict(
                    name="ERIK",
                    willing_to_screen=YES,
                    report_datetime=get_utcnow(),
                    patient_group=patient_group,
                    **{log_fld: log_value},
                )
                form_validator = self.get_form_validator_cls(subject_screening)(
                    cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
                )
                if should_raise:
                    with self.assertRaises(forms.ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(word, str(cm.exception.error_dict.get("__all__")))
                else:
                    form_validator.validate()

    @patch(
        "intecomm_form_validators.screening.patient_log_form_validator"
        ".get_subject_screening_model_cls"
    )
    def test_get_subject_screening(self, mock_subject_screening_model_cls):
        form_validator = Base(
            cleaned_data={},
            instance=MockModel(mock_name="PatientLog", name="BUBBA", screening_identifier="B"),
        )
        self.assertIsNotNone(form_validator.subject_screening)

    def test_age_in_years_lt_18_raises(self):
        for age in [17, 15, 1, 0]:
            with self.subTest(age=age):
                patient_log = PatientLogMockModel()
                form_validator = self.get_form_validator_cls()(
                    cleaned_data={"age_in_years": age},
                    instance=patient_log,
                    model=PatientLogMockModel,
                )

                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("age_in_years", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Patient must be 18 years or older",
                    str(cm.exception.error_dict.get("age_in_years")),
                )

    def test_age_in_years_gte_18_ok(self):
        for age in [18, 19, 29, 99]:
            with self.subTest(age=age):
                patient_log = PatientLogMockModel()
                form_validator = self.get_form_validator_cls()(
                    cleaned_data={"age_in_years": age},
                    instance=patient_log,
                    model=PatientLogMockModel,
                )
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_screening_refusal_reason_other_requires_other_field(self):
        patient_log = PatientLogMockModel()
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "willing_to_screen": NO,
                "screening_refusal_reason": OTHER,
                "screening_refusal_reason_other": "",
            },
            instance=patient_log,
            model=PatientLogMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("screening_refusal_reason_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("screening_refusal_reason_other")),
        )

        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "willing_to_screen": NO,
                "screening_refusal_reason": OTHER,
                "screening_refusal_reason_other": "Some other reason",
            },
            instance=patient_log,
            model=PatientLogMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_screening_refusal_reason_not_other_does_not_require_other_field(self):
        for answ in [
            "dont_have_time",
            "must_consult_spouse",
            "dont_want_to_join",
            "need_to_think_about_it",
        ]:
            with self.subTest(answ=answ):
                patient_log = PatientLogMockModel()
                form_validator = self.get_form_validator_cls()(
                    cleaned_data={
                        "willing_to_screen": NO,
                        "screening_refusal_reason": answ,
                        "screening_refusal_reason_other": "Some other reason",
                    },
                    instance=patient_log,
                    model=PatientLogMockModel,
                )
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("screening_refusal_reason_other", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("screening_refusal_reason_other")),
                )

                form_validator = self.get_form_validator_cls()(
                    cleaned_data={
                        "willing_to_screen": NO,
                        "screening_refusal_reason": answ,
                        "screening_refusal_reason_other": "",
                    },
                    instance=patient_log,
                    model=PatientLogMockModel,
                )
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")
