from enum import Enum

IMGFLIP_API_URL = "https://api.imgflip.com"


class Font(Enum):
    IMPACT = "impact"
    ARIAL = "arial"
    # Add some popular Google Fonts
    ROBOTO = "roboto"
    OPEN_SANS = "open-sans"
    LATO = "lato"
    MONTSERRAT = "montserrat"
    SOURCE_SANS_PRO = "source-sans-pro"
    UBUNTU = "ubuntu"
    NUNITO = "nunito"
    POPPINS = "poppins"
    INTER = "inter"
    WORK_SANS = "work-sans"


AVAILABLE_FONTS = [font.value for font in Font]


DEFAULT_FONT = Font.IMPACT.value
