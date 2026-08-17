from blocksections import block_sec
from stations import populate_connections
from .krdl_vzm_stations_data import station_dict, stations_list  # rename import if running multiple boards

# Converted from krdl_vzm_blocksections.py (old int dir 0/1/2 -> dn1/up1/mid1).
# Dropped: gtlm_vzm (link to VZM board), krpu_suku (link to KRPU board), vbl_salr (branch stub).


krdl_bchl_dn1  = block_sec('dn1', 'krdl', 'bchl', 9.14, {'krdl': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12', 's13', 's14', 's15'], 'bchl': ['s1', 's2','s3', 's4']}, stations_list)
krdl_bchl_up1  = block_sec('up1', 'krdl', 'bchl', 9.14, {'krdl': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12', 's13', 's14', 's15'], 'bchl': ['s1', 's2','s3', 's4']}, stations_list)

bchl_bhns_mid1 = block_sec('mid1', 'bchl', 'bhns', 9.55, {'bchl': ['s1', 's2', 's3', 's4'], 'bhns': ['s1', 's2', 's3']}, stations_list)

bhns_kmlr_mid1 = block_sec('mid1', 'bhns', 'kmlr', 12.43, {'bhns': ['s1', 's2', 's3'], 'kmlr': ['s1', 's2', 's3']}, stations_list)

kmlr_dwz_dn1   = block_sec('dn1', 'kmlr', 'dwz', 12.35, {'kmlr': ['s1', 's2', 's3'], 'dwz': ['s3', 's4', 's5']}, stations_list)
kmlr_dwz_up1   = block_sec('up1', 'kmlr', 'dwz', 12.35, {'kmlr': ['s1', 's2', 's3'], 'dwz': ['s1', 's2', 's4', 's5']}, stations_list)

dwz_giz_dn1    = block_sec('dn1', 'dwz', 'giz', 7.32, {'dwz': ['s3', 's4', 's5'], 'giz': ['s1', 's3', 's4']}, stations_list)
dwz_giz_up1    = block_sec('up1', 'dwz', 'giz', 7.32, {'dwz': ['s1', 's2', 's4', 's5'], 'giz': ['s1', 's2']}, stations_list)

giz_dbf_dn1    = block_sec('dn1', 'giz', 'dbf', 10.99, {'giz': ['s1', 's3', 's4'], 'dbf': ['s1', 's3', 's4']}, stations_list)
giz_dbf_up1    = block_sec('up1', 'giz', 'dbf', 10.99, {'giz': ['s1', 's2'], 'dbf': ['s1', 's2']}, stations_list)

dbf_kwgn_dn1   = block_sec('dn1', 'dbf', 'kwgn', 8.99, {'dbf': ['s1', 's3', 's4'], 'kwgn': ['s1', 's3', 's4']}, stations_list)
dbf_kwgn_up1   = block_sec('up1', 'dbf', 'kwgn', 8.99, {'dbf': ['s1', 's2'], 'kwgn': ['s1', 's2']}, stations_list)

kwgn_kklu_dn1  = block_sec('dn1', 'kwgn', 'kklu', 12.13, {'kwgn': ['s1', 's3', 's4'], 'kklu': ['s3', 's4']}, stations_list)
kwgn_kklu_up1  = block_sec('up1', 'kwgn', 'kklu', 12.13, {'kwgn': ['s1', 's2'], 'kklu': ['s1', 's2']}, stations_list)

kklu_kmsd_dn1  = block_sec('dn1', 'kklu', 'kmsd', 12.04, {'kklu': ['s3', 's4'], 'kmsd': ['s1', 's3', 's4']}, stations_list)
kklu_kmsd_up1  = block_sec('up1', 'kklu', 'kmsd', 12.04, {'kklu': ['s1', 's2'], 'kmsd': ['s1', 's2']}, stations_list)

kmsd_szy_dn1   = block_sec('dn1', 'kmsd', 'szy', 9.39, {'kmsd': ['s1', 's3', 's4'], 'szy': ['s3', 's4']}, stations_list)
kmsd_szy_up1   = block_sec('up1', 'kmsd', 'szy', 9.39, {'kmsd': ['s1', 's2'], 'szy': ['s1', 's2', 's3']}, stations_list)

szy_dmk_dn1    = block_sec('dn1', 'szy', 'dmk', 11.27, {'szy': ['s3', 's4'], 'dmk': ['s3', 's4']}, stations_list)
szy_dmk_up1    = block_sec('up1', 'szy', 'dmk', 11.27, {'szy': ['s1', 's2', 's3'], 'dmk': ['s1', 's2']}, stations_list)

dmk_bdxx_dn1   = block_sec('dn1', 'dmk', 'bdxx', 11.4, {'dmk': ['s3', 's4'], 'bdxx': ['s1', 's2', 's4', 's5']}, stations_list)
dmk_bdxx_up1   = block_sec('up1', 'dmk', 'bdxx', 11.4, {'dmk': ['s1', 's2'], 'bdxx': ['s1', 's2', 's3']}, stations_list)

bdxx_tpq_dn1   = block_sec('dn1', 'bdxx', 'tpq', 5.61, {'bdxx': ['s1', 's2', 's4', 's5'], 'tpq': ['s3', 's4']}, stations_list)
bdxx_tpq_up1   = block_sec('up1', 'bdxx', 'tpq', 5.61, {'bdxx': ['s1', 's2', 's3'], 'tpq': ['s1', 's2', 's4']}, stations_list)

tpq_kmez_dn1   = block_sec('dn1', 'tpq', 'kmez', 8.3, {'tpq': ['s3', 's4'], 'kmez': ['s3', 's4']}, stations_list)
tpq_kmez_up1   = block_sec('up1', 'tpq', 'kmez', 8.3, {'tpq': ['s1', 's2', 's4'], 'kmez': ['s1', 's2', 's4']}, stations_list)

kmez_jdb_dn1   = block_sec('dn1', 'kmez', 'jdb', 8.91, {'kmez': ['s3', 's4'], 'jdb': ['s1', 's2', 's3', 's4', 's5', 's6']}, stations_list)
kmez_jdb_up1   = block_sec('up1', 'kmez', 'jdb', 8.91, {'kmez': ['s1', 's2', 's4'], 'jdb': ['s1', 's2', 's3', 's4', 's5', 's6']}, stations_list)

jdb_nkx_dn1    = block_sec('dn1', 'jdb', 'nkx', 6.45, {'jdb': ['s1', 's2', 's3', 's4', 's5', 's6'], 'nkx': ['s3', 's4']}, stations_list)
jdb_nkx_up1    = block_sec('up1', 'jdb', 'nkx', 6.45, {'jdb': ['s1', 's2', 's3', 's4', 's5', 's6'], 'nkx': ['s1', 's2', 's4']}, stations_list)

nkx_agz_dn1    = block_sec('dn1', 'nkx', 'agz', 7.9, {'nkx': ['s3', 's4'], 'agz': ['s1', 's3', 's4']}, stations_list)
nkx_agz_up1    = block_sec('up1', 'nkx', 'agz', 7.9, {'nkx': ['s1', 's2', 's4'], 'agz': ['s1', 's2']}, stations_list)

agz_agb_dn1    = block_sec('dn1', 'agz', 'agb', 10.03, {'agz': ['s1', 's3', 's4'], 'agb': ['s1', 's3', 's4']}, stations_list)
agz_agb_up1    = block_sec('up1', 'agz', 'agb', 10.03, {'agz': ['s1', 's2'], 'agb': ['s1', 's2']}, stations_list)

agb_kprr_dn1   = block_sec('dn1', 'agb', 'kprr', 7.6, {'agb': ['s1', 's3', 's4'], 'kprr': ['s3', 's4']}, stations_list)
agb_kprr_up1   = block_sec('up1', 'agb', 'kprr', 7.6, {'agb': ['s1', 's2'], 'kprr': ['s1', 's2', 's4']}, stations_list)

kprr_cjs_dn1   = block_sec('dn1', 'kprr', 'cjs', 11.71, {'kprr': ['s3', 's4'], 'cjs': ['s3', 's4']}, stations_list)
kprr_cjs_up1   = block_sec('up1', 'kprr', 'cjs', 11.71, {'kprr': ['s1', 's2', 's4'], 'cjs': ['s1', 's2', 's4']}, stations_list)

cjs_kdpa_dn1   = block_sec('dn1', 'cjs', 'kdpa', 6.99, {'cjs': ['s3', 's4'], 'kdpa': ['s1', 's3', 's4']}, stations_list)
cjs_kdpa_up1   = block_sec('up1', 'cjs', 'kdpa', 6.99, {'cjs': ['s1', 's2', 's4'], 'kdpa': ['s1', 's2']}, stations_list)

kdpa_dir_dn1   = block_sec('dn1', 'kdpa', 'dir', 6.64, {'kdpa': ['s1', 's3', 's4'], 'dir': ['s3', 's4']}, stations_list)
kdpa_dir_up1   = block_sec('up1', 'kdpa', 'dir', 6.64, {'kdpa': ['s1', 's2'], 'dir': ['s1', 's2', 's4']}, stations_list)

dir_jyp_dn1    = block_sec('dn1', 'dir', 'jyp', 7.07, {'dir': ['s3', 's4'], 'jyp': ['s1', 's3', 's4', 's5']}, stations_list)
dir_jyp_up1    = block_sec('up1', 'dir', 'jyp', 7.07, {'dir': ['s1', 's2', 's4'], 'jyp': ['s1', 's2', 's4', 's5']}, stations_list)

jyp_cts_dn1    = block_sec('dn1', 'jyp', 'cts', 7.09, {'jyp': ['s1', 's3', 's4', 's5'], 'cts': ['s3', 's4']}, stations_list)
jyp_cts_up1    = block_sec('up1', 'jyp', 'cts', 7.09, {'jyp': ['s1', 's2', 's4', 's5'], 'cts': ['s1', 's2', 's3']}, stations_list)

cts_mvg_dn1    = block_sec('dn1', 'cts', 'mvg', 6.95, {'cts': ['s3', 's4'], 'mvg': ['s1', 's2', 's3']}, stations_list)
cts_mvg_up1    = block_sec('up1', 'cts', 'mvg', 6.95, {'cts': ['s1', 's2', 's3'], 'mvg': ['s1', 's2', 's3']}, stations_list)

mvg_jrt_mid1   = block_sec('mid1', 'mvg', 'jrt', 11.4, {'mvg': ['s1', 's2', 's3'], 'jrt': ['s1', 's2', 's3']}, stations_list)

jrt_mvf_mid1   = block_sec('mid1', 'jrt', 'mvf', 9.21, {'jrt': ['s1', 's2', 's3'], 'mvf': ['s1', 's2', 's3', 's4']}, stations_list)

mvf_krpu_dn1   = block_sec('dn1', 'mvf', 'krpu', 6.83, {'mvf': ['s1', 's2', 's3', 's4'], 'krpu': ['s1', 's3', 's4', 's5', 's6', 's7', 's8']}, stations_list)
mvf_krpu_up1   = block_sec('up1', 'mvf', 'krpu', 6.83, {'mvf': ['s1', 's2', 's3', 's4'], 'krpu': ['s1', 's2', 's4', 's5', 's6', 's7', 's8']}, stations_list)

krpu_dmrt_dn1  = block_sec('dn1', 'krpu', 'dmrt', 10.78, {'krpu': ['s1', 's3', 's4', 's5', 's6', 's7', 's8'], 'dmrt': ['s1', 's3', 's2', 's5']}, stations_list)
krpu_dmrt_up1  = block_sec('up1', 'krpu', 'dmrt', 10.78, {'krpu': ['s1', 's3', 's4', 's5', 's6', 's7', 's8'], 'dmrt': ['s1','s3', 's4', 's5']}, stations_list)

dmrt_dmnj_dn1  = block_sec('dn1', 'dmrt', 'dmnj', 8.12, {'dmrt': ['s1', 's2','s4', 's5'], 'dmnj': ['s1', 's2', 's4', 's5', 's6', 's7', 's8', 's9', 's10']}, stations_list)
dmrt_dmnj_up1  = block_sec('up1', 'dmrt', 'dmnj', 8.12, {'dmrt': ['s1', 's3', 's4', 's5'], 'dmnj': ['s3', 's4', 's5', 's6', 's7', 's8', 's9', 's10']}, stations_list)
 
dmnj_bgua_dn1  = block_sec('dn1', 'dmnj', 'bgua', 14.55, {'dmnj': ['s1', 's2', 's4', 's5', 's6', 's7', 's8', 's9', 's10'], 'bgua': ['s1', 's2']}, stations_list)
dmnj_bgua_up1  = block_sec('up1', 'dmnj', 'bgua', 14.55, {'dmnj': ['s3', 's4', 's5', 's6', 's7', 's8', 's9', 's10'], 'bgua': ['s2', 's3', 's4']}, stations_list)

bgua_kkgm_mid1 = block_sec('mid1', 'bgua', 'kkgm', 12.44, {'bgua': ['s1', 's2', 's3', 's4'], 'kkgm': ['s1', 's2', 's3', 's4']}, stations_list)

kkgm_lkmr_mid1 = block_sec('mid1', 'kkgm', 'lkmr', 15.28, {'kkgm': ['s1', 's2', 's3', 's4'], 'lkmr': ['s1', 's2', 's3', 's4']}, stations_list)

lkmr_sgrm_dn1  = block_sec('dn1', 'lkmr', 'sgrm', 12.83, {'lkmr': ['s1', 's2'], 'sgrm': ['s1', 's2']}, stations_list)
lkmr_sgrm_up1  = block_sec('up1', 'lkmr', 'sgrm', 12.83, {'lkmr': ['s1', 's3', 's4'], 'sgrm': ['s1', 's3', 's4']}, stations_list)

sgrm_tkri_dn1  = block_sec('dn1', 'sgrm', 'tkri', 9.07, {'sgrm': ['s1', 's2'], 'tkri': ['s1', 's2', 's3', 's4','s5', 's6']}, stations_list)
sgrm_tkri_up1  = block_sec('up1', 'sgrm', 'tkri', 9.07, {'sgrm': ['s1', 's3', 's4'], 'tkri': ['s1', 's2', 's3','s4', 's5', 's6']}, stations_list)

tkri_rul_mid1  = block_sec('mid1', 'tkri', 'rul', 12.43, {'tkri': ['s1', 's2', 's3', 's4', 's5', 's6'], 'rul': ['s1', 's2', 's3']}, stations_list)

rul_llgm_mid1  = block_sec('mid1', 'rul', 'llgm', 16.5, {'rul': ['s1', 's2', 's3'], 'llgm': ['s1', 's2', 's3']}, stations_list)

llgm_blmk_mid1 = block_sec('mid1', 'llgm', 'blmk', 16.93, {'llgm': ['s1', 's2', 's3'], 'blmk': ['s1', 's2', 's3']}, stations_list)

blmk_skpi_mid1 = block_sec('mid1', 'blmk', 'skpi', 10.4, {'blmk': ['s1', 's2', 's3'], 'skpi': ['s1', 's2', 's3']}, stations_list)

skpi_ktga_mid1 = block_sec('mid1', 'skpi', 'ktga', 14.77, {'skpi': ['s1', 's2', 's3'], 'ktga': ['s1', 's2', 's3', 's4']}, stations_list)

ktga_sprd_mid1 = block_sec('mid1', 'ktga', 'sprd', 9.63, {'ktga': ['s1', 's2', 's3', 's4'], 'sprd': ['s1', 's2', 's3', 's4', 's5']}, stations_list)

sprd_rgda_dn1  = block_sec('dn1', 'sprd', 'rgda', 9.23, {'sprd': ['s1', 's2', 's3','s4', 's5'], 'rgda': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9']}, stations_list)
sprd_rgda_up1  = block_sec('up1', 'sprd', 'rgda', 9.23, {'sprd': ['s1', 's2', 's3','s4', 's5'], 'rgda': ['s1', 's2', 's3', 's4', 's6', 's7', 's8', 's9']}, stations_list)
sprd_rgda_mid1 = block_sec('mid1', 'sprd', 'rgda', 9.23, {'sprd': ['s1', 's2', 's3', 's4', 's5'], 'rgda': ['s1', 's2', 's3', 's4', 's9']}, stations_list)

rgda_ldx_dn1   = block_sec('dn1', 'rgda', 'ldx', 7.82, {'rgda': ['s1', 's2', 's3', 's4', 's5', 's7', 's8', 's9'], 'ldx': ['s1', 's2']}, stations_list)
rgda_ldx_up1   = block_sec('up1', 'rgda', 'ldx', 7.82, {'rgda': ['s1', 's2', 's3', 's4', 's6', 's7', 's8', 's9'], 'ldx': ['s1', 's3', 's4']}, stations_list)

ldx_jmpt_dn1   = block_sec('dn1', 'ldx', 'jmpt', 7.18, {'ldx': ['s1', 's2'], 'jmpt': ['s1', 's2', 's4', 's5', 's6']}, stations_list)
ldx_jmpt_up1   = block_sec('up1', 'ldx', 'jmpt', 7.18, {'ldx': ['s1', 's3', 's4'], 'jmpt': ['s3', 's4', 's5', 's6']}, stations_list) 

jmpt_knrt_dn1  = block_sec('dn1', 'jmpt', 'knrt', 9.14, {'jmpt': ['s1', 's2', 's4'], 'knrt': ['s1', 's2', 's4']}, stations_list)
jmpt_knrt_up1  = block_sec('up1', 'jmpt', 'knrt', 9.14, {'jmpt': ['s3', 's4'], 'knrt': ['s1', 's3', 's4']}, stations_list)
jmpt_knrt_mid1 = block_sec('mid1', 'jmpt', 'knrt', 9.14, {'jmpt': [ 's4','s5', 's6'], 'knrt': ['s2','s3', 's4','s5', 's6']}, stations_list)

knrt_gmda_dn1  = block_sec('dn1', 'knrt', 'gmda', 8.87, {'knrt': ['s1', 's2', 's4'], 'gmda': ['s1', 's2']}, stations_list)
knrt_gmda_up1  = block_sec('up1', 'knrt', 'gmda', 8.87, {'knrt': [ 's1', 's3', 's4'], 'gmda': ['s1','s2', 's3', 's4']}, stations_list)
knrt_gmda_mid1 = block_sec('mid1', 'knrt', 'gmda', 8.87, {'knrt': ['s2','s3', 's4','s5', 's6'], 'gmda': ['s1','s2','s5', 's6']}, stations_list)
# knrt_gmda_mid1 = block_sec('mid1', 'knrt', 'gmda', 8.87, {'knrt': ['s2','s3', 's4','s5', 's6'], 'gmda': ['s1', 's2','s3','s4','s5', 's6']}, stations_list)

gmda_pvp_dn1   = block_sec('dn1', 'gmda', 'pvp', 13.59, {'gmda': ['s1', 's2'], 'pvp': ['s1', 's2', 's4', 's5', 's6']}, stations_list)
gmda_pvp_up1   = block_sec('up1', 'gmda', 'pvp', 13.59, {'gmda': ['s1', 's2','s3', 's4'], 'pvp': ['s1', 's3', 's4', 's5', 's6']}, stations_list)
gmda_pvp_mid1  = block_sec('mid1', 'gmda', 'pvp', 13.59, {'gmda': ['s1', 's2','s3','s4','s5', 's6'], 'pvp': ['s5', 's6']}, stations_list)

pvp_snm_dn1    = block_sec('dn1', 'pvp', 'snm', 12.8, {'pvp': ['s1', 's2', 's4', 's5', 's6'], 'snm': ['s1', 's2', 's4', 's5']}, stations_list)
pvp_snm_up1    = block_sec('up1', 'pvp', 'snm', 12.8, {'pvp': ['s1', 's3', 's4', 's5', 's6'], 'snm': ['s3', 's4', 's5']}, stations_list)

snm_vbl_dn1    = block_sec('dn1', 'snm', 'vbl', 11.28, {'snm': ['s1', 's2', 's4', 's5'], 'vbl': ['s1', 's2', 's4', 's5']}, stations_list)
snm_vbl_up1    = block_sec('up1', 'snm', 'vbl', 11.28, {'snm': ['s3', 's4', 's5'], 'vbl': ['s1', 's3', 's4', 's5']}, stations_list)
 
vbl_dnv_dn1    = block_sec('dn1', 'vbl', 'dnv', 11.96, {'vbl': ['s1', 's2', 's4', 's5'], 'dnv': ['s1', 's2']}, stations_list)
vbl_dnv_up1    = block_sec('up1', 'vbl', 'dnv', 11.96, {'vbl': ['s1', 's3', 's4', 's5'], 'dnv': ['s1', 's3', 's4', 's5']}, stations_list)
vbl_dnv_mid1    = block_sec('mid1', 'vbl', 'dnv', 11.96, {'vbl': ['s1', 's3', 's4', 's5'], 'dnv': ['s1', 's2', 's3', 's4', 's5']}, stations_list)
# added extra 's2' at the dnv station


dnv_kmx_dn1    = block_sec('dn1', 'dnv', 'kmx', 9.81, {'dnv': ['s1', 's2'], 'kmx': ['s1', 's2', 's3']}, stations_list)
dnv_kmx_up1    = block_sec('up1', 'dnv', 'kmx', 9.81, {'dnv': ['s1', 's2', 's3', 's4', 's5'], 'kmx': ['s1', 's2', 's4', 's5']}, stations_list)

kmx_gpi_dn1    = block_sec('dn1', 'kmx', 'gpi', 9.56, {'kmx': ['s1', 's2', 's3'], 'gpi': ['s1', 's2', 's4']}, stations_list)
kmx_gpi_up1    = block_sec('up1', 'kmx', 'gpi', 9.56, {'kmx': ['s1', 's2', 's4', 's5'], 'gpi': ['s3', 's4']}, stations_list)

gpi_grbl_dn1   = block_sec('dn1', 'gpi', 'grbl', 10.52, {'gpi': ['s1', 's2', 's4'], 'grbl': ['s1', 's2', 's3']}, stations_list)
gpi_grbl_up1   = block_sec('up1', 'gpi', 'grbl', 10.52, {'gpi': ['s3', 's4'], 'grbl': ['s1', 's2', 's4', 's5']}, stations_list)

grbl_gtlm_dn1  = block_sec('dn1', 'grbl', 'gtlm', 5.84, {'grbl': ['s1', 's2', 's3'], 'gtlm': ['s1', 's2', 's4']}, stations_list)
grbl_gtlm_up1  = block_sec('up1', 'grbl', 'gtlm', 5.84, {'grbl': ['s1', 's2', 's4', 's5'], 'gtlm': ['s3', 's4']}, stations_list)


blocksections_list = [
    krdl_bchl_dn1, krdl_bchl_up1,
    bchl_bhns_mid1,
    bhns_kmlr_mid1,
    kmlr_dwz_dn1, kmlr_dwz_up1,
    dwz_giz_dn1, dwz_giz_up1,
    giz_dbf_dn1, giz_dbf_up1,
    dbf_kwgn_dn1, dbf_kwgn_up1,
    kwgn_kklu_dn1, kwgn_kklu_up1,
    kklu_kmsd_dn1, kklu_kmsd_up1,
    kmsd_szy_dn1, kmsd_szy_up1,
    szy_dmk_dn1, szy_dmk_up1,
    dmk_bdxx_dn1, dmk_bdxx_up1,
    bdxx_tpq_dn1, bdxx_tpq_up1,
    tpq_kmez_dn1, tpq_kmez_up1,
    kmez_jdb_dn1, kmez_jdb_up1,
    jdb_nkx_dn1, jdb_nkx_up1,
    nkx_agz_dn1, nkx_agz_up1,
    agz_agb_dn1, agz_agb_up1,
    agb_kprr_dn1, agb_kprr_up1,
    kprr_cjs_dn1, kprr_cjs_up1,
    cjs_kdpa_dn1, cjs_kdpa_up1,
    kdpa_dir_dn1, kdpa_dir_up1,
    dir_jyp_dn1, dir_jyp_up1,
    jyp_cts_dn1, jyp_cts_up1,
    cts_mvg_dn1, cts_mvg_up1,
    mvg_jrt_mid1,
    jrt_mvf_mid1,
    mvf_krpu_dn1, mvf_krpu_up1,
    krpu_dmrt_dn1, krpu_dmrt_up1,
    dmrt_dmnj_dn1, dmrt_dmnj_up1,
    dmnj_bgua_dn1, dmnj_bgua_up1,
    bgua_kkgm_mid1,
    kkgm_lkmr_mid1,
    lkmr_sgrm_dn1, lkmr_sgrm_up1,
    sgrm_tkri_dn1, sgrm_tkri_up1,
    tkri_rul_mid1,
    rul_llgm_mid1,
    llgm_blmk_mid1,
    blmk_skpi_mid1,
    skpi_ktga_mid1,
    ktga_sprd_mid1,
    sprd_rgda_dn1, sprd_rgda_up1,
      sprd_rgda_mid1,
    rgda_ldx_dn1, rgda_ldx_up1,
    ldx_jmpt_dn1, ldx_jmpt_up1,
    jmpt_knrt_dn1, jmpt_knrt_up1, 
    jmpt_knrt_mid1,
    knrt_gmda_dn1, knrt_gmda_up1,
      knrt_gmda_mid1,
    gmda_pvp_dn1, gmda_pvp_up1,
      gmda_pvp_mid1,
    pvp_snm_dn1, pvp_snm_up1,
    snm_vbl_dn1, snm_vbl_up1,
    vbl_dnv_dn1, vbl_dnv_up1,
    dnv_kmx_dn1, dnv_kmx_up1,
    kmx_gpi_dn1, kmx_gpi_up1,
    gpi_grbl_dn1, gpi_grbl_up1,
    grbl_gtlm_dn1, grbl_gtlm_up1,
]

# populate_connections(blocksections_list, station_dict, stations_list)

