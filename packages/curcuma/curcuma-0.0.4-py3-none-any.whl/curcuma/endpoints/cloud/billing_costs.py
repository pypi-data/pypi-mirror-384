import locale
from loguru import logger

from ...endpoint import Endpoint


class BillingCosts(Endpoint):
    """
    Client for retrieving billing costs from the cloud API.

    Provides methods to fetch all billing costs, chart data, and to list costs per deployment.
    """

    def __init__(self, client, organization_id):
        """
        Initialize the BillingCosts client.

        Args:
            client: The HTTP client to use for requests.
            organization_id (str): The organization ID for billing.
        """
        self.BASE_URL = f"/api/v1/billing/costs/{organization_id}"
        super().__init__(client)

    def get_all(self) -> dict:
        """
        Retrieve all billing costs for deployments.

        Returns:
            dict: All billing costs data.
        """
        logger.info("Reading all billing costs")
        return self._get(self.BASE_URL + "/deployments")

    def get_charts(self) -> dict:
        """
        Retrieve billing cost chart data.

        Returns:
            dict: Chart billing costs data.
        """
        logger.info("Reading chart billing costs")
        return self._get(self.BASE_URL + "/charts")

    def charts(self):
        """
        Print billing cost chart data by date and values.
        """
        for t in self.get_charts().get("data"):
            print(f"date: {t.get('timestamp')}")
            for d in t.get("values"):
                print(d)

    def list(self, filter: str = None, country: str= "en"):
        """
        Print a list of deployment costs, optionally filtered by deployment name.

        Args:
            filter (str, optional): Filter string for deployment names.
        """
        if country == "de":
            fq_locale = "de_DE.UTF-8"
        elif country == "fr":
            fq_locale = "fr_FR.UTF-8"
        else:
            fq_locale = "en_US.UTF-8"
        locale.setlocale(locale.LC_ALL, fq_locale )
        r = self.get_all()
        deployment_costs = {}
        for deployment in r.get("deployments"):
            if deployment.get("deployment_name") in deployment_costs:
                deployment_costs[deployment.get("deployment_name")] += deployment.get("costs").get("total")
            else:
                deployment_costs[deployment.get("deployment_name")] = deployment.get("costs").get("total")
        total_costs = r.get('total_cost')
        filter_costs = 0
        for name, cost in sorted(deployment_costs.items(), key=lambda item: item[1], reverse=True):
            if filter is None or filter in name:
                print(f"Costs: {locale.format_string("%10.1f", cost, True)} ({locale.format_string("%.1f", cost / total_costs * 100)}%)  Name: {name}")
            if filter is not None and filter in name:
                filter_costs += cost
        print("=" * 25)
        if filter is not None:
            print(f"Filter: {locale.format_string("%9.1f", filter_costs, True)} ({locale.format_string("%.1f", filter_costs / total_costs * 100)}%)")
        print(f"Total: {locale.format_string("%10.1f", total_costs, True)}")
