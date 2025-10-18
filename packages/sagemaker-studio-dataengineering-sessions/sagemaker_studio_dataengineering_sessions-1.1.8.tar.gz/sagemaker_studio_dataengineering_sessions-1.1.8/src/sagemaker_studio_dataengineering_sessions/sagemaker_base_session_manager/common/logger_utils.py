import logging
import os


class SessionManagerFileHandler(logging.FileHandler):
    def __init__(self, **kwargs):
        file_name = kwargs.pop("file_name")
        log_path = "/var/log/apps"
        log_filename = "{0}/{1}.log".format(log_path, file_name)
        try:
            os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        except:
            log_filename = "/tmp" + log_filename
            os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        super(SessionManagerFileHandler, self).__init__(
            filename=log_filename, **kwargs
        )


def setup_logger(logger, name, file_name, level=logging.INFO):
    logger.name = name
    logger.setLevel(level)

    logger.propagate = True
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = SessionManagerFileHandler(file_name=file_name)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
