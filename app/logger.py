import logging


class Logger:
    @classmethod
    def get(cls, name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s : %(levelname)s : %(name)s : %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger
