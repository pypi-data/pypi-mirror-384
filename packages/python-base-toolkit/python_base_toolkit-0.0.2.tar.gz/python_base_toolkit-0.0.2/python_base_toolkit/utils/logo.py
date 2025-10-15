from pyfiglet import Figlet


def create_logo(text: str, font: str = "big") -> str:
    f = Figlet(font=font)
    return f.renderText(text)
