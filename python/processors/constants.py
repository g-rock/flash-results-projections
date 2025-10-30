# Dict defining whether lower seed is better for each event
EVENT_TYPE_SORTING_RULES = {
    '4x100 M Relay': True, '1500 M': True, '110 M Hurdles': True, '100 M': True,
    '400 M': True, '800 M': True, '3000 M Steeple': True, '200 M': True,
    '10000 M': True, '4x400 M Relay': True, '4x100': True, '4x400': True,
    'Heptathlon': False, 'Decathlon': False,
    'Hammer': False, 'Pole Vault': False, 'Javelin': False, 'Long Jump': False,
    'Shot Put': False, 'Discus': False, 'High Jump': False, 'Triple Jump': False,
}

# Points system for places 1–8
POINTS_SYSTEM = {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
