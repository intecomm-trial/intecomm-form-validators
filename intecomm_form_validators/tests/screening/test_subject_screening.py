from django import forms
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import DM, FEMALE, MALE, NO, YES
from edc_utils import get_utcnow

from intecomm_form_validators.screening import SubjectScreeningFormValidator as Base


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

    def get_gender_display(self):
        return "MALE" if self.gender == MALE else "FEMALE"


class SubjectScreeningTests(TestCase):
    @staticmethod
    def get_form_validator_cls(subject_screening=None):
        class SubjectScreeningFormValidator(Base):
            def get_consent_for_period_or_raise(self):
                return None

        return SubjectScreeningFormValidator

    def patient_log(self, **kwargs):
        """Default is stable not screened"""
        opts = dict(
            name="THING ONE",
            gender=MALE,
            stable=YES,
            screening_identifier=None,
            subject_identifier=None,
            conditions=MockSet(
                MockModel(
                    mock_name="Conditions",
                    name=DM,
                )
            ),
        )
        opts.update(**kwargs)
        return PatientLogMockModel(**opts)

    def test_gender(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"gender": MALE, "patient_log": self.patient_log(gender=FEMALE)},
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Invalid. Expected FEMALE", "|".join(cm.exception.messages))

    def test_gender_not_matching(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={"gender": MALE, "patient_log": self.patient_log(gender=FEMALE)},
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Invalid. Expected FEMALE", "|".join(cm.exception.messages))

    def test_consent_ability(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "gender": MALE,
                "patient_log": self.patient_log(gender=MALE),
                "consent_ability": NO,
            },
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "You may NOT screen this subject without their verbal consent",
            "|".join(cm.exception.messages),
        )

    def test_in_care_duration(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "report_datetime": get_utcnow(),
                "gender": MALE,
                "patient_log": self.patient_log(gender=MALE),
                "consent_ability": YES,
                "in_care_6m": YES,
                "in_care_duration": "1d",
                "hiv_dx": NO,
                "dm_dx": YES,
                "htn_dx": NO,
            },
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Expected at least 6m from the report date",
            "|".join(cm.exception.messages),
        )

    def test_in_care_duration_format(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "report_datetime": get_utcnow(),
                "gender": MALE,
                "patient_log": self.patient_log(gender=MALE),
                "consent_ability": YES,
                "in_care_6m": YES,
                "in_care_duration": "ERIK",
                "hiv_dx": NO,
                "dm_dx": YES,
                "htn_dx": NO,
            },
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Invalid format",
            "|".join(cm.exception.messages),
        )

    def test_no_conditions_in_patient_log(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "gender": MALE,
                "patient_log": self.patient_log(gender=MALE, conditions=[]),
                "consent_ability": YES,
                "in_care_6m": YES,
                "in_care_duration": "5y",
                "hiv_dx": YES,
            },
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "No conditions (HIV/DM/HTN) have been indicated for this patient",
            "|".join(cm.exception.messages),
        )

    def test_conditions_not_matching_patient_log(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "gender": MALE,
                "patient_log": self.patient_log(gender=MALE),
                "consent_ability": YES,
                "in_care_6m": YES,
                "in_care_duration": "5y",
                "hiv_dx": YES,
            },
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Invalid. HIV was not indicated as a condition on the Patient Log",
            "|".join(cm.exception.messages),
        )

    def test_conditions_matching_patient_log(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "gender": MALE,
                "patient_log": self.patient_log(gender=MALE),
                "consent_ability": YES,
                "in_care_6m": YES,
                "in_care_duration": "5y",
                "hiv_dx": NO,
                "dm_dx": YES,
                "htn_dx": NO,
            },
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_conditions_durations(self):
        cleaned_data = {
            "report_datetime": get_utcnow(),
            "gender": MALE,
            "patient_log": self.patient_log(gender=MALE),
            "consent_ability": YES,
            "in_care_6m": YES,
            "in_care_duration": "5y",
            "hiv_dx": NO,
            "dm_dx": YES,
            "htn_dx": NO,
            "dm_dx_ago": "5m",
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Expected at least 6m from the report date",
            "|".join(cm.exception.messages),
        )

        cleaned_data.update({"dm_dx_ago": "ERIK"})
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Invalid format",
            "|".join(cm.exception.messages),
        )

        cleaned_data.update({"dm_dx_ago": "6m"})
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_conditions_not_matching_patient_log2(self):
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "gender": MALE,
                "patient_log": self.patient_log(gender=MALE),
                "consent_ability": YES,
                "in_care_6m": YES,
                "in_care_duration": "5y",
                "dm_dx": NO,
            },
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Invalid. DM was indicated as a condition on the Patient Log",
            "|".join(cm.exception.messages),
        )

    def test_eligibility(self):
        pass
