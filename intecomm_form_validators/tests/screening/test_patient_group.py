from __future__ import annotations

from django import forms
from django_mock_queries.query import MockSet
from edc_constants.constants import COMPLETE, NO, YES

from intecomm_form_validators.screening import PatientGroupFormValidator as Base

from ..mock_models import PatientGroupMockModel, ScreeningRefusalReasonsMockModel
from ..test_case_mixin import TestCaseMixin


class PatientGroupTests(TestCaseMixin):
    @staticmethod
    def get_form_validator_cls(subject_screening=None):
        class PatientGroupFormValidator(Base):
            @property
            def subject_screening(self):
                return subject_screening

        return PatientGroupFormValidator

    def test_raises_if_randomized(self):
        patients = self.get_mock_patients(dm=10, htn=0, hiv=4)
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

    # def test_raises_if_status_not_complete(self):
    #     patients = self.get_mock_patients(dm=10, htn=0, hiv=4)
    #     patient_group = PatientGroupMockModel()
    #     form_validator = self.get_form_validator_cls()(
    #         cleaned_data=dict(
    #             status=RECRUITING, randomize_now=YES, patients=MockSet(*patients)
    #         ),
    #         instance=patient_group,
    #         model=PatientGroupMockModel,
    #     )
    #     self.assertRaises(forms.ValidationError, form_validator.validate)
    #     with self.assertRaises(forms.ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn("Invalid. Group is not complete", cm.exception.messages)

    def test_group_size_not_ok(self):
        patients = self.get_mock_patients(
            dm=10, htn=0, hiv=2, stable=True, screen=True, consent=True
        )
        patient_group = PatientGroupMockModel()
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Patient group must have at least 14 patients. Got 12.", cm.exception.messages
        )

    def test_group_size_ok(self):
        patients = self.get_mock_patients(
            dm=10, htn=0, hiv=4, stable=True, screen=True, consent=True
        )
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_group_size_overridden(self):
        patients = self.get_mock_patients(dm=10, htn=0, hiv=4)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
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
        patients = self.get_mock_patients(dm=10, htn=0, hiv=3)
        form_validator = self.get_form_validator_cls()(
            cleaned_data=dict(patients=MockSet(*patients), status=COMPLETE),
            instance=PatientGroupMockModel(randomized=False),
            model=PatientGroupMockModel,
        )
        self.assertRaises(forms.ValidationError, form_validator.validate)

    def test_review_patients_in_group_none_stable(self):
        patients = self.get_mock_patients(dm=10, htn=0, hiv=4, stable=False)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Patient is not known to be stable and in-care", "|".join(cm.exception.messages)
        )

    def test_review_patients_in_group_all_stable(self):
        patients = self.get_mock_patients(dm=10, htn=0, hiv=4, stable=YES)
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Patient has not screened for eligibility", "|".join(cm.exception.messages)
        )

    def test_review_patients_in_group_all_screened(self):
        patients = self.get_mock_patients(dm=10, htn=0, hiv=4, stable=YES, screen=True)
        patient_group = PatientGroupMockModel()
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("Patient has not consented", "|".join(cm.exception.messages))

    def test_review_patients_in_group_all_consented(self):
        patients = self.get_mock_patients(
            dm=10, htn=0, hiv=4, stable=YES, screen=True, consent=True
        )
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_ratio_ok(self):
        patients = self.get_mock_patients(
            dm=10, htn=0, hiv=4, stable=YES, screen=True, consent=True
        )
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_ratio_ok2(self):
        patients = self.get_mock_patients(
            dm=4, htn=4, hiv=4, hiv_ncd=2, stable=YES, screen=True, consent=True
        )
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_ratio_not_ok(self):
        for ratio in [[10, 0, 6], [11, 0, 3], [12, 0, 7], [13, 0, 7]]:
            with self.subTest(ratio=ratio):
                dm, htn, hiv = ratio
                patients = self.get_mock_patients(
                    dm, htn, hiv, stable=YES, screen=True, consent=True
                )
                patient_group = PatientGroupMockModel(patients=MockSet(*patients))
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

    # def test_confirm_randomize_now_required_if_randomize_now_yes(self):
    #     patients = self.get_mock_patients(
    #         dm=10, htn=0, hiv=4, stable=YES, screen=True, consent=True
    #     )
    #     patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))
    #
    #     form_validator = self.get_form_validator_cls()(
    #         cleaned_data={
    #             "status": COMPLETE,
    #             "randomize_now": YES,
    #             "confirm_randomize_now": "",
    #             "patients": MockSet(*patients),
    #         },
    #         instance=patient_group,
    #         model=PatientGroupMockModel,
    #     )
    #     with self.assertRaises(forms.ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn(
    #         "If you wish to randomize this group, please confirm",
    #         str(cm.exception.error_dict.get("confirm_randomize_now")),
    #     )

    # def test_confirm_randomize_now_not_required_if_randomize_now_not_yes(self):
    #     patients = self.get_mock_patients(
    #         dm=10, htn=0, hiv=4, stable=YES, screen=True, consent=True
    #     )
    #     patient_group = PatientGroupRandoMockModel(
    #         randomized=False, patients=MockSet(*patients)
    #     )
    #
    #     for randomize_now in [NO, "xxx"]:
    #         for confirm_randomize_now in ["R", "Rand", "RANDOMIZE"]:
    #             with self.subTest(
    #                 randomize_now=randomize_now,
    #                 confirm_randomize_now=confirm_randomize_now,
    #             ):
    #                 form_validator = self.get_form_validator_cls()(
    #                     cleaned_data={
    #                         "status": COMPLETE,
    #                         "randomize_now": randomize_now,
    #                         "confirm_randomize_now": confirm_randomize_now,
    #                         "patients": MockSet(*patients),
    #                     },
    #                     instance=patient_group,
    #                     model=PatientGroupRandoMockModel,
    #                 )
    #                 with self.assertRaises(forms.ValidationError) as cm:
    #                     form_validator.validate()
    #                 self.assertIn(
    #                     "This field is not required. "
    #                     "Only complete if you are ready to randomize now.",
    #                     str(cm.exception.error_dict.get("confirm_randomize_now")),
    #                 )

    def test_confirm_randomize_now_RANDOMIZE_randomize_now_yes_ok(self):
        patients = self.get_mock_patients(
            dm=10, htn=0, hiv=4, stable=YES, screen=True, consent=True
        )
        patient_group = PatientGroupMockModel(randomized=False, patients=MockSet(*patients))

        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": YES,
                "confirm_randomize_now": "RANDOMIZE",
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")

    def test_review_patients_in_group_patient_unwilling_to_screen_raises(self):
        patients = self.get_mock_patients(
            dm=10, htn=0, hiv=4, stable=YES, screen=True, consent=True
        )
        patient_group = PatientGroupMockModel()
        patients[1].willing_to_screen = NO
        patients[1].screening_refusal_reason = MockSet(
            ScreeningRefusalReasonsMockModel(name="need_to_think_about_it")
        )
        patients[1].save()
        patients[5].willing_to_screen = NO
        patients[5].screening_refusal_reason = MockSet(
            ScreeningRefusalReasonsMockModel(name="need_to_think_about_it")
        )
        patients[5].save()

        form_validator = self.get_form_validator_cls()(
            cleaned_data={
                "status": COMPLETE,
                "randomize_now": NO,
                "patients": MockSet(*patients),
            },
            instance=patient_group,
            model=PatientGroupMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn(
            "Patient reported as unwilling to screen. ",
            "|".join(cm.exception.messages),
        )
