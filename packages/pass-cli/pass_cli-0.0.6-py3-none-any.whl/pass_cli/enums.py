from enum import Enum


class Part(Enum):
    HEADER = 'header'
    BODY = 'body'
    FOOTER = 'footer'


class Mode(Enum):
    BASE = {
        'name': 'base',
        'header': '[N]',
        'frame': Part.BODY.value
    }
    COMMAND = {
        'name': 'command',
        'header': '[C]',
        'frame': Part.FOOTER.value
    }
