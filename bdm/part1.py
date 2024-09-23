#!/usr/bin/env python
import random
import glob
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
MAX_WTP = 100
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
# no time limit
MAX_DURATION = None
SOA = 0.2
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

def create_product_object(product, product_path):
    product_new_size = resize_image(product_path)
    product.setImage(product_path)
    product.setSize(product_new_size)
    return product

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

def display_slider(mouse, win, slider, product, instructions=None, delay=True, is_demo_trial=False, trials=None, block_num=0):
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
    while True:
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
        choice_text = f"מוכנים לשלם: {mouse_loc}"
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
                'image_path':product.image,
                'block':block_num
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
    dialouge = gui.Dlg(title="Subject number:")
    dialouge.addText('Subject info')
    dialouge.addField('Subject number:')
    dialouge.addField('Age:')
    dialouge.addField('Handedness:', choices=['Right', 'Left', 'Ambidextrous'])
    dialouge.show()
    if dialouge.OK:
        pass
    else:
        core.quit()
    subject_num = dialouge.data[0]
    subject_age = dialouge.data[1]
    subject_handedness = dialouge.data[2]

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
    instruction_2_text = '''בקרוב יוצגו בפניכם מוצרים, אחד אחרי השני.
עליכם לבחור את המחיר המירבי שתהיו מוכנים לשלם על המוצר.
יש לכם תקציב של ₪100 לכל מוצר. 

נסו להעריך כל מוצר בנפרד ולחשוב כמה הוא שווה עבורכם. ₪100 זמינים לכל מוצר בנפרד.

לחצו על העכבר כדי להמשיך.'''
    instruction_2_stim = visual.TextStim(win, text=instruction_2_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
    display_instructions(mouse, win, instruction_2_stim, instruction_2_headline_stim)
    core.wait(0.7)

    instruction_3_text = '''בסוף הניסוי, המחשב יבחר את אחד המוצרים ויקבע מחיר עבורו.

אם המחיר שבחרתם נמוך מהמחיר שנקבע על ידי המחשב, 
לא תקבלו את המוצר ותישארו עם כל התקציב.
אם המחיר שבחרתם גבוה מהמחיר שנקבע על ידי המחשב,
תשלמו את המחיר שנקבע ותקבלו את המוצר.

לחצו על העכבר כדי להמשיך.'''
    instruction_3_stim = visual.TextStim(win, text=instruction_3_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
    display_instructions(mouse, win, instruction_3_stim)
    core.wait(0.7)

    # BDM example 1
    example_1_text = f'''נתחיל עם דוגמא:
מה המחיר המירבי שתהיו מוכנים לשלם על המוצר הזה בין 0 ל-₪{MAX_WTP}?
הזיזו את העכבר על פני המלבן ולחצו כדי לבצע בחירה.'''
    example_1_stim = visual.TextStim(win, text=example_1_text, pos=(0, 150), alignText='right', **TEXT_STIM_KWARGS)
    # example_amount = visual.TextStim(win, text=f"₪40", height=TEXT_SIZE, pos=slider_example1.pos+(0, 150), color=TEXT_COLOR)
    # example_prob = visual.TextStim(win, text=f"65%", height=TEXT_SIZE, pos=slider_example1.pos+(0, 100), color=TEXT_COLOR)
    example_product = visual.ImageStim(win, pos=slider_example1.pos+(0, 250))
    event.Mouse(visible=False)
    example_product_1 = create_product_object(example_product, 'stimuli/example/example1.png')
    trial_data_dict = display_slider(mouse, win, slider_example1, example_product_1, example_1_stim, is_demo_trial=True, delay=False)
    example_1_choice = trial_data_dict['choice']
    core.wait(0.7)
    ##
    example_1_feedback_text = f'''יפה מאוד!
בחרתם שתהיו מוכנים לשלם ₪{example_1_choice} עבור המוצר. נשמע נכון?

כעת נניח שהמוצרה הזה נבחר בסוף הניסוי.
המחשב יקבע עבורו מחיר באקראי.

לחצו על העכבר להמשך.'''
    example_1_feedback_stim = visual.TextStim(win, text=example_1_feedback_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
    display_instructions(mouse, win, example_1_feedback_stim)
    core.wait(0.7)
    ##
    random_price = random.randint(0, example_1_choice)

    if random_price == example_1_choice:
        example_1_lower_or_equal = f'''המחיר שנקבע זהה לזה שבחרתם, אז תשלמו את המחיר שקבע המחשב (₪{random_price}) ותקבלו את המוצר.'''
    else:
        example_1_lower_or_equal = f'''המחיר שנקבע נמוך מזה שבחרתם, אז תשלמו את המחיר שקבע המחשב (₪{random_price}) ותקבלו את המוצר.'''

    example_1_price_text = f'''המחשב קבע מחיר: ₪{random_price}
ואתם בחרתם לשלם לכל היותר: ₪{example_1_choice}

''' + example_1_lower_or_equal + f'''
במקרה כזה, תסיימו את הניסוי עם תקציב של ₪{MAX_WTP - random_price} ועם המוצר.

לחצו על העכבר להמשך.'''
    example_1_price_stim = visual.TextStim(win, text=example_1_price_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
    display_instructions(mouse, win, example_1_price_stim)
    core.wait(0.7)

    # BDM example 2
    example_2_text = f'''הנה עוד דוגמא.'''
    example_2_stim = visual.TextStim(win, text=example_2_text, pos=(0, 250), alignText='right', **TEXT_STIM_KWARGS)
    example_product_2 = visual.ImageStim(win, pos=slider_example2.pos+(0, 250))
    example_product_2 = create_product_object(example_product_2, 'stimuli/example/example2.png')
    trial_data_dict = display_slider(mouse, win, slider_example2, example_product_2,  example_2_stim, is_demo_trial=True, delay=False)
    example_2_choice = trial_data_dict['choice']
    core.wait(0.7)
    ##
    example_2_feedback_text = f'''בחרתם שתהיו מוכנים לשלם ₪{example_2_choice} עבור המוצר.

נניח שהמוצר הזה נבחר בסוף הניסוי.
כעת המחשב יקבע עבורו מחיר באקראי.

לחצו על העכבר להמשך.'''
    example_2_feedback_stim = visual.TextStim(win, text=example_2_feedback_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
    display_instructions(mouse, win, example_2_feedback_stim)
    core.wait(0.7)
    ##
    random_price = random.randint(example_2_choice+1, MAX_WTP)
    example_2_price_text = f'''המחשב קבע מחיר: ₪{random_price}
ואתם בחרתם לשלם לכל היותר: ₪{example_2_choice}

מכיוון שהמחיר שבחרתם נמוך מהמחיר שנקבע, לא תקבלו את המוצר.
במקרה כזה, בסוף הניסוי תקבלו את כל התקציב ההתחלתי של ₪{MAX_WTP}.

לחצו על העכבר להמשך.'''
    example_2_price_stim = visual.TextStim(win, text=example_2_price_text, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
    display_instructions(mouse, win, example_2_price_stim)
    core.wait(0.7) 

    # examples 4-8
    example_paths = glob.glob('stimuli/example/example3*.png')
    example_conditions = data.importConditions(_thisDir + os.sep + 'example_stimuli.csv')
    trials = data.TrialHandler(trialList=example_conditions, nReps=1)
    TEXT_SIZE = 60
    SLIDER_WIDTH = 600
    product = visual.ImageStim(win, pos=slider.pos+(0, 250))
    choices = np.zeros(len(example_paths)) 
    rts = np.zeros(len(example_paths))
    for trial in trials:
        display_fixation(win, initial=True)
        product_path = trial['image']
        product = create_product_object(product, product_path)
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
    display_fixation(win, initial=False, fixation_time=fixation_time, trials=trials)
    core.wait(0.7) 
    # pre-start
    end_practice = f'''סיימתם את האימון!

כעת נתחיל את הניסוי.
אתם תראו מוצרים ותתבקשו לבחור כמה תהיו מוכנים לשלם עבורם.
יש לכם תקציב של ₪{MAX_WTP} עבור כל מוצר.
בסוף הניסוי מוצר אחד ייבחר באקראי.

לחצו על העכבר כדי להתחיל את הניסוי.'''
    end_practice_stim = visual.TextStim(win, text=end_practice, pos=(0, -50), alignText='right', **TEXT_STIM_KWARGS)
    display_instructions(mouse, win, end_practice_stim)
    core.wait(0.7)

    ### start of real experiment ###

    # load data and parameters
    TEXT_SIZE = 60
    SLIDER_WIDTH = 600
    blocks = 3
    if _thisDir[-3:]=='bdm':
        stimuli_files = glob.glob('../stimuli/*.png')
        # go one dir up
        conditions_path = _thisDir + os.sep + '..' + os.sep + 'stimuli.csv'
    else:
        stimuli_files = glob.glob('stimuli/*.png')
        conditions_path = _thisDir + os.sep + 'stimuli.csv' 
    # save stimuli to csv
    stimuli_df = pd.DataFrame({'image':stimuli_files})
    stimuli_df.to_csv(conditions_path)
    conditions = data.importConditions(conditions_path)
    expInfo = {
        'participant': subject_num,
        'age': subject_age,
        'handedness': subject_handedness
    }
    exp_name = 'neuro_DN'
    expInfo['date'] = data.getDateStr()  # add a simple timestamp
    expInfo['expName'] = exp_name
    subject_dir = _thisDir + os.sep + 'data' + os.sep + subject_num
    os.mkdir(subject_dir)
    filename = subject_dir + os.sep + f"{exp_name}_{expInfo['participant']}"
    os.chdir(_thisDir)

    choices = np.zeros(len(conditions))
    rts = np.zeros(len(conditions))
    product = visual.ImageStim(win, pos=slider.pos+(0, 250))
    CLOCK.reset()
    
    for block_i in range(blocks):
        display_fixation(win, initial=True)
        core.wait(0.7)
        # present block start screen
        block_num = block_i + 1
        block_trials = data.TrialHandler(trialList=conditions, nReps=1, method='random')
        block_start_text = f'''בלוק {block_num}.\n לחצו כדי להמשיך.'''
        # trials in random order for each block
        block_start_stim = visual.TextStim(win, text=block_start_text, pos=(0, 0), alignText='center', height=TEXT_SIZE, 
                                        wrapWidth=WRAP_WITDH, color=TEXT_COLOR, languageStyle='RTL', font=FONT)
        display_instructions(mouse, win, block_start_stim)
        core.wait(0.7)
        display_fixation(win, initial=True)
        i = 0
        for trial in block_trials:
            product_path = trial['image']
            product = create_product_object(product, product_path)
            trial_data_dict = display_slider(mouse, win, slider, product, trials=block_trials, block_num=block_num)
            trials = save_trial_data(trial_data_dict, block_trials)
            trial_rt = trial_data_dict['rt']
            if trial_rt is None:
                fixation_time = SOA - MAX_DURATION
            else:
                fixation_time = SOA - trial_rt
            wait_time = display_fixation(win, initial=False, fixation_time=fixation_time, trials=trials)
            trials.addData('wait_time', wait_time)
            i += 1
        trials.addData('subject', subject_num)
        trials.addData('age', subject_age)
        trials.addData('handedness', subject_handedness)
        # save block data to csv
        trials.saveAsWideText(f'{filename}_block{block_num}.csv', delim=',', appendFile=False)

    # read subject's data
    block_data_files = glob.glob(f'{filename}_block*.csv')
    experiment_data = pd.DataFrame([])
    for block_file in block_data_files:
        block_data = pd.read_csv(block_file, index_col=0)
        experiment_data = pd.concat([experiment_data, block_data])
    # average responses over blocks
    avg_product_choices = experiment_data[['image_path', 'choice']].groupby('image_path').mean()
    # sort products from highest (0) to lowset (-1)
    avg_product_choices = avg_product_choices.sort_values(by='choice', ascending=False)
    avg_product_choices = avg_product_choices.reset_index()
    # choose target products, the first 10 
    targets = avg_product_choices.iloc[:10]

    # choose 2 targets with diffs of 9, 7, 6, 5, 3, 1
    # define the differences between targets that we want to choose
    diffs = [9, 7, 6, 5, 3, 1]
    # get indices corresponding to each kind of diff from the targets, i.e., 1 and 10 for diff==9, 3 and 9 for diff==6, etc.
    target_indices = []
    for diff in diffs:
        target_diff_indices = []
        for i in range(len(targets)):
            if i + diff < len(targets):
                diff_array = np.array([i, i + diff, diff])
                target_diff_indices.append(diff_array)
        target_indices = target_indices + target_diff_indices

    # choose one randomly diff index for each diff, minimizing the amount of products that will be selected more than once
    target_indices = np.array(target_indices)
    target_indices_df = pd.DataFrame(target_indices, columns=['target1', 'target2', 'diff'])
    selected_indices = {diff: np.array([]) for diff in diffs}
    selected_products = set()
    product_counts = {product: 0 for product in range(len(targets))}
    for diff in diffs:
        # get indices with the current diff
        diff_indices = target_indices_df[target_indices_df['diff'] == diff].copy()
        # remove selected products from the diff indices
        least_selected_products = diff_indices[~diff_indices['target1'].isin(selected_products) & ~diff_indices['target2'].isin(selected_products)]
        # if all products have been selected at least once, choose the least selected pair
        if least_selected_products.empty:
            diff_indices.loc[:, 'target1_count'] = diff_indices['target1'].apply(lambda x: product_counts[x])
            diff_indices.loc[:, 'target2_count'] = diff_indices['target2'].apply(lambda x: product_counts[x])
            diff_indices.loc[:, 'pair_count'] = diff_indices['target1_count'] + diff_indices['target2_count']
            # get the pairs with minimal pair count
            minimal_count = diff_indices['pair_count'].min()
            least_selected_products = diff_indices[diff_indices['pair_count'] == minimal_count]
        # ranodmlly choose one of the least selected pairs
        least_selected_products = least_selected_products.sample()
        # save targets indices
        target1, target2 = least_selected_products['target1'].values[0], least_selected_products['target2'].values[0]
        selected_indices[diff] = np.array([target1, target2])
        # save selected products, increase count
        selected_products.add(target1)
        selected_products.add(target2)
        product_counts[target1] += 1
        product_counts[target2] += 1

    # save the selected target indices
    target_index_pair_df = pd.DataFrame(selected_indices, index=['target1', 'target2']).T
    # take next 20 to be distractors
    # choose 6 out of 20 distractors, with equal jumps of 4
    distractors = avg_product_choices.iloc[10::4]
    # construct the final stimuli dataframe
    fmri_stimuli_df = pd.DataFrame([], columns=['target1', 'target2', 'distractor', 
                                                'target1_rank', 'target2_rank', 'distractor_rank', 
                                                'target1_choice', 'target2_choice', 'distractor_choice', 
                                                'targets_diff'])
    # for each target pair, add all 6 distractors
    for diff in target_index_pair_df.index:
        target1_index, target2_index = target_index_pair_df.loc[diff]
        target1_rank, target2_rank = target1_index+1, target2_index+1
        target1 = targets.loc[target1_index, 'image_path']
        target2 = targets.loc[target2_index, 'image_path']
        target1_choice = targets.loc[target1_index, 'choice']
        target2_choice = targets.loc[target2_index, 'choice']
        for distractor_i in distractors.index:
            distractor = distractors.loc[distractor_i, 'image_path']
            distractor_choice = distractors.loc[distractor_i, 'choice']
            distractor_rank = distractor_i + 1
            stimuli_triad = pd.DataFrame({  'target1': target1, 'target2': target2, 'distractor': distractor, 
                                            'target1_rank': target1_rank, 'target2_rank': target2_rank, 'distractor_rank': distractor_rank,
                                            'target1_choice': target1_choice, 'target2_choice': target2_choice, 'distractor_choice': distractor_choice,
                                            'targets_diff': diff, 'is_blank': 0}, index=[distractor_i])
            fmri_stimuli_df = pd.concat([fmri_stimuli_df, stimuli_triad], ignore_index=True)
    # create 3 blank stimuli
    blank_stimuli = pd.DataFrame({'target1': np.zeros(3), 
                                  'target2': np.zeros(3), 
                                  'distractor': np.zeros(3), 
                                  'is_blank': np.ones(3)}, index=[0, 1, 2])
    # add blank stimuli to fMRI stimuli
    fmri_stimuli_df = pd.concat([fmri_stimuli_df, blank_stimuli], ignore_index=True)
    # save csv
    fmri_stimuli_df.to_csv(filename+'_BDM.csv', index=False)
    # write to json and turn to js for the next part
    json_format = fmri_stimuli_df.to_json(orient='records')
    js_format = f'var image_stimuli = {json_format}'
    # write js
    with open(subject_dir + os.sep + 'stimuli.js', 'w') as f:
        f.write(js_format)

    end_text = f'''כל הכבוד! סיימתם את החלק הזה.'''
    end_text_stim = visual.TextStim(win, text=end_text, pos=(0, -50), alignText='center', **TEXT_STIM_KWARGS)
    end_text_stim.draw()
    win.flip()
    keys = event.waitKeys(keyList = ['space', 'enter', 'escape'])
    # Close the window
    win.close()
    core.quit()
