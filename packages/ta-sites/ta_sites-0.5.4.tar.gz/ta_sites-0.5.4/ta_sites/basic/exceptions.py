import logging


def check_rpaframework_import():
    try:
        import RPA  # noqa
    except ModuleNotFoundError:
        logging.error("rpaframework not installed. Please install the rpaframework first to use this module")
        raise Exception("rpaframework not installed. Please install the rpaframework first to use this module")
