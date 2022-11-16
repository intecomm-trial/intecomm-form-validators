from django import forms
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import COMPLETE, DM, HIV, HTN, NO, YES

from intecomm_form_validators.constants import RECRUITING
from intecomm_form_validators.screening import PatientGroupFormValidator as Base


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


class ConditionsMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "Conditions"
        super().__init__(*args, **kwargs)


class PatientGroupTests(TestCase):
    @staticmethod
    def get_form_validator_cls(subject_screening=None):
        class PatientGroupFormValidator(Base):
            @property
            def subject_screening(self):
                return subject_screening

            @staticmethod
            def patient_log_url(search_term) -> str:
                return "patient_log_url"

            @staticmethod
            def patient_log_changelist_url(search_term) -> str:
                return "patient_log_changelist_url"

        return PatientGroupFormValidator

    @staticmethod
    def get_mock_patients(
        dm=None,
        htn=None,
        hiv=None,
        stable=None,
        screening_identifier=None,
        subject_identifier=None,
    ) -> list:
        patients = []
        for condition, count in {DM: dm or 0, HTN: htn or 0, HIV: hiv or 0}.items():
            for i in range(0, count):
                screening_identifier = f"SCRN{condition}{i}" if screening_identifier else None
                subject_identifier = f"SUBJ{condition}{i}" if subject_identifier else None
                patients.append(
                    PatientLogMockModel(
                        name=f"NAME{condition}{i}",
                        stable=NO if stable is None else stable,
                        screening_identifier=screening_identifier,
                        subject_identifier=subject_identifier,
                        conditions=MockSet(
                            MockModel(
                                mock_name="Conditions",
                                name=condition,
                            )
                        ),
                    )
                )
        return patients

    def test_raises_if_randomized(self):
        patients = self.get_mock_patients(dm=10, hiv=4)
        patient_group = PatientGroupMockModel(randomized=True, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={}, instance=patient_group, model=PatientGroupMockModel
        )
        self.assertRaises(forms.ValidationError, form_validator.validate)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={}, instance=patient_group, model=PatientGroupMockModel
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_raises_if_not_complete(self):
        patients = self.get_mock_patients(dm=10, hiv=4)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"status": RECRUITING, "randomize": YES},
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        self.assertRaises(forms.ValidationError, form_validator.validate)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Invalid. Group is not complete", cm.exception.messages)

    def test_group_size_not_ok(self):
        patients = self.get_mock_patients(dm=10, hiv=2)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"status": COMPLETE, "randomize": NO, "patients": MockSet(*patients)},
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        self.assertRaises(forms.ValidationError, form_validator.validate)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Invalid. Must have at least 14 patients. Got 12.", cm.exception.messages
        )

    def test_group_size_ok(self):
        patients = self.get_mock_patients(dm=10, hiv=4)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"status": COMPLETE, "randomize": NO, "patients": MockSet(*patients)},
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        # gets past group size check and starts reviewing patients
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Patient is not known to be stable and in-care", "|".join(cm.exception.messages)
        )

    def test_group_size_too_small(self):
        patients = self.get_mock_patients(dm=10, hiv=3)
        form_validator = self.get_form_validator_cls()(
            cleaned_data=dict(patients=MockSet(*patients), status=COMPLETE),
            instance=PatientGroupMockModel(randomized=False),
            model=PatientGroupMockModel,
        )
        self.assertRaises(forms.ValidationError, form_validator.validate)

    def test_review_patients_in_group_none_stable(self):
        patients = self.get_mock_patients(dm=10, hiv=4, stable=NO)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"status": COMPLETE, "randomize": NO, "patients": MockSet(*patients)},
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Patient is not known to be stable and in-care", "|".join(cm.exception.messages)
        )

    def test_review_patients_in_group_all_stable(self):
        patients = self.get_mock_patients(dm=10, hiv=4, stable=YES)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"status": COMPLETE, "randomize": NO, "patients": MockSet(*patients)},
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Patient has not been screened for eligibility", "|".join(cm.exception.messages)
        )

    def test_review_patients_in_group_all_screened(self):
        patients = self.get_mock_patients(dm=10, hiv=4, stable=YES, screening_identifier=True)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"status": COMPLETE, "randomize": NO, "patients": MockSet(*patients)},
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Patient has not consented", "|".join(cm.exception.messages))

    def test_review_patients_in_group_all_consented(self):
        patients = self.get_mock_patients(
            dm=10, hiv=4, stable=YES, screening_identifier=True, subject_identifier=True
        )
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"status": COMPLETE, "randomize": NO, "patients": MockSet(*patients)},
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_ratio_ok(self):
        patients = self.get_mock_patients(
            dm=10, hiv=4, stable=YES, screening_identifier=True, subject_identifier=True
        )
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"status": COMPLETE, "randomize": NO, "patients": MockSet(*patients)},
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_ratio_not_ok(self):
        for dm, hiv in [(10, 6), (11, 3), (12, 7), (13, 7)]:
            with self.subTest(dm=dm, hiv=hiv):
                patients = self.get_mock_patients(
                    dm=dm,
                    hiv=hiv,
                    stable=YES,
                    screening_identifier=True,
                    subject_identifier=True,
                )
                patient_group = PatientGroupMockModel(
                    randomized=False, patients=MockSet(*patients)
                )
                form_validator = self.get_form_validator_cls()(
                    cleaned_data={
                        "status": COMPLETE,
                        "randomize": NO,
                        "patients": MockSet(*patients),
                    },
                    instance=patient_group,
                    model=PatientGroupMockModel,
                )
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("Ratio NDC:HIV not met", "|".join(cm.exception.messages))
