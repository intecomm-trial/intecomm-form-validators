from django.apps import apps as django_apps
from edc_constants.constants import NO
from edc_crf.utils import raise_if_crf_does_not_exist


class HealthEconomicsFormValidatorMixin:
    def raise_if_health_economics_patient_crf_does_not_exist(self):
        model_cls = django_apps.get_model("intecomm_subject.healtheconomicshouseholdhead")
        if model_cls.objects.get(subject_identifier=self.subject_identifier).hoh == NO:
            raise_if_crf_does_not_exist(
                self.cleaned_data.get("subject_visit"),
                model="intecomm_subject.healtheconomicspatient",
            )
