from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from edc_constants.constants import COMPLETE, NO, NOT_APPLICABLE, YES
from edc_dx_review.constants import THIS_CLINIC
from edc_utils import get_utcnow

from ..test_case_mixin import TestCaseMixin


class HivReviewTests(TestCaseMixin):
    def setUp(self) -> None:
        super().setUp()
        raise_missing_clinical_review_patcher = patch(
            "intecomm_form_validators.subject.hiv_review_form_validator."
            "raise_if_clinical_review_does_not_exist"
        )
        self.addCleanup(raise_missing_clinical_review_patcher.stop)
        self.mock_raise_missing_clinical_review = raise_missing_clinical_review_patcher.start()

        get_initial_review_model_cls_patcher = patch(
            "intecomm_form_validators.subject.hiv_review_form_validator."
            "get_initial_review_model_cls"
        )
        self.addCleanup(get_initial_review_model_cls_patcher.stop)
        self.mock_get_initial_review_model_cls = get_initial_review_model_cls_patcher.start()

        self.dx_date = get_utcnow() - relativedelta(days=60)
        self.rx_date = self.dx_date + relativedelta(days=3)

    def get_cleaned_data(self, report_datetime: datetime = None, **kwargs) -> dict:
        cleaned_data = dict(
            subject_visit=self.get_subject_visit(),
            report_datetime=report_datetime or get_utcnow(),
            dx_date=get_utcnow() - relativedelta(days=60),
            dx_ago="",
            receives_care=YES,
            clinic=THIS_CLINIC,
            clinic_other="",
            rx_init=YES,
            rx_init_date=self.rx_date,
            rx_init_ago="",
            has_vl=NO,
            drawn_date=None,
            vl=None,
            vl_quantifier=NOT_APPLICABLE,
            has_cd4=NO,
            cd4=None,
            cd4_date=None,
            crf_status=COMPLETE,
            crf_status_comments="",
        )
        cleaned_data.update(**kwargs)
        return cleaned_data

    # def test_cleaned_data_ok(self):
    #     self.mock_raise_missing_clinical_review.return_value = False
    #     self.mock_get_initial_review_model_cls.return_value = HivInitialReviewMockModel()()
    #     hiv_review = HivReviewMockModel()
    #     cleaned_data = self.get_cleaned_data()
    #     form_validator = HivReviewFormValidator(
    #         cleaned_data=cleaned_data,
    #         instance=hiv_review,
    #         model=HivReviewMockModel,
    #     )
    #     try:
    #         form_validator.validate()
    #     except forms.ValidationError as e:
    #         self.fail(f"ValidationError unexpectedly raised. Got {e}")
    #
    # def test_rx_init_is_applicable(self):
    #     hiv_review = HivReviewMockModel()
    #     cleaned_data = self.get_cleaned_data(rx_init=NOT_APPLICABLE)
    #     form_validator = HivReviewFormValidator(
    #         cleaned_data=cleaned_data,
    #         instance=hiv_review,
    #         model=HivReviewMockModel,
    #     )
    #     with self.assertRaises(forms.ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn("rx_init", form_validator._errors)
