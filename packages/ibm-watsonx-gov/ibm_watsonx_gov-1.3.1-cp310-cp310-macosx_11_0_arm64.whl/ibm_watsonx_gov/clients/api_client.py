
# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

from ibm_cloud_sdk_core.authenticators import (BearerTokenAuthenticator,
                                               CloudPakForDataAuthenticator,
                                               IAMAuthenticator)
from ibm_watson_openscale import APIClient as WOSClient
from ibm_watsonx_gov.clients.wx_ai_client import WXAIClient
from ibm_watsonx_gov.entities.credentials import Credentials
from ibm_watsonx_gov.entities.enums import Region
from ibm_watsonx_gov.utils.async_util import run_in_event_loop
from ibm_watsonx_gov.utils.segment_batch_manager import SegmentBatchManager
from ibm_watsonx_gov.utils.url_mapping import (WATSONX_REGION_URLS,
                                               WOS_URL_MAPPING)


class APIClient():
    """
    The IBM watsonx.governance sdk client. It is required to access the watsonx.governance APIs.
    """

    def __init__(self, credentials: Credentials | None = None):
        self.credentials = credentials
        self.is_cpd = False
        if self.credentials.token:
            authenticator = BearerTokenAuthenticator(
                bearer_token=self.credentials.token)
            if self.credentials.version:
                self.is_cpd = True
        elif self.credentials.version:
            authenticator = CloudPakForDataAuthenticator(url=self.credentials.url,
                                                         username=self.credentials.username,
                                                         password=self.credentials.password,
                                                         apikey=self.credentials.api_key,
                                                         disable_ssl_verification=self.credentials.disable_ssl
                                                         )
            self.is_cpd = True
        elif self.credentials.region == Region.AP_SOUTH.value:
            from ibm_cloud_sdk_core.authenticators import MCSPV2Authenticator
            iam_url = WATSONX_REGION_URLS.get(
                self.credentials.region).iam_url
            authenticator = MCSPV2Authenticator(apikey=self.credentials.api_key, url=iam_url,
                                                scope_id=self.credentials.scope_id, scope_collection_type=self.credentials.scope_collection_type)
        else:
            iam_url = WATSONX_REGION_URLS.get(
                self.credentials.region).iam_url
            authenticator = IAMAuthenticator(apikey=self.credentials.api_key,
                                             url=iam_url,
                                             disable_ssl_verification=self.credentials.disable_ssl)
            if self.credentials.region in [Region.US_GOV_EAST1.value, "govcloudpreprod"]:
                authenticator.token_manager.OPERATION_PATH = "/api/rest/mcsp/apikeys/token"
                authenticator.token_manager.token_name = "token"

        try:
            self.wos_client = WOSClient(
                authenticator=authenticator,
                service_url=self.credentials.url,
                service_instance_id=self.credentials.service_instance_id,
            )
        except Exception as e:
            if "Multiple service instance id exists" in str(e) or "You are not authorized to access AI OpenScale instance" in str(e):
                raise e
            else:
                if self.is_cpd:
                    dai_url = self.credentials.url
                else:
                    dai_url = WATSONX_REGION_URLS.get(
                        self.credentials.region).dai_url
                self.wos_client = WXAIClient(service_url=dai_url,
                                             authenticator=authenticator,
                                             disable_ssl_verification=self.credentials.disable_ssl,
                                             is_cpd=self.is_cpd)
                self.wos_client.validate_user()

        # Adding segment event
        segment_manager = SegmentBatchManager(api_client=self)
        run_in_event_loop(segment_manager.track_event, {
                          "objectType": "API Client Initialization"})

    @property
    def credentials(self):
        return self._credentials

    @credentials.setter
    def credentials(self, credentials):
        """
        Setter for credentials object. If not provided, it will create a credentials object from environment variables.
        """
        if not credentials:
            self._credentials = Credentials.create_from_env()
        else:
            self._credentials = credentials
