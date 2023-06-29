from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from django import forms
from django.test import tag
from edc_constants.constants import COMPLETE
from edc_utils import get_utcnow

from ...subject.health_economics import HealthEconomicsPatientFormValidator
from ..mock_models import HealthEconomicsPatientMockModel
from ..test_case_mixin import TestCaseMixin


class HePatientTests(TestCaseMixin):
    def get_cleaned_data(self, report_datetime: datetime = None) -> dict:
        cleaned_data = dict(
            subject_visit=self.get_subject_visit(visit_code="1000", visit_code_sequence=0),
            report_datetime=report_datetime or get_utcnow(),
            crf_status=COMPLETE,
            crf_status_comments="",
        )
        return cleaned_data

    @patch(
        "intecomm_form_validators.subject.health_economics.patient_form_validator"
        ".raise_if_clinical_review_does_not_exist"
    )
    @patch(
        "intecomm_form_validators.subject.health_economics.patient_form_validator."
        "raise_if_crf_does_not_exist"
    )
    @tag("2")
    def test_patient_head(self, mock_review_exists, mock_crf_exists):
        mock_review_exists.return_value = True
        mock_crf_exists.return_value = True
        patient = HealthEconomicsPatientMockModel()
        cleaned_data = self.get_cleaned_data()
        form_validator = HealthEconomicsPatientFormValidator(
            cleaned_data=cleaned_data,
            instance=patient,
            model=HealthEconomicsPatientMockModel,
        )
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("relationship_to_hoh", cm.exception.error_dict)
