import logging
import threading
import time
from typing import Optional

import bql  # type: ignore - not available unless using simulator (dev) or in Bqnt

logger = logging.getLogger(__name__)

_BQSERVICE: Optional[bql.Service] = None

_BPSESSION = None
BQL_LOCK = threading.Lock()  # Prevent concurrent

BQSERVICE_TIMEOUT = 120
BQSERVICE_NEEDED_RETRY = False


def get_bqapi_session():
    global _BPSESSION
    if _BPSESSION is not None:
        return _BPSESSION
    with BQL_LOCK:
        # make sure we didn't create it after acquiring lock
        if _BPSESSION is not None:
            return _BPSESSION
        import bqapi as bp  # pyright: ignore

        _BPSESSION = bp.get_session_singleton()
        return _BPSESSION


class BqServiceRetriever(threading.Thread):
    service = None

    def run(self):
        self.service = bql.Service()


def get_bqservice(retries: int = 3) -> bql.Service:
    global _BQSERVICE
    global BQSERVICE_NEEDED_RETRY

    try:
        if _BQSERVICE is None:  # type: ignore
            logger.debug("Creating new bqService")

            start_time = time.time()

            retriever_thread = BqServiceRetriever()
            retriever_thread.start()
            retriever_thread.join(timeout=BQSERVICE_TIMEOUT)
            if retriever_thread.is_alive():
                raise TimeoutError(f"Unable to get bqservice in {BQSERVICE_TIMEOUT}")
            _BQSERVICE = retriever_thread.service

            end_time = time.time()
            duration = end_time - start_time
            logger.debug("Creating new bqService took %s seconds", round(duration))

    except Exception as e:
        logger.exception("Unable to create bq service")
        if retries <= 0:
            raise e

    if _BQSERVICE is None:
        if retries > 0:
            BQSERVICE_NEEDED_RETRY = True
            logger.warning("Retry get bqservice (retries left %s)", retries)
            return get_bqservice(retries - 1)
        raise ValueError("Unable to obtain bql.Service()")
    return _BQSERVICE


def close_bqservice():
    """Closing the session is not normally needed, but there is a limit on the number of concurrent connections.
    BQL uses (as far as we can tell) a Singleton so multiple bql sessions requests will not consume more connections.
    """
    try:
        global _BQSERVICE
        if _BQSERVICE is None or _BQSERVICE._Service__bqapi_session is None:  # type: ignore
            logger.debug("_Service__bqapi_session already closed or None")
            return
        else:
            logger.debug("Closing _Service__bqapi_session session")
            _BQSERVICE._Service__bqapi_session.close()  # type: ignore
            _BQSERVICE = None
    except Exception:
        logger.exception("Error closing bqapi session")
