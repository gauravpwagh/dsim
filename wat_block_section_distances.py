# WAT Network Block Section Distances (km)
# Source: WAT_Infra_Data.xlsx - Block Section sheet (MANINTRDIST column)

# ─── Section 1: KRDL → KTV (via KRPU on OEC line) ──────────────────────────

krdl_ktv = [
    'krdl', 'bchl', 'bhns', 'kmlr', 'dwz', 'giz', 'dbf', 'kwgn', 'kklu', 'kmsd',
    'szy', 'dmk', 'bdxx', 'tpq', 'kmez', 'jdb', 'nkx', 'agz', 'agb', 'kprr',
    'cjs', 'kdpa', 'dir', 'jyp', 'cts', 'mvg', 'jrt', 'mvf', 'krpu',
    'suku', 'pbv', 'mkrd', 'bhja', 'pfu', 'dpc', 'gpj', 'ark',
    'smlg', 'kvls', 'bghu', 'cmdp', 'txd', 'slpm', 'bdvr', 'sup', 'lvk', 'mvw', 'ktv'
]

krdl_ktv_segments = {
    # krdl → krpu
    ('krdl', 'bchl'): 9.14,  ('bchl', 'bhns'): 9.55,  ('bhns', 'kmlr'): 12.43,
    ('kmlr', 'dwz'):  12.35, ('dwz',  'giz'):  7.32,   ('giz',  'dbf'):  10.99,
    ('dbf',  'kwgn'): 8.99,  ('kwgn', 'kklu'): 12.13,  ('kklu', 'kmsd'): 12.04,
    ('kmsd', 'szy'):  9.39,  ('szy',  'dmk'):  11.27,  ('dmk',  'bdxx'): 11.40,
    ('bdxx', 'tpq'):  5.61,  ('tpq',  'kmez'): 8.30,   ('kmez', 'jdb'):   8.91,
    ('jdb',  'nkx'):  6.45,  ('nkx',  'agz'):  7.90,   ('agz',  'agb'):  10.03,
    ('agb',  'kprr'): 7.60,  ('kprr', 'cjs'):  11.71,  ('cjs',  'kdpa'):  6.99,
    ('kdpa', 'dir'):  6.64,  ('dir',  'jyp'):  7.07,   ('jyp',  'cts'):   7.09,
    ('cts',  'mvg'):  6.95,  ('mvg',  'jrt'):  11.40,  ('jrt',  'mvf'):   9.21,
    ('mvf',  'krpu'): 6.83,
    # krpu → ktv (oec line)
    ('krpu', 'suku'): 11.16, ('suku', 'pbv'):  7.59,  ('pbv',  'mkrd'): 12.57,
    ('mkrd', 'bhja'): 11.39, ('bhja', 'pfu'):  10.03, ('pfu',  'dpc'):   9.78,
    ('dpc',  'gpj'):  12.65, ('gpj',  'ark'):   9.90,  ('ark',  'smlg'): 11.72,
    ('smlg', 'kvls'): 9.00,  ('kvls', 'bghu'): 11.25, ('bghu', 'cmdp'):  9.01,
    ('cmdp', 'txd'):  11.89, ('txd',  'slpm'):  6.64,  ('slpm', 'bdvr'): 12.08,
    ('bdvr', 'sup'):  7.29,  ('sup',  'lvk'):   9.61,  ('lvk',  'mvw'):   7.42,
    ('mvw',  'ktv'):  8.93,
}

# ─── Section 2: SPRD → VZM (RV line, southern portion) ──────────────────────

sprd_vzm = [
    'sprd', 'rgda', 'ldx', 'jmpt', 'knrt', 'gmda', 'pvp', 'snm',
    'vbl', 'dnv', 'kmx', 'gpi', 'grbl', 'gtlm', 'vzm'
]

sprd_vzm_segments = {
    ('sprd', 'rgda'): 9.23,  ('rgda', 'ldx'):  7.82,  ('ldx',  'jmpt'):  7.18,
    ('jmpt', 'knrt'): 9.14,  ('knrt', 'gmda'): 8.87,  ('gmda', 'pvp'):  13.59,
    ('pvp',  'snm'):  12.80, ('snm',  'vbl'):  11.28,  ('vbl',  'dnv'):  11.96,
    ('dnv',  'kmx'):  9.81,  ('kmx',  'gpi'):  9.56,   ('gpi',  'grbl'): 10.52,
    ('grbl', 'gtlm'): 5.84,  ('gtlm', 'vzm'):  5.64,
}

# ─── Section 3: PSA → KTV (main line through VZM) ───────────────────────────

psa_ktv = [
    'psa', 'pun', 'nwp', 'kbm', 'tiu', 'ulm', 'che', 'dusi', 'pdu',
    'sgdm', 'cpp', 'gvi', 'nml', 'vzm', 'kuk', 'alm', 'kpl', 'ktv'
]

psa_ktv_segments = {
    ('psa',  'pun'):  12.29, ('pun',  'nwp'):  13.24, ('nwp',  'kbm'):  13.92,
    ('kbm',  'tiu'):  13.72, ('tiu',  'ulm'):  9.63,  ('ulm',  'che'):  10.04,
    ('che',  'dusi'): 6.46,  ('dusi', 'pdu'):  8.82,  ('pdu',  'sgdm'): 10.07,
    ('sgdm', 'cpp'):  13.27, ('cpp',  'gvi'):  6.57,  ('gvi',  'nml'):  12.33,
    ('nml',  'vzm'):  11.74, ('vzm',  'kuk'):  10.65, ('kuk',  'alm'):   7.11,
    ('alm',  'kpl'):  9.23,  ('kpl',  'ktv'):  7.74,
}


block_section_distances = {
    **krdl_ktv_segments,
    **sprd_vzm_segments,
    **psa_ktv_segments,
}

# print(f"Total block sections: {len(block_section_distances)}")