import os

import requests
import uvicorn

from jarvis.executors import port_handler
from jarvis.modules.builtin_overrides import APIServer
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import APIConfig, logger, multiprocessing_logger
from jarvis.modules.models import models


def jarvis_api() -> None:
    """Initiates the fast API in a dedicated process using uvicorn server.

    See Also:
        - Checks if the port is being used. If so, makes a ``GET`` request to the endpoint.
        - Attempts to kill the process listening to the port, if the endpoint doesn't respond.
    """
    multiprocessing_logger(filename=APIConfig().DEFAULT_LOG_FILENAME)
    url = f"http://{models.env.offline_host}:{models.env.offline_port}"

    if port_handler.is_port_in_use(port=models.env.offline_port):
        logger.info("%d is currently in use.", models.env.offline_port)

        try:
            res = requests.get(url=url, timeout=1)
            if res.ok:
                logger.info("'%s' is accessible.", url)
                return
            raise requests.ConnectionError
        except EgressErrors:
            logger.error("Unable to connect to existing uvicorn server.")

        # This might terminate Jarvis
        if not port_handler.kill_port_pid(port=models.env.offline_port):
            logger.critical(
                "ATTENTION::Failed to kill existing PID. Attempting to re-create session."
            )

    # Uvicorn config supports the module as a value for the arg 'app' which can be from relative imports
    # However, in this case, using relative imports will mess with the logger since it is shared across multiple process
    assert os.path.exists(
        os.path.join(os.path.dirname(__file__), "main.py")
    ), "API path has either been modified or unreachable."
    argument_dict = {
        "app": "jarvis.api.main:app",
        "host": models.env.offline_host,
        "port": models.env.offline_port,
        "ws_ping_interval": 20.0,
        "ws_ping_timeout": 20.0,
        "workers": models.env.workers,
    }

    logger.debug(argument_dict)
    logger.info(
        "Starting FastAPI on Uvicorn server with %d workers.", models.env.workers
    )

    server_conf = uvicorn.Config(**argument_dict)
    APIServer(config=server_conf).run_in_parallel()
