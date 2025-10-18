#color_ur_text
## A python library that provides various methods to stylize you terminal based apps or programs, like terminal coloring, GUI features like spinner, progress bar and animations like rainbow wave, typewriter etc anf many more feaures. 
## Note: Some terminal might not support the various color codes

# Installation
## You can install the module via pip using `pip install color_ur_text`

# Usage
```python
from color_ur_text import ColoredText as ct

ct.print_colored("Hello, World", ct.RED) prints Hello, World in RED
print(ct.rgb("Hello, World!", 255, 255, 0)) #prints Hello, World! in Yellow
print(ct.table("Hello")) #prints Hello in a box
#animations
ct.animate_text("WAVE ANIMATION", animation_type='rainbow_wave', speed=0.03, cycles=1)
#spinner
ColoredText.spinner("Loading data", duration=2.0, spinner_style='dots', color=(255, 0, 255))
```
