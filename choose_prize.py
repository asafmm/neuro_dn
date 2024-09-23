import pandas as pd
import numpy as np
import random
import scipy
import glob
import matplotlib.pyplot as plt
from tkinter.filedialog import askopenfilenames

# read files from dialog
run_files = askopenfilenames()
run_files = np.array(run_files)

# split into bdm and choice parts
bdm_part_bool = ['neuro_DN' in run_files[i] for i in range(len(run_files))]
bdm_part_bool = np.array(bdm_part_bool)
bdm_part_files = run_files[bdm_part_bool]
choice_part_files = run_files[~bdm_part_bool]

part = random.randint(1, 2)

# part one chosen 
if part==1:
    print(f'Part 1 chosen')
    # randomize run and trial
    run = random.randint(0, len(bdm_part_files)-1)
    # extract trial choice info
    chosen_file = bdm_part_files[run]
    run_df = pd.read_csv(chosen_file)
    n_trials = len(run_df)
    trial = random.randint(1, n_trials)
    print(f'Run: {run+1}, Trial: {trial}')
    # evaluation_trials = run_df.loc[run_df.part=='evaluation', ['response', 'ID', 'amount', 'prob']]
    chosen_trial = run_df.loc[run_df.TrialNumber==trial]
    chosen_response = chosen_trial.choice.values[0]
    # response is in tokens, each token is 1/10 NIS
    chosen_payment = chosen_response / 10 
    if ~np.isnan(chosen_response):
        chosen_response = int(chosen_response)
    chosen_product = chosen_trial.image_path.str.extract("\\\\(.*).png|.PNG").values[0, 0]
    
    # print results
    print(f'The chosen product is: {chosen_product}')
    # set random price
    print(f'You chose to pay maximum of: ₪{chosen_payment}')
    computer_random_price = random.randint(1, 10)
    print(f'The computer set the price of ₪{computer_random_price}')
    if computer_random_price > chosen_response:
        # price higher than response
        print('The price is higher than you offered, you get the full budget of ₪10.')
    else:
        # price lower than response
        print(f'You pay ₪{computer_random_price}.')
        print(f'You win the product: {chosen_product} and the remaining budget of ₪{10 - computer_random_price}')

# part 2 chosen
else:
    print(f'Part 2 chosen')
    # randomize run and trial
    run = random.randint(0, len(choice_part_files)-1)
    # extract trial choice info
    chosen_file = choice_part_files[run]
    choice_part_df = pd.read_csv(chosen_file)
    choice_part_df = choice_part_df[choice_part_df.part=='trinary'].reset_index(drop=True)
    n_trials = len(choice_part_df)
    trial = random.randint(1, n_trials)
    print(f'Run: {run+1}, Trial: {trial}')
    chosen_trial = choice_part_df.iloc[trial, :]
    chosen_response = chosen_trial.actual_choice
    if chosen_response == 'target1':
        chosen_product = chosen_trial.target1.split('\\')[-1].split('.')[0]
    elif chosen_response == 'target2':
        chosen_product = chosen_trial.target2.split('\\')[-1].split('.')[0]
    else:
        chosen_product = chosen_trial.distractor.split('\\')[-1].split('.')[0]
    print(f'You won: {chosen_product}')
