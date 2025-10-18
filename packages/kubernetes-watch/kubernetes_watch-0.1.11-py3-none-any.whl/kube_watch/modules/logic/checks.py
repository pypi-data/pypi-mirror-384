from prefect import get_run_logger
logger = get_run_logger()

def dicts_has_diff(dict_a, dict_b):
    return dict_a != dict_b


def remove_keys(d, keys):
    return {k: v for k, v in d.items() if k not in keys}


def print_data(data, indicator = None):
    if indicator:
        logger.info(indicator)    
    logger.info(data)