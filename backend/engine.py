import numpy as np


def build_feature_vector(payload):

    compound = payload['compound']

    is_soft = 1 if compound == 'SOFT' else 0
    is_medium = 1 if compound == 'MEDIUM' else 0
    is_hard = 1 if compound == 'HARD' else 0


    features = [

        payload['lap'],

        payload['tire_age'],

        is_soft,
        is_medium,
        is_hard,

        payload['track_temp'],

        payload['air_temp'],

        payload['gap_ahead'],

        payload['gap_behind'],

        payload['speed'],

        payload['rpm'],

        payload['throttle'],

        payload['brake'],

        payload['humidity'],

        payload['rain_risk'],

        payload['fuel_load'],

        payload['position'],

        payload['current_stint']
    ]


    sequence = np.tile(
        features,
        (5, 1)
    )

    return sequence