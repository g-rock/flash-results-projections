MULTI_EVENT_LIST = [
  'Heptathlon',
  'Pentathlon',
  'Decathlon'
]

# The relay event names are not standardized
# so we don't really use this list
RELAY_EVENT_LIST = [
  'Distance Medley',
  '4x400 Meter Relay',
  '4x100 Meter Relay'
]

FIELD_EVENT_LIST = [
  'Weight', # Sometimes it's called just weight
  'Weight Throw',
  'Hammer',
  'Pole Vault',
  'Javelin',
  'Long Jump',
  'Shot Put',
  'Discus',
  'High Jump',
  'Triple Jump'
]

# Points system for places 1–8
POINTS_SYSTEM = {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}

# Men's Decathlon Mappings
DECATHALON = {
  '100m': '100 M',
  'LJ': 'Long Jump',
  'SP': 'Shot Put',
  'HJ': 'High Jump',
  '400m': '400 M',
  '110mH': '110 M Hurdles',
  'DT': 'Discus',
  'PV': 'Pole Vault',
  'JV': 'Javelin',
  '1500m': '1500 M'
}

# Women's Heptathlon Mappings
HEPTATHALON = {
  'LJ': 'Long Jump',
  'SP': 'Shot Put',
  'HJ': 'High Jump',
  '100mH': '100 M Hurdles',
  'PV': 'Pole Vault',
  'JV': 'Javelin',
  '800m': '800 M',
  '200m': '200 M'
}