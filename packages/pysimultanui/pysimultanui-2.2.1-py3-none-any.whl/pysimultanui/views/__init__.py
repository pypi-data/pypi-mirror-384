import logging

logger = logging.getLogger('py_simultan_ui')

c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)

logger.addHandler(c_handler)
logger.setLevel('DEBUG')
