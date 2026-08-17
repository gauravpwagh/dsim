KRDL_KRPU_BOARD = ['KRDL', 'BCHL', 'BHNS', 'KMLR', 'DWZ', 'GIZ', 'DBF', 'KWGN', 'KKLU', 'KMSD', 'SZY', 'DMK',
                    'BDXX', 'TPQ', 'KMEZ', 'JDB', 'NKX', 'AGZ', 'AGB', 'KPRR', 'CJS', 'KDPA', 'DIR', 'JYP', 
                    'CTS', 'MVG', 'JRT', 'MVF', 'KRPU'] 

    # from KRPU it connects to DMRT and then to the VZM line 

KR_BOARD = ['KRPU', 'DMRT', 'DMNJ', 'BGUA', 'KKGM', 'LKMR', 'SGRM', 'TKRI', 'RUL', 'LLGM', 'BLMK'] # list goes till VZM

    # direct connection from BLMK to VZM 

RV_BOARD= ['BLMK', 'SKPI', 'KTGA', 'SPRD', 'RGDA', 'LDX', 'JMPT', 'KNRT', 'GMDA', 'PVP', 'SNM', 'VBL', 
           'DNV', 'KMX', 'GPI', 'GRBL', 'GTLM', 'VZM'] 

OEC_KRPU_BOARD = ['KRPU', 'SUKU', 'PBV', 'MKRD', 'BHJA', 'PFU', 'DPC', 'GPJ', 'ARK', 'SMLG', 'KVLS',
                   'BGHU', 'CMDP', 'TXD', 'SLPM', 'BDVR', 'SUP', 'LVK', 'MVW', 'KTV', 'PDT', 'SCMN'] 

# combine station line from KRDL to VZM; having a junction at KRPU
KRDL_VZM = ['KRDL', 'BCHL', 'BHNS', 'KMLR', 'DWZ', 'GIZ', 'DBF', 'KWGN', 'KKLU', 'KMSD', 'SZY', 'DMK',
            'BDXX', 'TPQ', 'KMEZ', 'JDB', 'NKX', 'AGZ', 'AGB', 'KPRR', 'CJS', 'KDPA', 'DIR', 'JYP', 
            'CTS', 'MVG', 'JRT', 'MVF', 'KRPU', 'DMRT', 'DMNJ', 'BGUA', 'KKGM', 'LKMR', 'SGRM', 
            'TKRI', 'RUL', 'LLGM', 'BLMK', 'SKPI', 'KTGA', 'SPRD', 'RGDA', 'LDX', 'JMPT', 'KNRT', 
            'GMDA', 'PVP', 'SNM', 'VBL', 'DNV', 'KMX', 'GPI', 'GRBL', 'GTLM', 'VZM'] 

# below stns are related to the port operations 
AREA_CONTROL = ['VSKP', 'WATD', 'WATE', 'GPT', 'SCMN']
VISHKHA_COMPLEX_BOARD = ['DVD', 'VSKP', 'GPT', 'SCMN', 'PDT', 'KTV']

ALL_STATIONS =  ['KRDL', 'BCHL', 'BHNS', 'KMLR', 'DWZ', 'GIZ', 'DBF', 'KWGN', 'KKLU', 'KMSD', 'SZY', 'DMK',
            'BDXX', 'TPQ', 'KMEZ', 'JDB', 'NKX', 'AGZ', 'AGB', 'KPRR', 'CJS', 'KDPA', 'DIR', 'JYP', 
            'CTS', 'MVG', 'JRT', 'MVF', 'KRPU', 'DMRT', 'DMNJ', 'BGUA', 'KKGM', 'LKMR', 'SGRM', 
            'TKRI', 'RUL', 'LLGM', 'BLMK', 'SKPI', 'KTGA', 'SPRD', # single line stations blocksections
              'RGDA', 'LDX', 'JMPT', 'KNRT', 
            'GMDA', 'PVP', 'SNM', 'VBL', 'DNV', 'KMX', 'GPI', 'GRBL', 'GTLM', 'VZM',
            'KRPU', 'SUKU', 'PBV', 'MKRD', 'BHJA', 'PFU', 'DPC', 'GPJ', 'ARK', 
            'SMLG', 'KVLS', 'BGHU', 'CMDP', 'TXD', 'SLPM', 'BDVR', # single line stations blocksections
              'SUP', 'LVK', 'MVW', 'KTV', 'PDT', 'SCMN']
 
pun_psa = ['PUN','NWP','KBM','TIU','ULM','CHE','DUSI','PDU','SGDM', 'CPP' , 'GVI','NML','VZM','KUK','ALM','KPL','KTV']


krdl_vzm_single_line_blsec = [bchl_bhns_mid1, bhns_kmlr_mid1, # end stations are bchl and bhns, middle station is kmlr  = DONE
                              mvg_jrt_mid1, jrt_mvf_mid1,   # mvg and mvf are end stations; jrt is the middle station   = DONE
                             bgua_kkgm_mid1, kkgm_lkmr_mid1, # end stations are bgua and lkmr                           = 
                              tkri_rul_mid1, rul_llgm_mid1, llgm_blmk_mid1, blmk_skpi_mid1, skpi_ktga_mid1, ktga_sprd_mid1, # tkri and sprd are the end stations = DONE
                              ]

krpu_ktv_sigle_line_blsec = [
    krpu_suku_mid1,                                                                                 # = DONE
    smlg_kvls_mid1, kvls_bghu_mid1, bghu_cmdp_mid1, cmdp_txd_mid1, txd_slpm_mid1, slpm_bdvr_mid1    # = DONE
    ]


psa_scmn_single_line_blsec = [
    None
]