"""
1. Get Data (temporal and limited to region)
2. Calculate reference point. (to be used for middle C or something.)  First and Third Quantiles to as lowest/highest
3.


"""
import os

import base64
import requests
import time
from mido import Message, MidiFile, MidiTrack
from .resources import DataSet

import midiutil
import uuid
import subprocess
import random

API_URL = "https://data.wprdc.org/api/action/datastore_search_sql"
C_MAJOR_CONTRA_ALTO = [72, 74, 76, 77, 79, 81, 83, 84, 86, 88, 89, 91, 93, 95, 96]
C_MAJOR_ALTO = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84]
C_MAJOR = [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72]
C_MAJOR_BASS = [36, 38, 40, 41, 43, 45, 47, 48, 50, 52, 53, 55, 57, 59, 60]


def get_note(val, min, max, key=C_MAJOR):
    """
    Normalize to note range
    """
    key = sorted(key)
    new_range = len(key) - 1
    norm_val = (val - min) / (max - min)
    new_val = int((norm_val * new_range))
    return key[new_val]


def get_raw_data(resource, date_field, start_date, target_field, target_condition, frequency, region_field, region_name,
                 method='count'):
    """
    Get's data from WPRDC and returns a table (list of dicts)

    :param resource: CKAN resource ID.
    :param date_field: field in CKAN resource representing the date of the event
    :param target_field: the field in the resource representing the event
    :param frequency: PostgreSQL time period ('DAY', 'WEEK', etc.)
    :param region_field: field in resource that has the region in question
    :param region_name: name of the region in question
    :param method: aggregation method to use on event data
    :return: [{}] - table representing data
    """
    condition = ''
    if target_condition:
       # print(target_condition)
        condition = 'AND "{target_field}" {target_condition}'.format(target_field=target_field,
                                                                     target_condition=target_condition)

    query = ('SELECT {method}("{target_field}") as "value", date_trunc(\'{frequency}\', "{date_field}") as "timeframe" '
             'FROM "{resource}" '
             'WHERE "{region_field}" = \'{region_name}\' AND "{date_field}" > \'{start_date}\'::date {condition}'
             'GROUP BY "timeframe" '
             'ORDER BY "timeframe" ').format(resource=resource, date_field=date_field, target_field=target_field,
                                             start_date=start_date,
                                             frequency=frequency,
                                             region_field=region_field, region_name=region_name, method=method,
                                             condition=condition)

    #print(query)

    response = requests.get(API_URL, params={'sql': query}).json()
    records = response['result']['records']

    return [(row['timeframe'], float(row['value'])) for row in records]


def get_notes(source, region_type, region_name, start_date='2016-9-1', target_field=None, target_condition=None,
              method=None, key=C_MAJOR):
    resource = source.value
    region_field = resource['region_fields'][region_type]

    if not target_field:
        target_field = resource['target_field']
    if not target_condition and 'target_condition' in resource:
        target_condition = resource['target_condition']
    if not method:
        method = resource['method']

    raw_data = get_raw_data(resource['id'], resource['date_field'], start_date, target_field, target_condition,
                            resource['frequency'], region_field,
                            region_name, resource['method'])

    values = [float(v) for t, v in raw_data]
    minimum = min(values)
    maximum = max(values)

    return [get_note(val, minimum, maximum, key=key) for val in values]


def make_track(notes, channel=0, instrument=1, velocity=100, velocities=None, length=100, lengths=None):
    """
    Makes a midi track from a series of notes
    :param notes: list of note values
    :param instrument:  midi instrument to play
    :param: velocity: velocity at which all notes will be played (0-127)
    :param velocities:  list of velocities at which notes will be played (note[n] will play with a velocity of velocities[n])
    :param length: length of time fop which all notes will sound
    :param lengths: list of lengths for which all notes will sound (note[n] will play for length[n] time)
    :return: MidiTrack
    """
    if velocity:
        velocities = [velocity for n in notes]
    if not velocities or len(velocities) < len(notes):
        raise Exception('velocities must be same length as notes, or single number')

    if type(length) in (float, int):
        lengths = [length for n in notes]
    if not lengths or len(lengths) < len(notes):
        raise Exception('lengths must be same length as notes, or single number')

    # Make the track
    track = MidiTrack()

    # Set the instrument
    track.append(Message('program_change', program=instrument, time=0))

    for note in notes:
        on = Message('note_on', time=0, velocity=100, note=note)
        track.append(on)

        off = Message('note_off', time=length, velocity=100, note=note)
        track.append(off)

    return track


#####################################################################################################################
base_length = 200

EIGHTH = 1
QUARTER = 2
HALF = 4

KEYS = [(C_MAJOR_BASS, HALF), (C_MAJOR, QUARTER), (C_MAJOR_CONTRA_ALTO, EIGHTH)]


WHOLE = 8

def make_nhood_music(hood, tracks):
    region_type = 'neighborhood'
    notes_set = []

    print(tracks)

    for track in tracks:
        if 'key' not in track:
            track['key'], track['length'] = random.choice(KEYS)

    # Get pitches
    for track in tracks:
        notes_set.append(
            get_notes(DataSet[track['dataset']],
                      region_type,
                      hood,
                      key=track['key'],
                      start_date='2016-10-1'))

    # Make midi pattern
    song = MidiFile()

    # Generate midi tracks from data
    for n in range(len(notes_set)):
        track = make_track(notes_set[n],
                           length=tracks[n]['length'] * base_length,
                           channel=n,
                           instrument=tracks[n]['instrument'])
        song.tracks.append(track)

    dir_path = os.path.dirname(os.path.realpath(__file__)) +'/midis/'
    # Write midi to file
    id = str(uuid.uuid4())
    file_path = dir_path + id
    print(file_path)
    song.save(file_path + '.mid')
    # Convert to mp3
    midi_file = file_path + '.mid'

    ps = subprocess.Popen(('timidity', midi_file, '-Ow', '-o', '-'), stdout=subprocess.PIPE)
    output = subprocess.check_output(('ffmpeg', '-i', '-', '-acodec', 'libmp3lame', '-ab', '64k', file_path+'.mp3'), stdin=ps.stdout)
    ps.wait()

    with open(file_path + '.mp3', 'rb') as f:
        result = base64.b64encode(f.read())

    return result



if __name__ == "__main__":
    tracks = [
        {
            'dataset': 'fires',
            'instrument': 2,  # Tubular Bells

        },
        {
            'dataset': 'arrests',
            'instrument': 57,  # Electric Grand Piano

        },
        {
            'dataset': 'three_one_one',
            'instrument': 1,  # Glock
        }
    ]
    make_nhood_music('Bloomfield', tracks)