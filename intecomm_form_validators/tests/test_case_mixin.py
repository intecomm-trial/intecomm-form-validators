from __future__ import annotations

from uuid import uuid4

from django.conf import settings
from django.test import TestCase
from django_mock_queries.query import MockSet
from edc_constants.constants import DM, HIV, HTN, NO, YES
from faker import Faker

from .mock_models import (
    AppointmentMockModel,
    ConditionsMockModel,
    PatientLogMockModel,
    SubjectVisitMockModel,
)

fake = Faker()


class TestCaseMixin(TestCase):
    def get_mock_patients(
        self,
        dm: int = None,
        htn: int = None,
        hiv: int = None,
        ncd: int = None,
        hiv_ncd: int = None,
        stable: bool | None = None,
        screen: bool | None = None,
        consent: bool | None = None,
        site: str | None = None,
    ) -> list:
        """Returns a list of mock patient logs"""
        patients = []
        default_ratio = (5, 5, 4, 0, 0)
        ratio = (dm or 0, htn or 0, hiv or 0, ncd or 0, hiv_ncd or 0) or default_ratio
        for i in range(0, ratio[0]):
            patients.append(
                self.get_mock_patient(
                    DM,
                    i=i + 100,
                    stable=stable,
                    screen=screen,
                    consent=consent,
                    site=site,
                )
            )
        for i in range(0, ratio[1]):
            patients.append(
                self.get_mock_patient(
                    HTN,
                    i=i + 200,
                    stable=stable,
                    screen=screen,
                    consent=consent,
                    site=site,
                )
            )
        for i in range(0, ratio[2]):
            patients.append(
                self.get_mock_patient(
                    HIV,
                    i=i + 300,
                    stable=stable,
                    screen=screen,
                    consent=consent,
                    site=site,
                )
            )
        for i in range(0, ratio[3]):
            patients.append(
                self.get_mock_patient(
                    DM,
                    HTN,
                    i=i + 300,
                    stable=stable,
                    screen=screen,
                    consent=consent,
                    site=site,
                )
            )
        for i in range(0, ratio[4]):
            patients.append(
                self.get_mock_patient(
                    HIV,
                    DM,
                    HTN,
                    i=i + 300,
                    stable=stable,
                    screen=screen,
                    consent=consent,
                    site=site,
                )
            )
        return patients

    @staticmethod
    def get_mock_patient(
        *conditions: str | list[str],
        i: int | None = None,
        stable: bool | None = None,
        screen: bool | None = None,
        consent: bool | None = None,
        site: str | None = None,
        willing_to_screen: str | None = None,
    ):
        """Returns a mock patient log"""
        # conditions = [condition] if isinstance(condition, (str,)) else condition
        stable = YES if stable else NO
        willing_to_screen = YES if willing_to_screen is None else willing_to_screen
        index = f"{i}"
        index = index.zfill(5)
        screening_identifier = f"XYZ{index}" if screen else str(uuid4())
        index = f"{i}"
        index = index.zfill(2)
        subject_identifier = (
            f"{settings.SITE_ID}-{settings.SITE_ID}-00{index}-2" if consent else str(uuid4())
        )
        first_name = fake.first_name()
        last_name = fake.last_name()
        initials = f"{first_name[0]}{i}{last_name[0]}"
        return PatientLogMockModel(
            legal_name=f"{first_name} {last_name}",
            familiar_name=f"{first_name} {last_name}",
            initials=initials,
            stable=stable,
            willing_to_screen=willing_to_screen,
            screening_identifier=screening_identifier,
            subject_identifier=subject_identifier,
            conditions=MockSet(
                *[ConditionsMockModel(name=x) for x in conditions],
            ),
            site=site,
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
