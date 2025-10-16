import wfdb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import neurokit2 as nk
from IPython.display import display
from ecgdetectors import Detectors
import sys

channel_names = ['I', 'II', 'III', 'AVR', 'AVL', 'AVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

def safe_divide(x, y):
    return np.divide(x, y, out=np.zeros_like(x), where=y!=0)

def load_raw_data(_df, _sampling_rate, _path):
    if _sampling_rate == 100:
        data = [wfdb.rdsamp(f"{_path}/{f}") for f in _df.filename_lr]
    else:
        data = [wfdb.rdsamp(f"{_path}/{f}") for f in _df.filename_hr]
    meta0 = data[0][1]
    data = np.array([signal for signal, meta in data])
    return data, meta0

def plot_and_rates(idxs: np.array, X: np.array, Y: pd.DataFrame, 
                                     sampling_rate: int, channels = np.arange(12, dtype = np.int32), 
                                     rpeak_style = 'nk', plot=False) -> dict:

  colors = px.colors.qualitative.Dark24
  for s_idx in idxs: # subject_index:
    X_subject = X[s_idx, :, :]
    scp_code = Y.scp_codes.iloc[s_idx]
    ecg_id = Y.index[s_idx]

    heart_rates = {}

    fig = go.Figure()
    for n_idx, idx in enumerate(channels):
      fig.add_trace(go.Scatter(x = np.arange(X_subject.shape[0]) / sampling_rate, y = X_subject[:,idx] + 2. * (len(channels) - n_idx), name = channel_names[idx], marker_color = colors[idx]))
      fig.add_trace(go.Scatter(x = np.arange(X_subject.shape[0]) / sampling_rate, y = np.zeros(X_subject.shape[0]) + 2. * (len(channels) - n_idx), marker_color = 'black', line = dict(width = 1.),  showlegend = False))
      
      # Estimate R-peaks:
      if rpeak_style == 'nk':
        _, rpeaks = nk.ecg_peaks(X_subject[:,idx], sampling_rate=sampling_rate)
        rpeaks = rpeaks['ECG_R_Peaks'].astype('float') / sampling_rate
      elif rpeak_style == 'hamilton':
        detectors = Detectors(sampling_rate)
        rpeaks = (np.array(detectors.hamilton_detector(X_subject[:,idx]))).astype('float')  / sampling_rate # np.hstack((np.zeros(10),
      elif rpeak_style == 'wvt':
        detectors = Detectors(sampling_rate)
        rpeaks = np.array(detectors.swt_detector(X_subject[:,idx])).astype('float') / sampling_rate
      else:
        sys.exit('Incorrect rpeak_style. Options: "nk", "hamilton", "wvt".')

      heart_rates[channel_names[idx]] = (rpeaks.shape[0] - 1) * sampling_rate / (rpeaks[-1] - rpeaks[0]) 

      for r in rpeaks:
        fig.add_trace(go.Scatter(x = r * np.ones(20), y = np.linspace(-1, 1, num = 20) + 2. * (len(channels) - n_idx), line = dict(color = 'grey'), showlegend = False))
    
    if plot:
      fig.update_layout(title = f'ECG id: {ecg_id}, scp: {scp_code} - R-peaks: grey', yaxis = dict(showticklabels=False))
      fig.show()
    display(pd.Series(heart_rates, name = 'heart_rates'))
    print("---------------------------------------------------------------------")
    return heart_rates
  

def vals_from_ecg(ecg, sampling_rate):
    _, rpeaks = nk.ecg_peaks(ecg, sampling_rate=sampling_rate)
    signal_cwt, waves_cwt = nk.ecg_delineate(ecg.copy(), 
                                            rpeaks, 
                                            sampling_rate=sampling_rate, 
                                            method="cwt", 
                                            show=False, 
                                            show_type='all')
    tpeaks = waves_cwt['ECG_T_Peaks']
    speaks = waves_cwt['ECG_S_Peaks']
    qpeaks = waves_cwt['ECG_Q_Peaks']
    _rpeaks = rpeaks['ECG_R_Peaks']

    # Minimum length where no nans
    min_len = min(len(tpeaks), len(speaks), len(qpeaks), len(_rpeaks))
    print(f"min len:{min_len}")
    print(f"len ecg:{len(ecg)}")
    print(f"tpeaks:{tpeaks}")
    print(f"speaks:{speaks}")
    print(f"qpeaks:{qpeaks}")

    # Find indices with NaN
    nan_tpeaks = np.where(np.isnan(tpeaks))
    nan_speaks = np.where(np.isnan(speaks))
    nan_qpeaks = np.where(np.isnan(qpeaks))
    nan_rpeaks = np.where(np.isnan(_rpeaks))
    # Total list of NaN indices
    
    s_tpeaks = np.array([ecg[i] for i in tpeaks[:min_len]])
    s_speaks = np.array([ecg[i] for i in speaks[:min_len]])
    s_qpeaks = np.array([ecg[i] for i in qpeaks[:min_len]])
    s_rpeaks = np.array([ecg[i] for i in _rpeaks[:min_len]])

    r_over_t = safe_divide(s_rpeaks, s_tpeaks)
    t_over_s = safe_divide(s_tpeaks, s_speaks)
    t_over_q = safe_divide(s_tpeaks, s_qpeaks)
    mean_r_over_t = np.nanmean(r_over_t)
    mean_t_over_s = np.nanmean(t_over_s)
    mean_t_over_q = np.nanmean(t_over_q)
    var_r_over_t = np.nanvar(r_over_t)
    var_t_over_s = np.nanvar(t_over_s)
    var_t_over_q = np.nanvar(t_over_q)

    # Heart rate from rpeaks
    heart_rate = (len(_rpeaks) - 1) * sampling_rate / (_rpeaks[-1] - _rpeaks[0])
    # Convert to BPM
    heart_rate = heart_rate * 60

    # Feature space:
    # 1. mean_r_over_t
    # 2. mean_t_over_s
    # 3. mean_t_over_q
    # 4. var_r_over_t
    # 5. var_t_over_s
    # 6. var_t_over_q
    # 7. heart_rate
    return_dict = {}
    return_dict['mean_r_over_t'] = mean_r_over_t
    return_dict['mean_t_over_s'] = mean_t_over_s
    return_dict['mean_t_over_q'] = mean_t_over_q
    return_dict['var_r_over_t'] = var_r_over_t
    return_dict['var_t_over_s'] = var_t_over_s
    return_dict['var_t_over_q'] = var_t_over_q
    return_dict['heart_rate'] = heart_rate
    return return_dict