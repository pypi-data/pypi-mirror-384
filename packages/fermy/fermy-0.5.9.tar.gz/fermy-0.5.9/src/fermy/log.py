import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO) # logging.WARNING logging.INFO
logger.addHandler(stream_handler)

