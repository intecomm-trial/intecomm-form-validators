from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django import forms
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import COMPLETE, FEMALE, MALE
from edc_utils import get_utcnow

from intecomm_form_validators.constants import RECRUITING
from intecomm_form_validators.screening import PatientLogFormValidator as Base


class SubjectScreeningMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "SubjectScreening"
        super().__init__(*args, **kwargs)


class PatientGroupMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "PatientGroup"
        super().__init__(*args, **kwargs)


class PatientLogMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "PatientLog"
        super().__init__(*args, **kwargs)


class PatientLogTests(TestCase):
    @staticmethod
    def get_form_validator_cls(subject_screening=None):
        class PatientLogFormValidator(Base):
            @property
            def subject_screening(self):
                return subject_screening

        return PatientLogFormValidator

    def test_raises_if_randomized(self):
        patient_group = PatientGroupMockModel(randomized=True)
        patient_log = PatientLogMockModel(patient_group=patient_group)
        form_validator = self.get_form_validator_cls()(
            cleaned_data={}, instance=patient_log, model=PatientLogMockModel
        )
        self.assertRaises(forms.ValidationError, form_validator.validate)

    def test_raises_if_last_routine_appt_date_is_future(self):
        patient_group = PatientGroupMockModel(name="PARKSIDE", randomized=None)
        patient_log = PatientLogMockModel()
        cleaned_data = dict(
            name="ERIK",
            patient_group=patient_group,
            report_datetime=get_utcnow(),
            last_routine_appt_date=(get_utcnow() + relativedelta(days=30)).date(),
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("last_routine_appt_date", cm.exception.error_dict)
        cleaned_data.update(
            last_routine_appt_date=(get_utcnow() - relativedelta(days=30)).date()
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_raises_if_next_routine_appt_date_is_past(self):
        patient_group = PatientGroupMockModel(name="PARKSIDE", randomized=None)
        patient_log = PatientLogMockModel()
        cleaned_data = dict(
            name="ERIK",
            patient_group=patient_group,
            report_datetime=get_utcnow(),
            next_routine_appt_date=(get_utcnow() - relativedelta(days=30)).date(),
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("next_routine_appt_date", cm.exception.error_dict)

        cleaned_data.update(
            next_routine_appt_date=(get_utcnow() + relativedelta(days=30)).date()
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_add_patient_log_to_group(self):
        patient_log = PatientLogMockModel()
        patient_group = PatientGroupMockModel(
            name="PARKSIDE", patients=MockSet(), randomized=None
        )
        cleaned_data = dict(
            name="ERIK",
            report_datetime=get_utcnow(),
            patient_group=patient_group,
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        form_validator.validate()

    def test_move_group(self):
        patient_group = PatientGroupMockModel(
            name="WESTWOOD", patients=MockSet(), randomized=None, status=RECRUITING
        )
        patient_log = PatientLogMockModel(name="BUBBA", patient_group=patient_group)
        cleaned_data = dict(
            patient_group=patient_group,
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        form_validator.validate()

    def test_remove_group(self):
        patient_group = PatientGroupMockModel(
            name="WESTWOOD", patients=MockSet(), randomized=None, status=RECRUITING
        )
        patient_log = PatientLogMockModel(name="BUBBA", patient_group=patient_group)
        cleaned_data = dict(patient_group=None)
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        form_validator.validate()

    def test_remove_group_not_allowed_if_complete(self):
        patient_log = MockModel(
            mock_name="PatientLog",
            name="BUBBA",
            patient_group=MockModel(
                mock_name="PatientGroup",
                name="NORTHSIDE",
                randomized=None,
                status=COMPLETE,
            ),
        )
        cleaned_data = dict(patient_group=None)
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Cannot remove from current group. Group is complete.",
            cm.exception.message_dict.get("__all__")[0],
        )

        patient_group = PatientGroupMockModel(
            name="WESTWOOD",
            patients=MockSet(patient_log),
            randomized=None,
            status=COMPLETE,
        )

        cleaned_data = dict(patient_group=patient_group)
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Cannot remove from current group. Group is complete.",
            cm.exception.message_dict.get("__all__")[0],
        )

    def test_move_group_not_allowed_if_complete(self):
        patient_group1 = PatientGroupMockModel(
            name="WESTWOOD", patients=MockSet(), randomized=None, status=COMPLETE
        )
        patient_group2 = PatientGroupMockModel(
            name="NORTHSIDE", patients=MockSet(), randomized=None
        )
        patient_log2 = PatientLogMockModel(name="BUBBA", patient_group=patient_group2)
        cleaned_data = dict(
            patient_group=patient_group1,
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data, instance=patient_log2, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Cannot add to group", cm.exception.message_dict.get("__all__")[0])

    def test_patient_log_matches_screening(self):
        patient_log = PatientLogMockModel(name="ERIK")
        patient_group = PatientGroupMockModel(
            name="PARKSIDE", patients=MockSet(patient_log), randomized=None
        )
        data = [
            ("gender", "gender", MALE, MALE, "Gender", False),
            ("gender", "gender", FEMALE, MALE, "Gender", True),
            ("initials", "initials", "XX", "XX", "Initials", False),
            ("initials", "initials", "XX", "YY", "Initials", True),
            ("hospital_identifier", "hf_identifier", "12345", "12345", "Identifier", False),
            ("hospital_identifier", "hf_identifier", "12345", "54321", "Identifier", True),
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
