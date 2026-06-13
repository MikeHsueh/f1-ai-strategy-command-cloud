import os
import fastf1

CACHE_DIR = 'fastf1_cache'

os.makedirs(
    CACHE_DIR,
    exist_ok=True
)

fastf1.Cache.enable_cache(
    CACHE_DIR
)

print('FastF1 cache initialized')

# 測試下載 session

session = fastf1.get_session(
    2023,
    'Bahrain',
    'R'
)

session.load()

print('Session downloaded')