# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import aiohttp
from ibm_watsonx_gov.utils.gov_sdk_logger import GovSDKLogger
from ibm_watsonx_gov.utils.python_utils import get_authenticator_token

logger = GovSDKLogger.get_logger(__name__)


class SegmentClient():

    def __init__(self, api_client):
        self.api_client = api_client

    async def trigger_segment_endpoint(self, segment_data):
        try:
            segment_publish_url = "{0}/v2/segment/events".format(
                self.api_client.service_url)

            iam_headers = {
                "Content-Type": "application/json",
                "accept": "application/json",
                "Authorization": f"Bearer {get_authenticator_token(self.api_client.authenticator)}"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=segment_publish_url,
                    headers=iam_headers,
                    json=segment_data,
                    ssl=False
                ) as response:
                    text = await response.text()
                    logger.info(
                        f"Segment response: {response.status}, Body: {text}"
                    )
                    return response.status == 202
        except Exception as ex:
            logger.error(f"Failed to send segment events. Details: {ex}")
            return False
