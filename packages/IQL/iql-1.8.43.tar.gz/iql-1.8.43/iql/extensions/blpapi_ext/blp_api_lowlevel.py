import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Reference: https://data.bloomberglp.com/professional/sites/10/2017/03/BLPAPI-Core-Developer-Guide.pdf

# API Docs (check for latest): https://bloomberg.github.io/blpapi-docs/


def get_blp_api_session(svc_type):
    # defer blpapi load until this is actually used to prevent loading on init
    import blpapi

    session = blpapi.Session()  # type: ignore

    session.start()
    session.openService(svc_type)
    # TODO Validate the session was successful, since in Bquant Enterprise, this will fail.

    return session


def await_response(session):
    import blpapi

    response = []
    msgidx = 0
    while True:
        ev = session.nextEvent(500)
        # for msg in ev:
        #    logging.debug(f"{msgidx=}: {ev.eventType()=}, {msg=}")

        msgidx = msgidx + 1

        if ev.eventType() == blpapi.Event.RESPONSE or ev.eventType() == blpapi.Event.PARTIAL_RESPONSE:  # type: ignore
            for msg in ev:
                response.append(msg)  # pyright: ignore

            if ev.eventType() == blpapi.Event.RESPONSE:  # type: ignore
                break
    return response


def get_mktdata(field_name, equity="IBM US Equity"):
    """Used when subscribing to streaming real-time and delayed market data."""

    raise NotImplementedError("Not Implemented")


def get_user_entitlements(uuid):
    # https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf
    svc_type: str = "//blp/apiauth"
    session = get_blp_api_session(svc_type)
    ref_svc = session.getService(svc_type)
    request = ref_svc.createRequest("UserEntitlementsRequest")

    userinfo = request.getElement("userInfo")  # type: ignore
    userinfo.setElement("uuid", uuid)  # type: ignore

    session.sendRequest(request)

    response = await_response(session)

    # Convert response to a Dict
    results = []
    for e in response:
        e_py = e.toPy()
        results.append(e_py)

    session.stop()
    return results


#  Request request = authSvc.CreateRequest("UserEntitlementsRequest");
# Element userinfo = request.GetElement("userInfo");
# userinfo.SetElement("uuid", 11223344);


param_map = {
    "per": "periodicitySelection",
    "days": "nonTradingDayFillOption",
    "fill": "nonTradingDayFillMethod",
}


def get_refdata(  # noqa: C901
    fields: tuple[str],
    securities: tuple[str] = ("IBM US Equity",),
    historical: bool = False,
    parameters: Optional[dict] = None,  # Really a frozendict
):
    """_summary_
        Typed as tuples for caching.
        Do not call directly, choose the cached or uncached versions
        Example:
            ba.get_refdata(["PX_LAST"], historical=True, parameters = {"startDate": "20230101", "endDate": "20230103"})
    val

        Args:
            fields (list[str]): _description_
            equities (list[str], optional): _description_. Defaults to ['IBM US Equity'].
            historical (bool, optional): _description_. Defaults to False.
            parameters (dict, optional): _description_. Defaults to {}.

        Returns:
            _type_: _description_
    """

    svc_type: str = "//blp/refdata"
    session = get_blp_api_session(svc_type)
    ref_svc = session.getService(svc_type)

    if historical:
        request = ref_svc.createRequest("HistoricalDataRequest")
    else:
        request = ref_svc.createRequest("ReferenceDataRequest")

    for f in fields:
        request.getElement("fields").appendValue(f)  # type: ignore

    for eq in securities:
        request.getElement("securities").appendValue(eq)  # type: ignore

    if parameters:
        for k, v in parameters.items():
            if k in param_map:
                k = param_map[k]
                v = v.upper()

            request.set(k, v)  # type: ignore

    session.sendRequest(request)

    response = await_response(session)

    # Convert response to a Dict
    results = []
    for e in response:
        e_py = e.toPy()
        logger.debug(e_py)
        if "responseError" in e_py:
            # Handle error
            result = {"status": "responseError"}
            result.update(e_py["responseError"])
            results.append(result)
            continue

        # for security_data in e_py["securityData"]:
        security_data = e_py["securityData"]

        if not isinstance(
            security_data, list
        ):  # historical data is a single security data, with a list of field datas. Ref data is a list of security data and a single field data
            security_data = [security_data]

        for security_data_instance in security_data:
            field_data = security_data_instance["fieldData"]

            if not isinstance(field_data, list):
                field_data = [field_data]

            for field_data_instance in field_data:
                result = {
                    "security": security_data_instance["security"],
                    "eid_data": security_data_instance["eidData"],
                    "exceptions": security_data_instance["fieldExceptions"],
                    "sequenceNumber": security_data_instance["sequenceNumber"],
                }
                result.update(field_data_instance)
                results.append(result)

    session.stop()
    return results


def get_field_info(fieldname: Optional[str] = None, search: bool = False):
    """If fieldname is None, returns all available fields"""

    svc_type = "//blp/apiflds"
    session = get_blp_api_session(svc_type)
    fld_svc = session.getService(svc_type)

    if search:
        request = fld_svc.createRequest("FieldSearchRequest")
        request.set("searchSpec", fieldname)  # type: ignore
        request.set("returnFieldDocumentation", True)  # type: ignore
    elif fieldname is None or fieldname in ("All", "Static", "RealTime"):  # All Fields
        request = fld_svc.createRequest("FieldListRequest")
        if not fieldname:
            fieldname = "All"
        request.set("fieldType", fieldname)  # type: ignore
        request.set("returnFieldDocumentation", True)  # type: ignore
    else:  # Individual Field
        request = fld_svc.createRequest("FieldInfoRequest")
        request.append("id", fieldname)  # type: ignore
        request.set("returnFieldDocumentation", True)  # type: ignore

    session.sendRequest(request)
    data = await_response(session)

    results = []

    for e in data:
        e_py = e.toPy()
        logger.debug(e_py)
        field_data = e_py["fieldData"]

        for field_data_instance in field_data:
            fid = field_data_instance["id"]
            field_info = (
                field_data_instance["fieldInfo"]
                if "fieldInfo" in field_data_instance
                else field_data_instance["fieldError"]
            )
            ftype = field_info["ftype"] if "ftype" in field_info else None

            result = {"id": fid, "ftype": ftype}
            result.update(field_info)
            results.append(result)

    session.stop()
    return results
