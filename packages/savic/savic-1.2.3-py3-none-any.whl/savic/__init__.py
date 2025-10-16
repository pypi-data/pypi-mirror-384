import os
import numpy as np
import wget
import warnings
warnings.filterwarnings("ignore")

# ---------------------------
# Expected file sizes dictionary
# ---------------------------

file_sizes_models = {
    'GMM_C/GMM_C.png': 48100,
    'GMM_C/GMM_C_Brazil_4.png': 3594210,
    'GMM_C/GMM_C_covariances.npy': 1696,
    'GMM_C/GMM_C_means.npy': 352,
    'GMM_C/GMM_C_weights.npy': 160,
    'GMM_CA/GMM_CA.png': 64121,
    'GMM_CA/GMM_CA_Brazil_6.png': 1089962,
    'GMM_CA/GMM_CA_covariances.npy': 9536,
    'GMM_CA/GMM_CA_means.npy': 800,
    'GMM_CA/GMM_CA_weights.npy': 176,
    'GMM_CB/GMM_CB.png': 82851,
    'GMM_CB/GMM_CB_Brazil_8.png': 1196694,
    'GMM_CB/GMM_CB_covariances.npy': 12672,
    'GMM_CB/GMM_CB_means.npy': 1024,
    'GMM_CB/GMM_CB_weights.npy': 192,
    'GMM_CBA/GMM_CBA.png': 142428,
    'GMM_CBA/GMM_CBA_Brazil_14.png': 4463508,
    'GMM_CBA/GMM_CBA_Brazil_refined_12.png': 4009836,
    'GMM_CBA/GMM_CBA_covariances.npy': 40560,
    'GMM_CBA/GMM_CBA_means.npy': 2256,
    'GMM_CBA/GMM_CBA_refined.png': 113786,
    'GMM_CBA/GMM_CBA_weights.npy': 240,
    'xgbc_kca.json': 14293033,
    'xgbc_kca.png': 51725,
    'xgbc_kcb.json': 58960041,
    'xgbc_kcb.png': 76527,
    'xgbc_kcba.json': 16574099,
    'xgbc_kcba.png': 92406,
    'xgbc_sus_c.json': 1850667,
    'xgbc_sus_c.png': 40687,
    'xgbc_sus_ca.json': 11984789,
    'xgbc_sus_ca.png': 29898,
    'xgbc_sus_cb.json': 18950584,
    'xgbc_sus_cb.png': 38598,
    'xgbc_sus_cba.json': 30488776,
    'xgbc_sus_cba.png': 43568,
    'xgbr_c.json': 16387983,
    'xgbr_c.png': 91188,
    'xgbr_ca_c0_a1_k0.json': 45454962,
    'xgbr_ca_c0_a1_k0.png': 108944,
    'xgbr_ca_c1_a0_k0.json': 16626577,
    'xgbr_ca_c1_a0_k0.png': 92845,
    'xgbr_ca_c1_a1_k0.json': 12857830,
    'xgbr_ca_c1_a1_k0.png': 99268,
    'xgbr_ca_c1_a1_k1.json': 3712066,
    'xgbr_ca_c1_a1_k1.png': 118761,
    'xgbr_cba_c0_b0_a1.json': 75864632,
    'xgbr_cba_c0_b0_a1.png': 113565,
    'xgbr_cba_c0_b1_a0_k0.json': 26606376,
    'xgbr_cba_c0_b1_a0_k0.png': 92448,
    'xgbr_cba_c0_b1_a0_k1.json': 16586299,
    'xgbr_cba_c0_b1_a0_k1.png': 93464,
    'xgbr_cba_c0_b1_a1.json': 23243410,
    'xgbr_cba_c0_b1_a1.png': 106928,
    'xgbr_cba_c1_b0_a0.json': 50577428,
    'xgbr_cba_c1_b0_a0.png': 82779,
    'xgbr_cba_c1_b0_a1.json': 24188460,
    'xgbr_cba_c1_b0_a1.png': 106436,
    'xgbr_cba_c1_b1_a0.json': 62450387,
    'xgbr_cba_c1_b1_a0.png': 126609,
    'xgbr_cba_c1_b1_a1.json': 10690959,
    'xgbr_cba_c1_b1_a1.png': 115973,
    'xgbr_cb_c0_b1_k0.json': 49250105,
    'xgbr_cb_c0_b1_k0.png': 112469,
    'xgbr_cb_c0_b1_k1.json': 29677188,
    'xgbr_cb_c0_b1_k1.png': 94806,
    'xgbr_cb_c1_b0.json': 58917559,
    'xgbr_cb_c1_b0.png': 86685,
    'xgbr_cb_c1_b1.json': 72669964,
    'xgbr_cb_c1_b1.png': 143089,
}

# ---------------------------
# Download models
# ---------------------------

for name in MODEL_FILES:
    expected_size = file_sizes_models.get(name)
    download_if_missing(BASE_PATH_MODELS, BASE_URL_MODELS, name, expected_size)

# ---------------------------
# Download tutorial files
# ---------------------------

for name in TUTORIAL_FILES:
    download_if_missing(BASE_PATH_TUTORIAL, BASE_URL_TUTORIAL, name)
