import unittest

from system_tests.e2e.base_test import BaseTestServerStream
from system_tests.e2e.digital_sales_test_helpers import DigitalSalesTestHelpers


class TestServerStreamFast(BaseTestServerStream):
    """
    Test class for Cuga agent in FAST mode.
    """

    test_env_vars = {"DYNACONF_FEATURES__CUGA_MODE": "fast"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helpers = DigitalSalesTestHelpers()

    async def test_get_top_account_by_revenue_stream_fast(self):
        """Test getting the top account by revenue from my accounts."""
        await self.helpers.test_get_top_account_by_revenue_stream(self, "fast")

    async def test_list_my_accounts_fast(self):
        """Test listing all my accounts and how many are there."""
        await self.helpers.test_list_my_accounts(self, "fast")

    async def test_find_vp_sales_active_high_value_accounts_fast(self):
        """Test finding Vice President of Sales in Active, Tech Transformation Accounts."""
        await self.helpers.test_find_vp_sales_active_high_value_accounts(self, "fast")


if __name__ == "__main__":
    unittest.main()
