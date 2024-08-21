#!/usr/bin/env python
from psychopy import visual, core, event, data, gui

TEXT_COLOR = "#D5D5D5"
BACKGROUND_COLOR = "#787878"
FONT = 'Arial'
TEXT_SIZE = 60

# setup the experiment window
win = visual.Window(color=BACKGROUND_COLOR, units='pix', pos=(0, 10), fullscr=True)
win.mouseVisible = False
# sliders
fixation_stim = visual.TextStim(win, text='+', height=TEXT_SIZE, color=TEXT_COLOR, languageStyle='RTL', font=FONT, alignText='center')
fixation_stim.draw()
win.flip()
keys = event.waitKeys(keyList = ['escape'])
win.close()
core.quit()