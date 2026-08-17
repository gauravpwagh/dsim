from blocksections import block_sec
from stations import populate_connections
from .krpu_ktv_stations_data import station_dict, stations_list  # rename import if running multiple boards

# Converted from krpu_ktv_blocksections.py (old int dir 0/1/2 -> dn1/up1/mid1).
# Dropped: krpu_mvf, krpu_dmrt (branch stubs), mvw_ktv (inter-board link; ktv not in this board).


krpu_suku_mid1= block_sec('mid1', 'krpu', 'suku', 11.16, {'krpu': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'], 'suku': ['s1', 's2', 's3', 's4']}, stations_list)

suku_pbv_dn1  = block_sec('dn1', 'suku', 'pbv', 7.59, {'suku': ['s1', 's2', 's3', 's4'], 'pbv': ['s3', 's4']}, stations_list)
suku_pbv_up1  = block_sec('up1', 'suku', 'pbv', 7.59, {'suku': ['s1', 's2', 's3', 's4'], 'pbv': ['s1', 's2', 's3']}, stations_list)

# pbv_mkrd_mid1  = block_sec('mid1', 'pbv', 'mkrd', 12.57, {'pbv': ['s3', 's4'], 'mkrd': ['s3', 's4']}, stations_list) 
pbv_mkrd_dn1  = block_sec('dn1', 'pbv', 'mkrd', 12.57, {'pbv': ['s3', 's4'], 'mkrd': ['s3', 's4']}, stations_list)
pbv_mkrd_up1  = block_sec('up1', 'pbv', 'mkrd', 12.57, {'pbv': ['s1', 's2', 's3'], 'mkrd': ['s1', 's2']}, stations_list)
# pbv_mkrd_mid2  = block_sec('mid2', 'pbv', 'mkrd', 12.57, {'pbv': ['s1', 's2', 's3'], 'mkrd': ['s1', 's2']}, stations_list)

# mkrd_bhja_mid1 = block_sec('mid1', 'mkrd', 'bhja', 11.39, {'mkrd': ['s3', 's4'], 'bhja': ['s3', 's4']}, stations_list)
mkrd_bhja_dn1 = block_sec('dn1', 'mkrd', 'bhja', 11.39, {'mkrd': ['s3', 's4'], 'bhja': ['s3', 's4']}, stations_list)
mkrd_bhja_up1 = block_sec('up1', 'mkrd', 'bhja', 11.39, {'mkrd': ['s1', 's2'], 'bhja': ['s1', 's2', 's3']}, stations_list)
# mkrd_bhja_mid2 = block_sec('mid2', 'mkrd', 'bhja', 11.39, {'mkrd': ['s1', 's2'], 'bhja': ['s1', 's2', 's3']}, stations_list)


bhja_pfu_dn1  = block_sec('dn1', 'bhja', 'pfu', 10.03, {'bhja': ['s1', 's2','s3', 's4'], 'pfu': ['s1', 's2', 's3', 's4']}, stations_list) 
bhja_pfu_up1  = block_sec('up1', 'bhja', 'pfu', 10.03, {'bhja': ['s1', 's2','s3', 's4'], 'pfu': ['s1', 's2', 's3', 's4']}, stations_list)

pfu_dpc_dn1   = block_sec('dn1', 'pfu', 'dpc', 9.78, {'pfu': ['s1', 's2', 's3', 's4'], 'dpc': ['s1', 's3', 's4']}, stations_list)
pfu_dpc_up1   = block_sec('up1', 'pfu', 'dpc', 9.78, {'pfu': ['s1', 's2', 's3','s4'], 'dpc': ['s1', 's2', 's3']}, stations_list)

dpc_gpj_dn1   = block_sec('dn1', 'dpc', 'gpj', 12.65, {'dpc': ['s1', 's3', 's4'], 'gpj': ['s3', 's4']}, stations_list)
dpc_gpj_up1   = block_sec('up1', 'dpc', 'gpj', 12.65, {'dpc': ['s1', 's2'], 'gpj': ['s1', 's2', 's4']}, stations_list)

gpj_ark_dn1   = block_sec('dn1', 'gpj', 'ark', 9.9, {'gpj': ['s3', 's4'], 'ark': ['s5', 's6']}, stations_list)
gpj_ark_up1   = block_sec('up1', 'gpj', 'ark', 9.9, {'gpj': ['s1', 's2', 's4'], 'ark': ['s1', 's2', 's3', 's4', 's6']}, stations_list)

ark_smlg_dn1  = block_sec('dn1', 'ark', 'smlg', 11.72, {'ark': ['s5', 's6'], 'smlg': ['s1', 's2', 's3']}, stations_list)
ark_smlg_up1  = block_sec('up1', 'ark', 'smlg', 11.72, {'ark': ['s1', 's2', 's3', 's4', 's6'], 'smlg': ['s1', 's2', 's3']}, stations_list)

smlg_kvls_mid1= block_sec('mid1', 'smlg', 'kvls', 9.0, {'smlg': ['s1', 's2', 's3'], 'kvls': ['s1', 's2', 's3']}, stations_list)

kvls_bghu_mid1= block_sec('mid1', 'kvls', 'bghu', 11.25, {'kvls': ['s1', 's2', 's3'], 'bghu': ['s1', 's2', 's3']}, stations_list)

bghu_cmdp_mid1= block_sec('mid1', 'bghu', 'cmdp', 9.01, {'bghu': ['s1', 's2', 's3'], 'cmdp': ['s1', 's2', 's3']}, stations_list)

cmdp_txd_mid1 = block_sec('mid1', 'cmdp', 'txd', 11.89, {'cmdp': ['s1', 's2', 's3'], 'txd': ['s1', 's2']}, stations_list)

txd_slpm_mid1 = block_sec('mid1', 'txd', 'slpm', 6.64, {'txd': ['s1', 's2'], 'slpm': ['s1', 's2', 's3']}, stations_list)

slpm_bdvr_mid1= block_sec('mid1', 'slpm', 'bdvr', 12.08, {'slpm': ['s1', 's2', 's3'], 'bdvr': ['s1', 's2', 's3']}, stations_list)

bdvr_sup_dn1  = block_sec('dn1', 'bdvr', 'sup', 7.29, {'bdvr': ['s1','s2', 's3'], 'sup': ['s2', 's3', 's5', 's6']}, stations_list)
bdvr_sup_up1  = block_sec('up1', 'bdvr', 'sup', 7.29, {'bdvr': ['s1', 's2', 's3'], 'sup': ['s2', 's3', 's4']}, stations_list)

sup_lvk_dn1   = block_sec('dn1', 'sup', 'lvk', 9.61, {'sup': ['s2', 's3', 's5', 's6'], 'lvk': ['s3', 's4', 's5']}, stations_list)
sup_lvk_up1   = block_sec('up1', 'sup', 'lvk', 9.61, {'sup': ['s1', 's2', 's3', 's4'], 'lvk': ['s1', 's2', 's3']}, stations_list)

lvk_mvw_dn1   = block_sec('dn1', 'lvk', 'mvw', 7.42, {'lvk': ['s3', 's4', 's5'], 'mvw': ['s1', 's2', 's4', 's5']}, stations_list)
lvk_mvw_up1   = block_sec('up1', 'lvk', 'mvw', 7.42, {'lvk': ['s1', 's2', 's3'], 'mvw': ['s1', 's2', 's3']}, stations_list)

blocksections_list = [
    krpu_suku_mid1,
    suku_pbv_dn1, suku_pbv_up1,
   pbv_mkrd_dn1, pbv_mkrd_up1,
    mkrd_bhja_dn1, mkrd_bhja_up1,
    bhja_pfu_dn1, bhja_pfu_up1,
    pfu_dpc_dn1, pfu_dpc_up1,
    dpc_gpj_dn1, dpc_gpj_up1,
    gpj_ark_dn1, gpj_ark_up1,
    ark_smlg_dn1, ark_smlg_up1,
    smlg_kvls_mid1,
    kvls_bghu_mid1,
    bghu_cmdp_mid1,
    cmdp_txd_mid1,
    txd_slpm_mid1,
    slpm_bdvr_mid1,
    bdvr_sup_dn1, bdvr_sup_up1,
    sup_lvk_dn1, sup_lvk_up1,
    lvk_mvw_dn1, lvk_mvw_up1,
   
]

# populate_connections(blocksections_list, station_dict, stations_list)

