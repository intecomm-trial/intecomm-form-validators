from dateutil.relativedelta import relativedelta
from edc_crf.crf_form_validator import CrfFormValidator
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import INVALID_ERROR


class NextAppointmentFormValidator(CrfFormValidator):
    def __init__(self, **kwargs):
        self._integrated_clinic_days = None
        super().__init__(**kwargs)

    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.date_not_before(
            "report_datetime",
            "appt_date",
            msg="Cannot be before the report date",
            convert_to_date=True,
        )
        self.date_not_equal(
            "report_datetime",
            "appt_date",
            msg="Cannot be the same as the report date",
            convert_to_date=True,
        )

        if self.cleaned_data.get("report_datetime") and self.cleaned_data.get("appt_date"):
            report_date = self.cleaned_data.get("report_datetime").date()
            if self.cleaned_data.get("appt_date") > report_date + relativedelta(months=6):
                raise self.raise_validation_error(
                    {"appt_date": "Cannot be more than 6 months from report date"},
                    INVALID_ERROR,
                )
        self.validate_date_is_on_clinic_day()

    @property
    def integrated_clinic_days(self) -> list[int]:
        if not self._integrated_clinic_days:
            if self.cleaned_data.get("health_facility"):
                self._integrated_clinic_days = self.cleaned_data.get(
                    "health_facility"
                ).clinic_days
            # if not self._integrated_clinic_days:
            #     site = self.cleaned_data.get("subject_visit").site
            #     if s_obj := [s for s in all_sites.get("uganda") if s.site_id == site.id]:
            #         self._integrated_clinic_days = s_obj[0].integrated_clinic_days
            #     else:
            #         self._integrated_clinic_days = [
            #             s for s in all_sites.get("tanzania") if s.site_id == site.id
            #         ][0].integrated_clinic_days
        return self._integrated_clinic_days

    def validate_date_is_on_clinic_day(self):
        if appt_date := self.cleaned_data.get("appt_date"):
            if appt_date.isoweekday() > 5:
                day = "Saturday" if appt_date.isoweekday() == 6 else "Sunday"
                raise self.raise_validation_error(
                    {"appt_date": f"Expected Mon-Fri. Got {day}"},
                    INVALID_ERROR,
                )
        if appt_date and self.cleaned_data.get("subject_visit").site:
            if (
                self.integrated_clinic_days
                and appt_date.isoweekday() not in self.integrated_clinic_days
            ):
                dct = dict(zip([1, 2, 3, 4, 5, 6], ["M", "T", "W", "Th", "F", "Sa"]))
                expected_days = [v for k, v in dct.items() if k in self.integrated_clinic_days]
                raise self.raise_validation_error(
                    {
                        "appt_date": (
                            "Not an integrated clinic day. "
                            f"Expected {''.join(expected_days)}. "
                            f"Got {appt_date.strftime('%A')}"
                        )
                    },
                    INVALID_ERROR,
                )
