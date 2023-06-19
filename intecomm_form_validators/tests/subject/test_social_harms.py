from __future__ import annotations

from unittest.mock import patch

from django import forms
from edc_constants.constants import YES

from intecomm_form_validators.subject import SocialHarmsFormValidator as Base

from ..mock_models import SocialHarmsMockModel
from ..test_case_mixin import TestCaseMixin


class SocialHarmsTests(TestCaseMixin):
    @staticmethod
    def get_form_validator_cls():
        class SocialHarmsFormValidator(Base):
            pass

        return SocialHarmsFormValidator

    @patch(
        "intecomm_form_validators.subject.social_harms_form_validator."
        "raise_if_clinical_review_does_not_exist"
    )
    def test_ok(self, mock_func):
        social_harms = SocialHarmsMockModel()
        cleaned_data = {
            "subject_visit": None,
            "partner": YES,
            "partner_disclosure": None,
        }
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=social_harms,
            model=SocialHarmsMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("partner_disclosure", cm.exception.error_dict)

        cleaned_data.update(
            {
                "partner_disclosure": "blah",
                "partner_impact": YES,
                "partner_impact_severity": None,
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=social_harms,
            model=SocialHarmsMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("partner_impact_severity", cm.exception.error_dict)

        cleaned_data.update(
            {
                "partner_impact_severity": "blah",
                "healthcare_impact": YES,
                "healthcare_impact_severity": None,
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=social_harms,
            model=SocialHarmsMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("healthcare_impact_severity", cm.exception.error_dict)

        cleaned_data.update(
            {
                "partner_impact_severity": "blah",
                "healthcare_impact": YES,
                "healthcare_impact_severity": "blah",
                "other_impact": YES,
                "other_impact_description": None,
                "other_impact_severity": None,
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=social_harms,
            model=SocialHarmsMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("other_impact_description", cm.exception.error_dict)

        cleaned_data.update(
            {
                "partner_impact_severity": "blah",
                "healthcare_impact": YES,
                "healthcare_impact_severity": "blah",
                "other_impact": YES,
                "other_impact_description": "blah",
                "other_impact_severity": None,
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=social_harms,
            model=SocialHarmsMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("other_impact_severity", cm.exception.error_dict)

        cleaned_data.update(
            {
                "partner_impact_severity": "blah",
                "healthcare_impact": YES,
                "healthcare_impact_severity": "blah",
                "other_impact": YES,
                "other_impact_description": "blah",
                "other_impact_severity": "blah",
            }
        )
        form_validator = self.get_form_validator_cls()(
            cleaned_data=cleaned_data,
            instance=social_harms,
            model=SocialHarmsMockModel,
        )
        try:
            form_validator.validate()
        except forms.ValidationError:
            self.fail("ValidationError unexpectedly raised")
