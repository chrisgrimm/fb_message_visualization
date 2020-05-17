from bs4 import BeautifulSoup
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
import os
import numpy as np
import pickle
import csv
import argparse
import re


Message = namedtuple('Message', ['time',  'message', 'author'])
Thread = namedtuple('Thread', ['name', 'messages'])


def get_messages_from_thread_html(thread_html):
    soup = BeautifulSoup(thread_html, features='html.parser')
    message_soups = soup.select('div.pam')
    messages = []
    for message_soup in message_soups:
        try:
            messages.append(parse_message_soup(message_soup))
        except IndexError:
            continue
    return messages


def parse_message_soup(message_soup):
    author = message_soup.select('div._2pio')
    author = author[0]
    author = author.text
    message = message_soup.select('div._2let')
    message = message[0]
    message = message.text
    time = message_soup.select('div._2lem')
    time = time[0]
    time = time.text
    time = datetime.strptime(time, '%b %d, %Y, %I:%M %p')
    return Message(time, message, author)


def load_threads(base_dir, your_name, use_random_names=False):
    inbox_path = os.path.join(base_dir, 'messages', 'inbox')
    threads = []
    all_convos = os.listdir(inbox_path)
    all_convos = [c for c in all_convos if not c.startswith('.')]
    random_name_counter = 0
    if use_random_names:
        with open('./random_names.txt', 'r') as f:
            random_names = f.readlines()
    else:
        random_names = []
    for i, convo in enumerate(all_convos):
        print(f'({i} / {len(all_convos)}) Loading {convo}')
        thread_path = os.path.join(inbox_path, convo, 'message_1.html')
        with open(thread_path, 'r') as f:
            thread_html = f.read()
        messages = get_messages_from_thread_html(thread_html)[::-1]
        participants = get_thread_participants(messages)
        # only consider threads between you and one other person
        if (len(participants) != 2) or (your_name not in participants):
            continue
        participants.remove(your_name)
        other_participant = participants.pop()
        if use_random_names:
            other_participant = random_names[random_name_counter]
            random_name_counter += 1
        threads.append(Thread(other_participant, messages))
    return threads


def get_thread_participants(messages):
    participants = set()
    for message in messages:
        participants.add(message.author)
    return participants


def bin_thread_by_messages(thread, start_time, end_time, increment):
    time = start_time
    cutoff_time = start_time + increment
    bins = dict()
    while cutoff_time <= end_time:
        bins[(time, cutoff_time)] = []
        time = cutoff_time
        cutoff_time = time + increment
    message_idx = 0
    for time, cutoff_time in bins:
        while True:
            try:
                message = thread.messages[message_idx]
            except IndexError:
                break
            if time <= message.time < cutoff_time:
                bins[(time, cutoff_time)].append(message)
                message_idx += 1
            else:
                break
    return bins


def n_step_moving_average(lst, n):
    n_list = []
    for l in lst:
        n_list.append(l)
        n_list = n_list[-n:]
        yield np.mean(n_list)


def thread_to_num_messages(thread, start_time, end_time, increment):
    binned_thread = bin_thread_by_messages(thread, start_time, end_time, increment)
    sorted_keys = sorted(binned_thread.keys(), key=lambda x: x[0])
    num_messages = [len(binned_thread[key]) for key in sorted_keys]
    # average weekly count
    return num_messages


def get_convo_bounds(threads):
    start_time = None
    end_time = None
    for thread in threads:
        if start_time is None or thread.messages[0].time < start_time:
            start_time = thread.messages[0].time
        if end_time is None or thread.messages[-1].time > end_time:
            end_time = thread.messages[-1].time
    return start_time, end_time


def compute_thread_scores(base_dir, increment, your_name, use_random_names=False):
    threads = load_threads(base_dir, your_name, use_random_names)
    start_time, end_time = get_convo_bounds(threads)
    all_num_messages = []
    for thread in threads:
        num_messages = thread_to_num_messages(thread, start_time, end_time, increment)
        all_num_messages.append((thread.name, num_messages))
    return all_num_messages, start_time, end_time, increment


def build_csv(scores_file):
    with open(scores_file, 'rb') as f:
        scores, start_time, end_time, increment = pickle.load(f)
    # get cutoff times
    cutoff_time = start_time + increment
    cutoff_times = []
    while cutoff_time <= end_time:
        cutoff_times.append(cutoff_time)
        time = cutoff_time
        cutoff_time = time + increment
    str_times = []
    for cutoff_time in cutoff_times:
        print(cutoff_time)
        str_times.append(cutoff_time.strftime('%b %d, %Y'))
    headers = ['Name', 'Image URL'] + str_times
    def get_initials_link(name):
        initials = [x[0].upper() for x in name.split(' ')]
        initials = [initials[0], initials[-1]]
        initials = ''.join(initials)
        return f'https://dummyimage.com/300x200/000/fff.png&text={initials}'
    with open('scores.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for friend, num_messages in scores:
            if friend == 'Facebook User':
                continue
            print('Friend', friend)
            avgs = dict(zip(str_times, list(n_step_moving_average(num_messages, 120))))
            row = {'Name': friend, 'Image URL': get_initials_link(friend)}
            row = {**row, **avgs}
            writer.writerow(row)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-dir', type=str, required=True)
    parser.add_argument('--name', type=str, required=True)
    parser.add_argument('--increment', type=str, default='1d')
    parser.add_argument('--use-random-names', action='store_true')
    args = parser.parse_args()
    base_dir = args.base_dir
    your_name = args.name
    increment_str = args.increment
    match = re.match(r'^(\d+)([hdm])$', increment_str)
    if not match:
        raise Exception(f'Invalid argument increment={increment_str}. '
                        f'Must be integer followed by unit. '
                        f'(i.e., 1h = 1 hour, 2d = 2 days, 3m = 3 months')
    amount, unit = match.group()
    unit = {'h': 'hours', 'd': 'days', 'm': 'months'}[unit]
    increment = timedelta(**{unit: int(amount)})
    scores = compute_thread_scores(base_dir, increment, your_name, use_random_names=args.use_random_names)
    with open('scores.pickle', 'wb') as f:
        pickle.dump(scores, f)
    scores_file = '/Users/chris/projects/fb_messages/scores.pickle'
    build_csv(scores_file)