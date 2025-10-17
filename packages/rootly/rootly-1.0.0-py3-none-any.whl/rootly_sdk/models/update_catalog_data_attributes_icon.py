from enum import Enum


class UpdateCatalogDataAttributesIcon(str, Enum):
    CHART_BAR = "chart-bar"
    CURSOR_ARROW_RIPPLE = "cursor-arrow-ripple"
    GLOBE_ALT = "globe-alt"
    LIGHT_BULB = "light-bulb"
    SERVER_STACK = "server-stack"
    SHAPES = "shapes"
    USERS = "users"
    USER_GROUP = "user-group"

    def __str__(self) -> str:
        return str(self.value)
