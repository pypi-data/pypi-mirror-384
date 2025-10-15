from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread

from darfix.tasks.copy import DataCopy


class DataCopyWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=DataCopy):
    """
    Widget that creates a new dataset from a given one, and copies its data.
    """

    name = "data copy"
    icon = "icons/copy.svg"
    want_main_area = False
