# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import pandas as pd
from typing import Dict
from ibm_watsonx_gov.entities.metric import Mapping


def mapping_to_df(mapping: Mapping, mapping_data: Dict) -> pd.DataFrame:
    """
    Convert mapping configuration and mapping data into a pandas DataFrame.
    """
    row = {}
    for item in mapping.items:
        try:
            row[item.name] = mapping_data[item.span_name][item.attribute_name][item.json_path]
        except KeyError:
            row[item.name] = None  # missing key
    return pd.DataFrame([row])
