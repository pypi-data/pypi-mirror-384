"""Actions associated to different configuration levels (required, advanced and optional)"""

from silx.gui import icons
from silx.gui import qt


class RequiredConfigurationAction(qt.QAction):
    """
    Action to display the 'required' options only
    """

    def __init__(self, parent):
        super().__init__("required options", parent)
        self.__icon = icons.getQIcon("darfix:gui/icons/required_settings")
        self.setIcon(self.__icon)
        self.setIconVisibleInMenu(True)
        self.setCheckable(True)
        self.setToolTip(self.tooltip())

    def tooltip(self):
        return "Show only required options"

    def icon(self):
        return self.__icon

    def text(self):
        return "Required configuration"


class OptionalConfigurationAction(qt.QAction):
    """
    Action to display the 'optional' options only
    """

    def __init__(self, parent):
        super().__init__("optional options", parent)
        self.__icon = icons.getQIcon("darfix:gui/icons/optional_settings")
        self.setIcon(self.__icon)
        self.setIconVisibleInMenu(True)
        self.setCheckable(True)
        self.setToolTip(self.tooltip())

    def tooltip(self):
        return "Show required and optional options. Not any advanced options displayed"

    def icon(self):
        return self.__icon

    def text(self):
        return "Optional configuration"


class AdvancedConfigurationAction(qt.QAction):
    """
    Action to display the 'advanced' / expert options
    """

    def __init__(self, parent):
        super().__init__("advanced options", parent)
        self.__icon = icons.getQIcon("darfix:gui/icons/advanced_settings")
        self.setIcon(self.__icon)
        self.setIconVisibleInMenu(True)
        self.setCheckable(True)
        self.setToolTip(self.tooltip())

    def tooltip(self):
        return "Show all existing options"

    def icon(self):
        return self.__icon

    def text(self):
        return "Advanced configuration"
