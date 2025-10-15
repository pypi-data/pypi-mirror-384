from ewokscore import Task


class MetadataTask(
    Task,
    input_names=[
        "dataset",
    ],
):
    """
    'Place holder' task for the MetadataWidgetOW.
    This widget only does display of information an no processing.
    But having this task allow use to have it compatible with ewoks.
    """

    def run(self):
        pass
