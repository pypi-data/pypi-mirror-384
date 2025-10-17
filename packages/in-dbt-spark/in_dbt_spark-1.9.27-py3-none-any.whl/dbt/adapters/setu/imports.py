import importlib

from dbt.adapters.events.logging import AdapterLogger

logger = AdapterLogger("Spark")


class SetuCluster:
    """Module imports from in-dbt MP"""

    def __init__(self, cluster=None):
        self.cluster = cluster
        try:
            self.cluster_impl = importlib.import_module("linkedin.indbt.utils.setu_cluster")
        except Exception as e:
            logger.error(
                "Error while importing linkedin.indbt.utils.setu_cluster module,"
                "Please reach out to indbt on-call for support"
            )
            raise ModuleNotFoundError(e)

    def get_url(self):
        """
        Returns setu cluster URL based on platform
        """
        return self.cluster_impl.get_url(self.cluster)

    def get_grestin_certs_for_biz_machines(self):
        """
        Create & get grestin certs for users
        """
        return self.cluster_impl.get_grestin_certs(self.cluster)

    def get_dv_token_from_grestin_cert(self, fabric, dv_token_address, cert, key):
        """
        Get DV token from grestin cert
        :param fabric: fabric for dv token
        :type fabric: string
        :param dv_token_address: address for conversion of dv token from grestin cert
        :type dv_token_address: string
        :param cert: path for grestin certificate
        :type cert: string
        :param key: path for grestin key
        :type key: string
        :return: datavault token
        :rtype: string
        """
        return self.cluster_impl.get_dv_token_from_grestin_cert(
            fabric, dv_token_address, cert, key
        )
