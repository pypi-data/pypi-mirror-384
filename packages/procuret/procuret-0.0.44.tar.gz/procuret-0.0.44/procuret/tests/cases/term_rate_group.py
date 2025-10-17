"""
Procuret Python
Exercise Term Rate Group Test
author: hugh@blinkybeach.com
"""
from procuret.tests.variants.with_supplier import TestWithSupplier
from procuret.tests.test_result import Success, TestResult
from procuret.session import Perspective
from procuret.ancillary.command_line import CommandLine
from procuret.term_rate.group import TermRateGroup


class ExerciseTermRateGroup(TestWithSupplier):

    NAME = 'Retrieve a TermRateGroup'

    test_perspective = Perspective.SUPPLIER

    def execute(self) -> TestResult:

        cl = CommandLine.load()

        group_id = cl.require(
            key='--term-rate-group',
            of_type=str,
            type_name='string'
        )

        group = TermRateGroup.retrieve(
            public_id=group_id,
            session=self.session
        )

        assert isinstance(group, TermRateGroup)

        return Success()
