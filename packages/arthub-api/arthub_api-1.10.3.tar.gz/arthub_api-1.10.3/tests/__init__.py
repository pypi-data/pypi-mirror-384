import arthub_api.__main__
import logging
arthub_api.__main__.setup_logging()
arthub_api.__main__.init_config()

logging.info("[TEST][INIT] Pytest has been initialized")
