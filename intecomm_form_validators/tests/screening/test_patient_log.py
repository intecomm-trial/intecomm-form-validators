import pdb

from dateutil.relativedelta import relativedelta
from django import forms
from django.test import TestCase, tag
from django_mock_queries.query import MockModel, MockSet
from edc_utils import get_utcnow

from intecomm_form_validators.screening import PatientLogFormValidator


class PatientGroupMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "PatientGroup"
        super().__init__(*args, **kwargs)


class PatientLogMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "PatientLog"
        super().__init__(*args, **kwargs)


class PatientLogTests(TestCase):
    def test_raises_if_randomized(self):
        patient_group = PatientGroupMockModel(randomized=True)
        patient_log = PatientLogMockModel(patient_group=patient_group)
        form_validator = PatientLogFormValidator(
            cleaned_data={}, instance=patient_log, model=PatientLogMockModel
        )
        self.assertRaises(forms.ValidationError, form_validator.validate)
        # try:
        #     form_validator.validate()
        # except forms.ValidationError as e:
        #     self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_raises_if_future_date(self):
        patient_group = PatientGroupMockModel(name="PARKSIDE", randomized=None)
        patient_log = PatientLogMockModel()
        cleaned_data = dict(
            name="ERIK",
            patient_group=patient_group,
            report_datetime=get_utcnow(),
            last_routine_appt_date=(get_utcnow() + relativedelta(days=30)).date(),
        )
        form_validator = PatientLogFormValidator(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("last_routine_appt_date", cm.exception.error_dict)

        cleaned_data.update(
            last_routine_appt_date=(get_utcnow() - relativedelta(days=30)).date()
        )

        form_validator = PatientLogFormValidator(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_raises_if_not_future_date(self):
        patient_group = PatientGroupMockModel(name="PARKSIDE", randomized=None)
        patient_log = PatientLogMockModel()
        cleaned_data = dict(
            name="ERIK",
            patient_group=patient_group,
            report_datetime=get_utcnow(),
            next_routine_appt_date=(get_utcnow() - relativedelta(days=30)).date(),
        )
        form_validator = PatientLogFormValidator(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("next_routine_appt_date", cm.exception.error_dict)

        cleaned_data.update(
            next_routine_appt_date=(get_utcnow() + relativedelta(days=30)).date()
        )

        form_validator = PatientLogFormValidator(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_add_to_group(self):
        patient_log = PatientLogMockModel()
        patient_group = PatientGroupMockModel(
            name="PARKSIDE", patients=MockSet(), randomized=None
        )
        cleaned_data = dict(
            name="ERIK",
            report_datetime=get_utcnow(),
            patient_group=patient_group,
        )
        form_validator = PatientLogFormValidator(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
        form_validator.validate()

    @tag("1")
    def test_move_group(self):

        patient_log = PatientLogMockModel(name="ERIK")
        patient_group = PatientGroupMockModel(
            name="PARKSIDE", patients=MockSet(patient_log), randomized=None
        )
        cleaned_data = dict(
            name="ERIK",
            report_datetime=get_utcnow(),
            patient_group=patient_group,
        )
        form_validator = PatientLogFormValidator(
            cleaned_data=cleaned_data, instance=patient_log, model=PatientLogMockModel
        )
