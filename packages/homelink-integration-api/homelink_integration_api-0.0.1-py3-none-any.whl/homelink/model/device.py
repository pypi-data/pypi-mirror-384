from homelink.model.button import Button


class Device:

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.buttons = []
