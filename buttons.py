# buttons
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.properties import StringProperty

class TestButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super(TestButton, self).__init__(**kwargs)
        #self.text = "test"
    def on_press(self):
        self.background_color = (1, 1, 1, 1)
        self.font_color = (0, 0, 0, 1)
    def on_release(self):
        self.background_color = (0, 0, 0, 0)
        self.font_color = (1, 1, 1, 1)

class ExitButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super(ExitButton, self).__init__(**kwargs)
        image = StringProperty()
    def on_press(self):
        self.background_color = (1,1,1,0.5)#(0.145, 0.243, 0.455, 1)
    def on_release(self):
        self.background_color = (1,1,1,1)#(0.078, 0.129, 0.239, 0)

class EscapeButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super(EscapeButton, self).__init__(**kwargs)
        #self.min_state_time = 3
    def on_press(self):
        self.line_color = (1,1,1,0.5)
    def on_release(self):
        self.line_color = (0,0,0,0)

class InfoButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super(InfoButton, self).__init__(**kwargs)
        #self.text = "test"
        image = StringProperty()
    def on_press(self):
        self.background_color = (1,1,1,0.5)#(0.145, 0.243, 0.455, 1)
    def on_release(self):
        self.background_color = (1,1,1,1)#(0.078, 0.129, 0.239, 1)

class BigButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super(BigButton, self).__init__(**kwargs)
        #self.text = "test"
    def on_press(self):
        self.background_color = (0.988, 0.639, 0.067, 0.5)#(1, 1, 1, 1)
    def on_release(self):
        self.background_color = (0.988, 0.639, 0.067, 1)

class MainButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super(MainButton, self).__init__(**kwargs)
        #self.text = "test"
    def on_press(self):
        self.background_color = (0.898, 0.898, 0.898, 0.5)#(0.988, 0.639, 0.067, 1)
    def on_release(self):
        self.background_color = (0.898, 0.898, 0.898, 1)