import kivy
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import ListProperty

from kivy.factory import Factory
from kivy.lang import Builder

from kivy.app import App
from kivy.lang import Builder

Builder.load_string("""
<LabelB>:
  bcolor: 1, 1, 1, 1
  canvas.before:
    Color:
      rgba: self.bcolor
    Rectangle:
      pos: self.pos
      size: self.size
""")

class LabelB(Label):
  bcolor = ListProperty([1,1,1,1])

Factory.register('KivyB', module='LabelB')
Builder.load_string("""
<MyGrid>:
  rows: 2
  LabelB:
    bcolor: 1,0,0,1
  LabelB:
    bcolor: 0,1,0,1
""")

class MyGrid(GridLayout):
    pass

class TheApp(App):
    def build(self):
        return MyGrid()

TheApp().run()