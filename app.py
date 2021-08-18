# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash

import tensorflow.keras as keras
import pandas as pd
import datetime
import requests
import json

def get_live_matches():
    r = requests.get(f'https://api.betting-api.com/fonbet/football/live/all', headers=api_headers)
    matches = json.loads(r.content.decode())
    matches = [[match['id'], match['team1'], match['team2'], match['markets']['win1']['v'], match['markets']['winX']['v'], match['markets']['win2']['v'], match['league'], match['league_id'], 'Live'] for match in matches if ('win1' in match['markets'].keys()) and ('winX' in match['markets'].keys()) and ('league' in match.keys())]
    
    return matches

def get_pre_matches():
    r = requests.get(f'https://api.betting-api.com/fonbet/football/line/all', headers=api_headers)
    matches = json.loads(r.content.decode())
    matches = [[match['id'], match['team1'], match['team2'], match['markets']['win1']['v'], match['markets']['winX']['v'], match['markets']['win2']['v'], match['league'], match['league_id'], 'PreMatch'] for match in matches if ('win1' in match['markets'].keys()) and ('winX' in match['markets'].keys()) and ('league' in match.keys())]
    
    return matches

def get_all_matches():
    df = pd.DataFrame(get_live_matches(), columns = ['match_id', 'team1', 'team2', 'win1', 'winX', 'win2', 'league', 'league_id', 'state'])
    df = df.append(pd.DataFrame(get_pre_matches(), columns = ['match_id', 'team1', 'team2', 'win1', 'winX', 'win2', 'league', 'league_id', 'state']), ignore_index=True)

    return df

def argmax(arr):
    max_ = -1
    idx = 0
    for i in range(len(arr)):
        if arr[i] > max_:
            max_ = arr[i]
            idx = i

    return idx

def decode_labels(p):
  return list(map(argmax, p))

def predict_score(matches):
    pred = model.predict(matches)
    h_pred = decode_labels(pred[0])
    a_pred = decode_labels(pred[1])

    return [f'{h}:{a}' for h, a in zip(h_pred, a_pred)]

def get_prediction():
    data = get_all_matches()
    data['prediction'] = predict_score(data[['win1', 'winX', 'win2']].to_numpy())
    return data

api_key = '0213302b8a454ed79f3524260cfcfede16639678e31347b3845991ed87a24dd9'
api_headers = {'Authorization':api_key}

model = keras.models.load_model('model.h5')

data = get_prediction()
last_update = datetime.datetime.now()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[

    html.Div([
        html.H1('Select league:'),
        dcc.Dropdown(
            'leagues-dropdown',
            options=[{'label': label, 'value': value} for label, value in data[['league', 'league_id']].itertuples(index = False, name = None)]
        ),
    ],
        className = 'card'
    ),

    html.Div([
        html.H1('Select match:'),
        dcc.Dropdown(
            'matches-dropdown',
            options=[{'label':'', 'value':0}]
        ),
    ],
        className = 'card'
    ),

    html.Div([
        html.H1('Result:'),
        html.H1('???', id = 'score'),
    ],
        className='card'
    ),

    dcc.Interval(
        'timer',
        interval=1000 * 5
    )
])

@app.callback(
    Output('matches-dropdown', 'options'),
    Output('matches-dropdown', 'value'),
    Input('leagues-dropdown', 'value')
)
def update_matches(ld):
    if ld == None:
        return [], None
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = ''
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    matches = data[data['league_id'] == ld].drop(['league', 'league_id'], 1).itertuples(index = False, name = None)
    return [{'label':f'{match[1]} - {match[2]} ({match[6]})', 'value':match[0]} for match in matches], None

@app.callback(
    Output('leagues-dropdown', 'options'),
    Input('timer', 'n_intervals')
)
def update_data(n):
    global last_update
    if (datetime.datetime.now() - last_update).seconds > 60 * 10:
        global data
        last_update = datetime.datetime.now()
        data = get_prediction()

    return [{'label': label, 'value': value} for label, value in data[['league', 'league_id']].itertuples(index = False, name = None)]

@app.callback(
    Output('score', 'children'),
    Input('matches-dropdown', 'value'),
    Input('matches-dropdown', 'options')
)
def update_score(match_id, options):
    if options:
        if match_id:
            return data[data['match_id'] == match_id]['prediction']
        else:
            return '???'
    else:
        return '???'

if __name__ == '__main__':
    app.run_server(debug=True)