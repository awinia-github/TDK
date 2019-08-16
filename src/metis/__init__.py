import os

if 'METIS' not in os.environ:
    raise ImportError("Set the 'METIS' environment variable in order to be able to use this module")

from metis.utils.lot_based_inquiries import get_lots
