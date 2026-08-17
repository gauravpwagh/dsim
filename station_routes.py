# Base line segments
KRDL_TO_KRPU = ['KRDL', 'BCHL', 'BHNS', 'KMLR', 'DWZ', 'GIZ', 'DBF', 'KWGN', 'KKLU', 'KMSD', 'SZY', 'DMK',
                 'BDXX', 'TPQ', 'KMEZ', 'JDB', 'NKX', 'AGZ', 'AGB', 'KPRR', 'CJS', 'KDPA', 'DIR', 'JYP',
                 'CTS', 'MVG', 'JRT', 'MVF', 'KRPU']

KRPU_TO_KTV = ['KRPU', 'SUKU', 'PBV', 'MKRD', 'BHJA', 'PFU', 'DPC', 'GPJ', 'ARK',
               'SMLG', 'KVLS', 'BGHU', 'CMDP', 'TXD', 'SLPM', 'BDVR', 'SUP', 'LVK', 'MVW', 'KTV']

KRPU_TO_SPRD = ['KRPU', 'DMRT', 'DMNJ', 'BGUA', 'KKGM', 'LKMR', 'SGRM', 'TKRI', 'RUL', 'LLGM',
                'BLMK', 'SKPI', 'KTGA', 'SPRD']

SPRD_TO_VZM = ['SPRD', 'RGDA', 'LDX', 'JMPT', 'KNRT', 'GMDA', 'PVP', 'SNM', 'VBL',
               'DNV', 'KMX', 'GPI', 'GRBL', 'GTLM', 'VZM']

KTV_TO_SCMN = ['KTV', 'PDT', 'SCMN']

VZM_TO_SCMN = ['VZM', 'VSKP', 'WATD', 'WATE', 'GPT', 'SCMN']

KTV_TO_VZM = ['KTV', 'KPL', 'ALM', 'KUK', 'VZM']

VZM_TO_PSA = ['VZM', 'NML', 'GVI', 'CPP', 'SGDM', 'PDU', 'DUSI', 'CHE', 'ULM', 'TIU', 'KBM', 'NWP', 'PUN']

# Derived segment (KTV → VZM → PSA)
KTV_TO_PSA = KTV_TO_VZM + VZM_TO_PSA[1:]

# Composite routes
KRDL_KTV   = KRDL_TO_KRPU + KRPU_TO_KTV[1:]
KRDL_VZM   = KRDL_TO_KRPU + KRPU_TO_SPRD[1:] + SPRD_TO_VZM[1:]
KRDL_SCMN  = KRDL_TO_KRPU + KRPU_TO_SPRD[1:] + SPRD_TO_VZM[1:] + VZM_TO_SCMN[1:]
KRDL_PSA   = KRDL_KTV + KTV_TO_PSA[1:]
KTV_SCMN   = KTV_TO_SCMN
SPRD_VZM   = SPRD_TO_VZM
SPRD_SCMN  = SPRD_TO_VZM + VZM_TO_SCMN[1:]
SPRD_PSA   = SPRD_TO_VZM + VZM_TO_PSA[1:]
VZM_PSA    = VZM_TO_PSA
SPRD_KTV   = SPRD_TO_VZM + list(reversed(KTV_TO_VZM))[1:]

BRANCH_LISTS = {
    # KRDL origin/destination
    'KRDL_KTV':   KRDL_KTV,
    'KTV_KRDL':   list(reversed(KRDL_KTV)),
    'KRDL_VZM':   KRDL_VZM,
    'VZM_KRDL':   list(reversed(KRDL_VZM)),
    'KRDL_SCMN':  KRDL_SCMN,
    'SCMN_KRDL':  list(reversed(KRDL_SCMN)),
    'KRDL_PSA':   KRDL_PSA,
    'PSA_KRDL':   list(reversed(KRDL_PSA)),
    # KTV origin/destination
    'KTV_SCMN':   KTV_SCMN,
    'SCMN_KTV':   list(reversed(KTV_SCMN)),
    'KTV_PSA':    KTV_TO_PSA,
    'PSA_KTV':    list(reversed(KTV_TO_PSA)),
    # VZM origin/destination
    'VZM_SCMN':   VZM_TO_SCMN,
    'SCMN_VZM':   list(reversed(VZM_TO_SCMN)),
    'VZM_PSA':    VZM_PSA,
    'PSA_VZM':    list(reversed(VZM_PSA)),
    # SPRD origin/destination
    'SPRD_VZM':   SPRD_VZM,
    'VZM_SPRD':   list(reversed(SPRD_VZM)),
    'SPRD_SCMN':  SPRD_SCMN,
    'SCMN_SPRD':  list(reversed(SPRD_SCMN)),
    'SPRD_PSA':   SPRD_PSA,
    'PSA_SPRD':   list(reversed(SPRD_PSA)),
    'SPRD_KTV':   SPRD_KTV,
    'KTV_SPRD':   list(reversed(SPRD_KTV)),
}
