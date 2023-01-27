from __future__ import annotations

from django.test import TestCase
from django_mock_queries.query import MockSet
from edc_constants.constants import DM, HIV, HTN, NO, YES

from .mock_models import (
    AppointmentMockModel,
    ConditionsMockModel,
    PatientLogMockModel,
    SubjectVisitMockModel,
)


class TestCaseMixin(TestCase):
    def get_mock_patients(
        self,
        ratio: list[int, int, int] | None = None,
        stable: bool | None = None,
        screen: bool | None = None,
        consent: bool | None = None,
    ) -> list:
        """Returns a list of mock patient logs"""
        patients = []
        ratio = ratio or (5, 5, 4)  # (DM, HTN, HIV)
        for i in range(0, ratio[0]):
            patients.append(self.get_mock_patient(DM, i + 100, stable, screen, consent))
        for i in range(0, ratio[1]):
            patients.append(self.get_mock_patient(HTN, i + 200, stable, screen, consent))
        for i in range(0, ratio[2]):
            patients.append(self.get_mock_patient(HIV, i + 300, stable, screen, consent))
        return patients

    @staticmethod
    def get_mock_patient(
        condition: str | list[str],
        i: int | None = None,
        stable: bool | None = None,
        screen: bool | None = None,
        consent: bool | None = None,
    ):
        """Returns a mock patient log"""
        conditions = [condition] if isinstance(condition, (str,)) else condition
        stable = YES if stable else NO
        screening_identifier = f"XYZ{str(i)}" if screen else None
        subject_identifier = f"999-{str(i)}" if consent else None
        return PatientLogMockModel(
            name=f"NAME-{str(i)}",
            stable=stable,
            screening_identifier=screening_identifier,
            subject_identifier=subject_identifier,
            conditions=MockSet(
                *[ConditionsMockModel(name=x) for x in conditions],
            ),
        )

    @staticmethod
    def get_subject_visit(
        schedule_name: str = None,
        visit_code: str = None,
        visit_code_sequence: int = None,
        timepoint: int = None,
    ):
        appointment = AppointmentMockModel(
            schedule_name=schedule_name,
            visit_code=visit_code,
            visit_code_sequence=visit_code_sequence,
            timepoint=timepoint,
        )
        return SubjectVisitMockModel(appointment=appointment)
