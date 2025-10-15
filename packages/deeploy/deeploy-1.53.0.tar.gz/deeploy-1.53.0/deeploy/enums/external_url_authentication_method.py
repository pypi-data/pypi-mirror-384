from enum import Enum


class ExternalUrlAuthenticationMethod(Enum):
    """Class that contains external url authentication method"""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    CUSTOM = "custom"
    OAUTH = "oauth"
