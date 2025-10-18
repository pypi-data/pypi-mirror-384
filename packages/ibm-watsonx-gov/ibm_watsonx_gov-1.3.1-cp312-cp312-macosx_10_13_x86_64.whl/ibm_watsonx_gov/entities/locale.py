# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------


from pydantic import BaseModel


class Locale(BaseModel):
    input: list[str] | dict[str, str] | str | None = None
    output: list[str] | None = None
    reference: list[str] | dict[str, str] | str | None = None
