"""
Procuret Python
Exercise Instalment Link Test
author: hugh@blinkybeach.com
"""
from procuret.integrate.xero import XeroEntityMap
from procuret.tests.test_result import Success, TestResult
from procuret.tests.variants.with_supplier import TestWithSupplier
from procuret.session import Perspective


class RetrieveXeroEntityMap(TestWithSupplier):

    NAME = 'Retrieve a Xero EntityMap'

    test_perspective = Perspective.SUPPLIER

    def execute(self) -> TestResult:

        entity_map = XeroEntityMap.retrieve(
            entity_id=self.supplier_id,
            session=self.session
        )

        # For the purposes of this test, an absent EntityMap with no errors
        # is an adequate outcome.
        assert entity_map is None or isinstance(entity_map, XeroEntityMap)

        return Success()
