from silx.gui import qt


class FitComboBox(qt.QComboBox):
    def __init__(self) -> None:
        super().__init__()
        self.addItems(("trf", "dogbox", "lm"))
        self.setItemData(
            self.findText("trf"),
            "Bounded - Trust Region Reflective algorithm, particularly suitable for large sparse problems with bounds. Generally robust method.",
        )
        self.setItemData(
            self.findText("dogbox"),
            "Bounded - dogleg algorithm with rectangular trust regions, typical use case is small problems with bounds. Not recommended for problems with rank-deficient Jacobian",
        )
        self.setItemData(
            self.findText("lm"),
            "Unbounded Levenberg-Marquardt algorithm as implemented in MINPACK. Doesn’t handle bounds and sparse Jacobians. Usually the most efficient method for small unconstrained problems.",
        )

        self.setCurrentText("lm")
