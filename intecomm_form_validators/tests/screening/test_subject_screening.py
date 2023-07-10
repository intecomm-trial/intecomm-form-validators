from django import forms
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import DM, MALE, NO, NOT_APPLICABLE, YES
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

    def get_changelist_url(self):
        return "some_url"


class SubjectScreeningFormValidator(Base):
    def get_consent_for_period_or_raise(self):
        return None


class SubjectScreeningTests(TestCase):
    @staticmethod
    def patient_log(**kwargs):
        """Default is stable not screened"""
        opts = dict(
            patient_log_identifier="PXPXPXP",
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
            first_health_talk=NO,
            second_health_talk=NO,
            willing_to_screen=YES,
            screening_refusal_reason=None,
        )
        opts.update(**kwargs)
        return PatientLogMockModel(**opts)

    def get_cleaned_data(self):
        return dict(
            gender=MALE,
            consent_ability=YES,
            in_care_6m=YES,
            in_care_duration="5y",
            hiv_dx=NO,
            dm_dx=YES,
            htn_dx=NO,
            willing_to_screen=YES,
        )

    def test_cleaned_data_ok(self):
        patient_log = self.patient_log()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"patient_log_identifier": patient_log.patient_log_identifier})
        form_validator = SubjectScreeningFormValidator(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_consent_ability(self):
        patient_log = self.patient_log()
        form_validator = SubjectScreeningFormValidator(
            cleaned_data={
                "patient_log_identifier": patient_log.patient_log_identifier,
                "gender": MALE,
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
        patient_log = self.patient_log()
        form_validator = SubjectScreeningFormValidator(
            cleaned_data={
                "patient_log_identifier": patient_log.patient_log_identifier,
                "report_datetime": get_utcnow(),
                "gender": MALE,
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
        patient_log = self.patient_log()
        form_validator = SubjectScreeningFormValidator(
            cleaned_data={
                "patient_log_identifier": patient_log.patient_log_identifier,
                "report_datetime": get_utcnow(),
                "gender": MALE,
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

    def test_conditions_durations(self):
        patient_log = self.patient_log()
        cleaned_data = {
            "patient_log_identifier": patient_log.patient_log_identifier,
            "report_datetime": get_utcnow(),
            "gender": MALE,
            "consent_ability": YES,
            "in_care_6m": YES,
            "in_care_duration": "5y",
            "hiv_dx": NO,
            "dm_dx": YES,
            "htn_dx": NO,
            "dm_dx_ago": "5m",
        }
        form_validator = SubjectScreeningFormValidator(
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
        form_validator = SubjectScreeningFormValidator(
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
        form_validator = SubjectScreeningFormValidator(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_reasons_unsuitable_required_if_unsuitable_for_study_yes(self):
        patient_log = self.patient_log()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "patient_log_identifier": patient_log.patient_log_identifier,
                "unsuitable_for_study": YES,
                "reasons_unsuitable": "",
            }
        )
        form_validator = SubjectScreeningFormValidator(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("reasons_unsuitable", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("reasons_unsuitable")),
        )

    def test_reasons_unsuitable_not_required_if_unsuitable_for_study_not_yes(self):
        patient_log = self.patient_log()
        with self.subTest():
            cleaned_data = self.get_cleaned_data()
            cleaned_data.update(
                {
                    "patient_log_identifier": patient_log.patient_log_identifier,
                    "unsuitable_for_study": NO,
                    "reasons_unsuitable": "Some reason ....",
                }
            )
            form_validator = SubjectScreeningFormValidator(
                cleaned_data=cleaned_data,
                instance=SubjectScreeningMockModel(),
                model=SubjectScreeningMockModel,
            )
            with self.assertRaises(forms.ValidationError) as cm:
                form_validator.validate()
            self.assertIn("reasons_unsuitable", cm.exception.error_dict)
            self.assertIn(
                "This field is not required.",
                str(cm.exception.error_dict.get("reasons_unsuitable")),
            )

    def test_unsuitable_agreed_applicable_if_unsuitable_for_study_yes(self):
        patient_log = self.patient_log()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "patient_log_identifier": patient_log.patient_log_identifier,
                "unsuitable_for_study": YES,
                "reasons_unsuitable": "Some reason",
                "unsuitable_agreed": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("unsuitable_agreed", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("unsuitable_agreed")),
        )

    def test_unsuitable_agreed_not_applicable_if_unsuitable_for_study_no(self):
        patient_log = self.patient_log()
        for agreed_answ in [YES, NO]:
            with self.subTest(unsuitable_agreed=agreed_answ):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "patient_log_identifier": patient_log.patient_log_identifier,
                        "unsuitable_for_study": NO,
                        "reasons_unsuitable": "",
                        "unsuitable_agreed": agreed_answ,
                    }
                )
                form_validator = SubjectScreeningFormValidator(
                    cleaned_data=cleaned_data,
                    instance=SubjectScreeningMockModel(),
                    model=SubjectScreeningMockModel,
                )
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("unsuitable_agreed", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("unsuitable_agreed")),
                )

    def test_unsuitable_agreed_no_raises_if_unsuitable_for_study_yes(self):
        patient_log = self.patient_log()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "patient_log_identifier": patient_log.patient_log_identifier,
                "unsuitable_for_study": YES,
                "reasons_unsuitable": "Reason unsuitable",
                "unsuitable_agreed": NO,
            }
        )
        form_validator = SubjectScreeningFormValidator(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("unsuitable_agreed", cm.exception.error_dict)
        self.assertIn(
            (
                "The study coordinator MUST agree with your assessment. "
                "Please discuss before continuing."
            ),
            str(cm.exception.error_dict.get("unsuitable_agreed")),
        )

    def test_unsuitable_agreed_yes_with_unsuitable_for_study_yes_ok(self):
        patient_log = self.patient_log()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "patient_log_identifier": patient_log.patient_log_identifier,
                "unsuitable_for_study": YES,
                "reasons_unsuitable": "Reason unsuitable",
                "unsuitable_agreed": YES,
            }
        )
        form_validator = SubjectScreeningFormValidator(
            cleaned_data=cleaned_data,
            instance=SubjectScreeningMockModel(),
            model=SubjectScreeningMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
