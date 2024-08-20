#!/usr/bin/env python
import random
import os
import numpy as np 
import pandas as pd
from psychopy import visual, core, event, data, gui
from copy import deepcopy
import argparse
import PIL
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

TEXT_COLOR = "#D5D5D5"
BACKGROUND_COLOR = "#1C1C1C"
FONT = 'Arial'
MAX_WTP = 80
N_TRIALS = 3
TEXT_SIZE = 40
SLIDER_WIDTH = 500
WINDOW_WIDTH = 2048
WINDOW_HEIGHT = 968
WRAP_WITDH = round(WINDOW_WIDTH*0.8)
TEXT_STIM_KWARGS = {'height':TEXT_SIZE, 
                    'wrapWidth':WRAP_WITDH, 
                    'color':TEXT_COLOR, 
                    'languageStyle':'RTL',
                    'font':FONT}
FIXATION_TIME = 0.2
JITTER_FIXATION = 0.2
INITAL_FIXATION_TIME = 0.5
SLIDER_DELAY = 1
MAX_DURATION = 1
SOA = 0.5
CLOCK = core.Clock()
MAX_IMAGE_WIDTH = 250
MAX_IMAGE_HEIGHT = 250

def resize_image(image_path):
    img = PIL.Image.open(image_path)
    width, height = img.size
    ratio = np.max([width / MAX_IMAGE_WIDTH, height / MAX_IMAGE_HEIGHT])
    new_width = int(width / ratio)
    new_height = int(height / ratio)
    return new_width, new_height

def display_instructions(mouse, win, instruction, headline=None):
    while True:
        mouse.clickReset()
        if headline is not None:
            headline.draw()
        instruction.draw()
        win.flip()
        keys = event.getKeys()
        space_pressed = 'space' in keys
        mouse_clicked = mouse.getPressed()[0]
        if mouse_clicked or space_pressed:
            break

def normalize_mouse_loc(mouse_loc):
    norm_loc = int(np.round(MAX_WTP * (mouse_loc + SLIDER_WIDTH/2) / SLIDER_WIDTH, 0))
    return norm_loc

def reverse_normalize_mouse_loc(norm_loc):
    reverse_loc = norm_loc * SLIDER_WIDTH / MAX_WTP - SLIDER_WIDTH/2 
    return reverse_loc

def display_slider(mouse, win, slider, product, instructions=None, delay=True, is_demo_trial=False, trials=None):
    if instructions is not None:
        instructions.draw()
    # save time of presenting the stimuli
    view_time = CLOCK.getTime()
    if delay:
        core.wait(SLIDER_DELAY)
    # set random start of slider
    rand_x = random.randint(-1*SLIDER_WIDTH/2, SLIDER_WIDTH/2)
    mouse.setPos((rand_x, 0))
    mouse_random_start = int(np.round(MAX_WTP * (rand_x + SLIDER_WIDTH/2) / SLIDER_WIDTH, 0))
    mouse_random_start = MAX_WTP if mouse_random_start > MAX_WTP else mouse_random_start
    mouse_random_start = 0 if mouse_random_start < 0 else mouse_random_start
    mouse.mouseClock.reset()
    mouse.clickReset()
    first_slider_time = None
    rt = None
    while is_demo_trial or (mouse.mouseClock.getTime() < MAX_DURATION):
        if instructions is not None:
            instructions.draw()
        product.draw()
        slider.draw()
        mouse_loc = mouse.getPos()[0]
        # normalize mouse location
        mouse_loc = normalize_mouse_loc(mouse_loc)
        # bound mouse location
        if mouse_loc > MAX_WTP:
            mouse_loc = MAX_WTP
            max_mouse_pos = reverse_normalize_mouse_loc(mouse_loc)
            mouse.setPos((max_mouse_pos, 0))
        if mouse_loc < 0:
            mouse_loc = 0
            min_mouse_pos = reverse_normalize_mouse_loc(mouse_loc)
            mouse.setPos((min_mouse_pos, 0))
        # draw mouse location
        choice_text = f"מוכנים לשלם: ₪{mouse_loc}"
        choice_pos = slider.pos + (0, 50)
        choice_stim = visual.TextStim(win, text=choice_text, height=0.8*TEXT_SIZE, pos=choice_pos, color=TEXT_COLOR, languageStyle='RTL', font=FONT)
        choice_stim.draw()
        slider.markerPos = mouse_loc 
        win.flip()
        # save time of presenting the slider
        if (trials is not None) and (first_slider_time is None):
            first_slider_time = CLOCK.getTime()
        # Break the loop if a value is selected from the slider
        all_clicks, all_times = mouse.getPressed(getTime=True)
        mouse_click, mouse_time_clicked = all_clicks[0], all_times[0]
        keys = event.getKeys()
        if 'p' in keys:
            event.waitKeys(keyList=['p'])
        if 'escape' in keys:
            core.quit()
        if mouse_click:
            rt = mouse_time_clicked
            break
    # if no response
    end_time = CLOCK.getTime()
    trial_data_dict = {
                'view_time':view_time,
                'slider_time':first_slider_time,
                'end_time':end_time,
                'rt':rt,
                'choice':mouse_loc,
                'mouse_start':mouse_random_start,
                'image_path':product.image
                }
    return trial_data_dict

def save_trial_data(data_dict, trials):
    for key, value in data_dict.items():
        trials.addData(key, value)
    return trials

def display_fixation(win, initial=False, fixation_time=FIXATION_TIME, trials=None):
    fixation_stim = visual.TextStim(win, text='+', height=TEXT_SIZE, wrapWidth=WRAP_WITDH, color=TEXT_COLOR, languageStyle='RTL', font=FONT, alignText='center')
    fixation_stim.draw()
    win.flip()
    keys = event.getKeys()
    if initial:
        core.wait(INITAL_FIXATION_TIME)
    else:
        random_jitter = random.uniform(-1*JITTER_FIXATION, JITTER_FIXATION)
        wait_time = fixation_time + random_jitter
        core.wait(wait_time)
        return wait_time

def display_blank(win, trials):
    win.flip()
    view_time = CLOCK.getTime()
    rt = None
    core.wait(MAX_DURATION+SLIDER_DELAY)
    end_time = CLOCK.getTime()
    blank_trial_dict = {
                'view_time':view_time,
                'slider_time':None,
                'end_time':end_time,
                'rt':rt,
                'choice':None,
                'mouse_start':None
                }
    return blank_trial_dict

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--instructions', dest='instructions', action='store_true')
    parser.add_argument('-b', '--block', type=int, help='block number (1-5)', dest='block_num')
    parser.add_argument('-s', '--subject', type=str, help='subject number', dest='subject_num')
    args = parser.parse_args()
    # setup the experiment window
    win = visual.Window([WINDOW_WIDTH, WINDOW_HEIGHT], color=BACKGROUND_COLOR, units='pix', pos=(0, 10), fullscr=True)
    # win = visual.Window([1920, 1080], color=BACKGROUND_COLOR, units='pix', fullscr=True)
    win.mouseVisible = False
    # sliders
    slider_ticks = np.arange(0, MAX_WTP+20, 20)
    slider_labels = [f"{i}" for i in slider_ticks]
    slider_kwargs = {
        'win':win,
        'size':(SLIDER_WIDTH, 30),
        'style':'slider',
        'granularity':1,
        'flip':False,
        'ticks':slider_ticks,
        'markerColor':TEXT_COLOR,
        'labels':slider_labels,
        'color':TEXT_COLOR,
        'labelColor':TEXT_COLOR,
        'labelHeight':int(0.5*TEXT_SIZE),
        'font':FONT
    }
    slider_example1 = visual.Slider(pos=np.array([0, -300]), **slider_kwargs)
    slider_example2 = visual.Slider(pos=np.array([0, -150]), **slider_kwargs)
    slider = visual.Slider(pos=np.array([0, -100]), **slider_kwargs)
    # mouse
    mouse = event.Mouse(win=win, visible=False)
    _thisDir = os.getcwd()
    if args.instructions:
        CLOCK.reset()
        # welcome
        welcome_headline = '''שלום וברוכים הבאים!'''
        welcome_headline_stim = visual.TextStim(win, text=welcome_headline, pos=(0, 120), height=1.2*TEXT_SIZE, wrapWidth=WRAP_WITDH, 
                                                    color=TEXT_COLOR, languageStyle='RTL', font=FONT, alignText='center', bold=True)
        instruction_text = '''
לפניכם ניסוי בקבלת החלטות.
לחצו על העכבר כדי להמשיך.'''
        instruction_stim = visual.TextStim(win, instruction_text, pos=(0, -50), alignText='center', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, instruction_stim, headline=welcome_headline_stim)
        core.wait(0.7)

        # instrcutions
        instruction_2_headline = '''הוראות'''
        instruction_2_headline_stim = visual.TextStim(win, text=instruction_2_headline, pos=(0, 120), height=1.2*TEXT_SIZE, wrapWidth=WRAP_WITDH, 
                                                    color=TEXT_COLOR, languageStyle='RTL', font=FONT, alignText='center', bold=True)
        instruction_2_text = '''בקרוב יוצגו בפניכם הגרלות.
עליכם לבחור את המחיר המירבי שתהיו מוכנים לשלם כדי להשתתף בהגרלה שתוצג.
יש לכם תקציב של ₪80 לכל הגרלה. 

נסו להעריך כל הגרלה בנפרד ולחשוב כמה היא שווה עבורכם. ₪80 זמינים לכל הגרלה בנפרד.

לחצו על העכבר כדי להמשיך.'''
        instruction_2_stim = visual.TextStim(win, text=instruction_2_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, instruction_2_stim, instruction_2_headline_stim)
        core.wait(0.7)

        instruction_3_text = '''בסוף הניסוי, המחשב יבחר את אחת ההגרלות ויקבע מחיר לכרטיס עבורה.

אם המחיר שבחרתם נמוך מהמחיר שנקבע על ידי המחשב, 
לא תשתתפו בהגרלה ותישארו עם כל התקציב.
אם המחיר שבחרתם גבוה מהמחיר שנקבע על ידי המחשב,
תשלמו את המחיר שנקבע ותשתתפו בהגרלה.

לחצו על העכבר כדי להמשיך.'''
        instruction_3_stim = visual.TextStim(win, text=instruction_3_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, instruction_3_stim)
        core.wait(0.7)

        # BDM example 1
        example_1_text = f'''נתחיל עם דוגמא:
ההגרלה מטה מציעה 65% סיכוי לזכות ב-₪40 ו-35% סיכוי לזכות ב-₪0.

מה המחיר המירבי שתהיו מוכנים לשלם על כרטיס להגרלה זו בין 0 ל-₪{MAX_WTP}?
הזיזו את העכבר על פני המלבן ולחצו כדי לבצע בחירה.'''
        example_1_stim = visual.TextStim(win, text=example_1_text, pos=(0, 100), alignText='right', **TEXT_STIM_KWARGS)
        example_amount = visual.TextStim(win, text=f"₪40", height=TEXT_SIZE, pos=slider_example1.pos+(0, 150), color=TEXT_COLOR)
        example_prob = visual.TextStim(win, text=f"65%", height=TEXT_SIZE, pos=slider_example1.pos+(0, 100), color=TEXT_COLOR)
        event.Mouse(visible=False)
        trial_data_dict = display_slider(mouse, win, slider_example1, example_amount, example_prob, instructions=example_1_stim, delay=False, is_demo_trial=True)
        example_1_choice = trial_data_dict['choice']
        core.wait(0.7)
        ##
        example_1_feedback_text = f'''יפה מאוד!
בחרתם שתהיו מוכנים לשלם ₪{example_1_choice} כדי להשתתף בהגרלה. נשמע נכון?

כעת נניח שהגרלה זו נבחרה בסוף הניסוי.
המחשב יקבע מחיר עבורה באקראי.

לחצו על העכבר להמשך.'''
        example_1_feedback_stim = visual.TextStim(win, text=example_1_feedback_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, example_1_feedback_stim)
        core.wait(0.7)
        ##
        random_price = random.randint(0, example_1_choice)

        if random_price == example_1_choice:
            example_1_lower_or_equal = f'''המחיר שנקבע זהה לזה שבחרתם, אז תשלמו את המחיר שקבע המחשב (₪{random_price}) ותשתתפו בהגרלה.'''
        else:
            example_1_lower_or_equal = f'''המחיר שנקבע נמוך מזה שבחרתם, אז תשלמו את המחיר שקבע המחשב (₪{random_price}) ותשתתפו בהגרלה.'''

        example_1_price_text = f'''המחשב קבע מחיר: ₪{random_price}
ואתם בחרתם לשלם לכל היותר: ₪{example_1_choice}

''' + example_1_lower_or_equal + f'''
במקרה כזה, תסיימו את הניסוי עם תקציב של ₪{80 - random_price} ועם סיכוי לזכות ב-₪40 נוספים מההגרלה.
כלומר, תוכלו לקבל ₪{80 - random_price} אם לא תזכו בהגרלה, או ₪{80 - random_price + 40} אם תזכו בהגרלה.

לחצו על העכבר להמשך.'''
        example_1_price_stim = visual.TextStim(win, text=example_1_price_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, example_1_price_stim)
        core.wait(0.7)
        # BDM example 2
        example_2_text = f'''הנה עוד דוגמא:
ההגרלה מטה מציעה 35% סיכוי לזכות ב-₪18, ו-65% סיכוי לזכות ב-₪0.'''
        example_2_stim = visual.TextStim(win, text=example_2_text, pos=(0, 100), alignText='right', **TEXT_STIM_KWARGS)
        example_amount = visual.TextStim(win, text=f"₪18", height=TEXT_SIZE, pos=slider_example2.pos+(0, 150), color=TEXT_COLOR)
        example_prob = visual.TextStim(win, text=f"35%", height=TEXT_SIZE, pos=slider_example2.pos+(0, 100), color=TEXT_COLOR)
        trial_data_dict = display_slider(mouse, win, slider_example2, example_amount, example_prob, example_2_stim, is_demo_trial=True, delay=False)
        example_2_choice = trial_data_dict['choice']
        core.wait(0.7)
        ##
        example_2_feedback_text = f'''בחרתם שתהיו מוכנים לשלם ₪{example_2_choice} כדי להשתתף בהגרלה.

נניח שהגרלה זו נבחרה בסוף הניסוי.
כעת המחשב יקבע עבורה מחיר באקראי.

לחצו על העכבר להמשך.'''
        example_2_feedback_stim = visual.TextStim(win, text=example_2_feedback_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, example_2_feedback_stim)
        core.wait(0.7)
        ##
        random_price = random.randint(example_2_choice+1, MAX_WTP)
        example_2_price_text = f'''המחשב קבע מחיר: ₪{random_price}
ואתם בחרתם לשלם לכל היותר: ₪{example_2_choice}

מכיוון שהמחיר שבחרתם נמוך מהמחיר שנקבע, לא תשתתפו בהגרלה.
במקרה כזה, בסוף הניסוי תקבלו את כל התקציב ההתחלתי של ₪80.

לחצו על העכבר להמשך.'''
        example_2_price_stim = visual.TextStim(win, text=example_2_price_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, example_2_price_stim)
        core.wait(0.7)

        # BDM example 3 - with time limit
        example_3_text = f'''במהלך הניסוי, קודם תראו את ההגרלה ורק לאחר מכן תוכלו לבחור.
כמו כן, יהיו לכם מספר שניות מוגבל להגיב.
בואו נראה איך זה נראה.

לחצו על העכבר כדי להתחיל באימון.'''
        example_3_stim = visual.TextStim(win, text=example_3_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, example_3_stim)
        core.wait(0.7)
        #
        example_amount = visual.TextStim(win, text=f"₪21", height=TEXT_SIZE, pos=slider.pos+(0, 150), color=TEXT_COLOR)
        example_prob = visual.TextStim(win, text=f"65%", height=TEXT_SIZE, pos=slider.pos+(0, 100), color=TEXT_COLOR)
        display_fixation(win)
        trial_data_dict = display_slider(mouse, win, slider, example_amount, example_prob)
        example_3_choice = trial_data_dict['choice']
        example_3_rt = trial_data_dict['rt']
        core.wait(0.7)

        if example_3_rt is None:
            example_3_feedback_text = f'''לא הגבתם בזמן המוקצב לתגובה. 
נסו להגיב מהר יותר בפעם הבאה!

לחצו על העכבר כדי להמשיך באימון.'''
        else:
            example_3_feedback_text = f'''יפה. הפעם בחרתם לשלם לכל היותר ₪{example_3_choice}.
לחצו על העכבר כדי להמשיך באימון.'''
        example_3_feedback_stim = visual.TextStim(win, text=example_3_feedback_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, example_3_feedback_stim)
        core.wait(0.7)    

        # examples 4-8
        amounts = [60, 14, 35, 74, 27]
        probs = [20, 75, 55, 45, 15]
        conditions = data.importConditions(_thisDir + os.sep + '../stimuli.csv')
        trials = data.TrialHandler(trialList=conditions, nReps=1)
        TEXT_SIZE = 60
        SLIDER_WIDTH = 600
        product = visual.ImageStim(win, pos=slider.pos+(0, 120))
        choices = np.zeros(len(amounts))
        rts = np.zeros(len(amounts))
        for trial in trials:
            display_fixation(win, initial=True)
            product_path = trial['image']
            product_new_size = resize_image(product_path)
            product.setImage(product_path, size=product_new_size)
            trial_data_dict = display_slider(mouse, win, slider, product, trials=trials)
            trials = save_trial_data(trial_data_dict, trials)
            trial_rt = trial_data_dict['rt']
            if trial_rt is None:
                fixation_time = SOA - MAX_DURATION
            else:
                fixation_time = SOA - trial_rt
            wait_time = display_fixation(win, initial=False, fixation_time=fixation_time, trials=trials)
            trials.addData('wait_time', wait_time)
        trials.saveAsWideText(f'data/instruction_results.csv', delim=',', appendFile=False)
        print(trials.data['rt'])
        # pre-start
        end_practice = f'''סיימתם את האימון!

כעת נתחיל את הניסוי.
אתם תראו הגרלות ותתבקשו לבחור כמה תהיו מוכנים לשלם כדי להשתתף בהן.
יש לכם תקציב של ₪80 עבור כל הגרלה.
בסוף הניסוי הגרלה אחת תבחר באקראי ותשוחק.

לחצו על העכבר כדי להתחיל את הניסוי.'''
        end_practice_stim = visual.TextStim(win, text=end_practice, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
        display_instructions(mouse, win, end_practice_stim)
        core.wait(0.7)

    elif (args.block_num>=1) & (args.block_num<=5):
        TEXT_SIZE = 60
        SLIDER_WIDTH = 600
        conditions = data.importConditions(_thisDir + os.sep + 'stimuli.csv')
        trials = data.TrialHandler(trialList=conditions, nReps=1, method='random')
        expInfo = {
            'participant': args.subject_num,
            'block': args.block_num,
        }
        exp_name = 'neuro_DN'
        expInfo['date'] = data.getDateStr()  # add a simple timestamp
        expInfo['expName'] = exp_name
        filename = _thisDir + os.sep + f"data/{exp_name}_{expInfo['participant']}_{expInfo['block']}"
        os.chdir(_thisDir)
        # wait for scanner
        pre_start_text = f'''מיד מתחילים.'''
        pre_start_stim = visual.TextStim(win, text=pre_start_text, pos=(0, 0), alignText='center', height=TEXT_SIZE, 
                                         wrapWidth=WRAP_WITDH, color=TEXT_COLOR, languageStyle='RTL', font=FONT)
        pre_start_stim.draw()
        win.flip()
        keys = event.waitKeys(keyList = ['t', '5'])

        choices = np.zeros(len(conditions))
        rts = np.zeros(len(conditions))
        product = visual.ImageStim(win, pos=slider.pos+(0, 250))
        CLOCK.reset()
        i = 0
        display_fixation(win, initial=True)
        for trial in trials:
            product_path = trial['image']
            product_new_size = resize_image(product_path)
            product.setImage(product_path)
            product.setSize(product_new_size)
            trial_data_dict = display_slider(mouse, win, slider, product, trials=trials)
            trials = save_trial_data(trial_data_dict, trials)
            trial_rt = trial_data_dict['rt']
            if trial_rt is None:
                fixation_time = SOA - MAX_DURATION
            else:
                fixation_time = SOA - trial_rt
            wait_time = display_fixation(win, initial=False, fixation_time=fixation_time, trials=trials)
            trials.addData('wait_time', wait_time)
            i += 1
        num_missed = np.sum(pd.isna(trials.data['rt']))
        print(f'Missed: {num_missed}')
        trials.saveAsWideText(filename+'.csv', delim=',', appendFile=False)

        # analyze subject's choices and create csv for fMRI
        analyzed_data = pd.DataFrame({'image':trials.data['image_path'], 'choice':trials.data['choice']})
        # sort product by choice
        analyzed_data.sort_values(by='choice', ascending=False, inplace=True)
        # take top 10 to be targets
        targets_1 = analyzed_data.iloc[:10:2]
        targets_2 = analyzed_data.iloc[1:10:2]
        # take next 20 to be distractors
        distractors = analyzed_data.iloc[10:20:2]
        stimuli_df = pd.DataFrame({'target1':targets_1.image_path.values, 'target1_rating':targets_1.choice.values,
                                   'target2':targets_2.image_path.values, 'target2_rating':targets_2.choice.values,
                                   'distracter':distractors.image_path.values, 'distracter_rating':distractors.choice.values})
        stimuli_df.to_csv(filename+'_fMRI.csv', index=False)

        if args.block_num != 5:
            end_text = f'''נגמר הבלוק.'''
        else:
            end_text = f'''כל הכבוד! סיימתם את החלק הזה.'''
        end_text_stim = visual.TextStim(win, text=end_text, pos=(0, -50), alignText='center', **TEXT_STIM_KWARGS)
        end_text_stim.draw()
        win.flip()
        keys = event.waitKeys(keyList = ['space', 'enter', 'escape'])
    # Close the window
    win.close()
    core.quit()
