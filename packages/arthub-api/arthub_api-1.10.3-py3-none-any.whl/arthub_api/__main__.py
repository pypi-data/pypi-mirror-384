import os
import logging
import logging.handlers
from . import arthub_api_config
from . import cli
from . import utils


def load_config(file_path=None):
    UserError = type("UserError", (Exception,), {})

    file_path = file_path or os.getenv("ARTHUB_API_CONFIG",
                                       os.path.expanduser("~/Documents/ArtHub/arthub_api_config.py"))
    if not os.path.isfile(file_path):
        return

    mod = {
        "__file__": file_path,
    }

    try:
        with open(file_path) as file_obj:
            exec(compile(file_obj.read(), file_obj.name, "exec"), mod)
    except IOError:
        raise

    except Exception:
        raise UserError("Better double-check your user config.")

    for key in dir(arthub_api_config):
        if key.startswith("__"):
            continue

        try:
            value = mod[key]
        except KeyError:
            continue
        setattr(arthub_api_config, key, value)

    return file_path


def patch_config():
    for member in dir(arthub_api_config):
        if member.startswith("__"):
            continue

        setattr(arthub_api_config, "_%s" % member,
                getattr(arthub_api_config, member))


def setup_logging(log_level=logging.INFO):
    logger = utils.logger
    logger.setLevel(log_level)

    # to file
    log_dir = os.path.expanduser("~/Documents/ArtHub/sdk_log")
    if utils.mkdir(log_dir):
        f_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(log_dir, "arthub_api.log"),
                                                              when='midnight', interval=1,
                                                              backupCount=7)
        f_handler.setLevel(log_level)
        f_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d] - %(message)s"))
        logger.addHandler(f_handler)

    # to stdout
    s_handler = logging.StreamHandler()
    s_handler.setLevel(log_level)
    s_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(s_handler)


def apply_environ_to_config():
    """This loads config from env and set into arthub_api_config."""

    value = os.environ.get("AH_API_CONFIG_NAME")
    if value:
        arthub_api_config.api_config_name = value
    value = os.environ.get("AH_BLADE_PUBLIC_TOKEN")
    if value:
        arthub_api_config.blade_public_token = value
    value = os.environ.get("AH_ACCOUNT_NAME")
    if value:
        arthub_api_config.account_email = value
    value = os.environ.get("AH_PASSWORD")
    if value:
        arthub_api_config.password = value
    value = os.environ.get("AH_LOG_LEVEL", "INFO")
    if value:
        arthub_api_config.log_level = value


def init_config():
    patch_config()
    load_config()
    apply_environ_to_config()


def main():
    init_config()
    setup_logging(arthub_api_config.log_level)
    cli.cli()


if __name__ == '__main__':
    main()
