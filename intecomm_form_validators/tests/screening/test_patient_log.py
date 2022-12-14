from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django import forms
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import FEMALE, MALE
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
        patient_log = PatientLogMockModel(name="ERIK")
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

    # @tag("1")
    # def test_attempt_to_change_patient_in_randomized_group_raises(self):
    #     patients = self.get_mock_patients(ratio=[10, 0, 4])
    #     save_patients = []
    #     for patient in patients:
    #         patient.id = uuid4()
    #         save_patients.append(patient)
    #     patient_group = PatientGroupMockModel(
    #         randomized=True, patients=MockSet(*save_patients)
    #     )
    #     patient_group.save()
    #
    #     patient_log = save_patients[0]
    #     cleaned_data = dict(
    #         next_appt_date=(get_utcnow() + relativedelta(days=60)).date(),
    #     )
    #     form_validator = self.get_form_validator_cls()(
    #         cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
    #     )
    #     with self.assertRaises(forms.ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn("next_appt_date", cm.exception.error_dict)
