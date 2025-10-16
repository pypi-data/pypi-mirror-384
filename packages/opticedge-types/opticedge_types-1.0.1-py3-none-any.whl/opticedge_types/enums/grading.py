from enum import Enum

class GradingField(Enum):
    GRADING = "grading"
    CENTER  = "centering_grading"
    SURFACE = "surface_grading"
    EDGE    = "edge_grading"
    CORNER  = "corner_grading"
