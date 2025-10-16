from typing import Optional, Union, List, Dict, Tuple, Any
import numpy as np
from sklearn.model_selection import train_test_split
import optuna
from scipy.interpolate import BSpline, interp1d
from sklearn.metrics import accuracy_score, roc_auc_score, mean_squared_error
import warnings
from .models import LightGBMModelWrapper
from numba import jit
import pywt
from scipy import fft

def generate_bspline_pattern(control_points: List[float], width: int) -> np.ndarray:
    degree = 3
    n_cp = len(control_points)
    knots = np.concatenate([np.zeros(degree + 1), np.linspace(0, 1, n_cp - degree + 1)[1:-1], np.ones(degree + 1)])
    return BSpline(knots, np.asarray(control_points), degree)(np.linspace(0, 1, width))

def apply_transformation(series: np.ndarray, transform_type: str, target_length: int) -> np.ndarray:
    if transform_type == 'raw':
        return series
    elif transform_type == 'wavelet_db4_level4':
        coeffs = pywt.wavedec(series, 'db4', level=4, mode='periodization')
        concatenated = np.concatenate(coeffs)
        x_old = np.linspace(0, 1, len(concatenated))
        x_new = np.linspace(0, 1, target_length)
        return interp1d(x_old, concatenated, kind='linear')(x_new)
    elif transform_type == 'wavelet_db4_level3':
        coeffs = pywt.wavedec(series, 'db4', level=3, mode='periodization')
        concatenated = np.concatenate(coeffs)
        x_old = np.linspace(0, 1, len(concatenated))
        x_new = np.linspace(0, 1, target_length)
        return interp1d(x_old, concatenated, kind='linear')(x_new)
    elif transform_type == 'fft_magnitude':
        magnitude = np.abs(fft.fft(series))[:len(series)//2]
        x_old = np.linspace(0, 1, len(magnitude))
        x_new = np.linspace(0, 1, target_length)
        return interp1d(x_old, magnitude, kind='linear')(x_new)
    elif transform_type == 'fft_power':
        power = np.abs(fft.fft(series))**2
        power = power[:len(power)//2]
        x_old = np.linspace(0, 1, len(power))
        x_new = np.linspace(0, 1, target_length)
        return interp1d(x_old, power, kind='linear')(x_new)
    elif transform_type == 'derivative':
        deriv = np.gradient(series)
        return deriv
    return series

@jit(nopython=True)
def _calculate_distances(series_data, pattern, pattern_width, pattern_start, shift_tolerance):
    n_samples, n_time_points = series_data.shape
    min_dists = np.full(n_samples, np.inf)
    
    min_start = max(0, pattern_start - shift_tolerance)
    max_start = min(n_time_points - pattern_width, pattern_start + shift_tolerance)
    
    for i in range(n_samples):
        # Initialize min_dist for the current sample
        min_dist_i = np.inf
        for start in range(min_start, max_start + 1):
            dist = 0.0
            for j in range(pattern_width):
                dist += (series_data[i, start + j] - pattern[j]) ** 2
            dist = np.sqrt(dist / pattern_width)
            if dist < min_dist_i:
                min_dist_i = dist
        min_dists[i] = min_dist_i
    return min_dists

def pattern_to_features(input_series: np.ndarray, pattern_width: int, pattern_start: int, series_index: int = 0, shift_tolerance: int = 0, control_points: Optional[List[float]] = None, pattern: Optional[np.ndarray] = None) -> np.ndarray:
    if pattern is None:
        if control_points is None:
            raise ValueError("Either control_points or pattern must be provided.")
        pattern = generate_bspline_pattern(control_points, pattern_width)
    
    # This check can be simplified as numba handles boundaries
    if pattern_start + pattern_width > input_series.shape[2] and shift_tolerance == 0:
        return np.full(input_series.shape[0], np.inf)
        
    series_data = input_series[:, series_index, :]
    return _calculate_distances(series_data, pattern, pattern_width, pattern_start, shift_tolerance)

def evaluate_model_performance(model, metric, cached_data):
    X_train, X_val, y_train_split, y_val = cached_data
    model = model.clone()
    model.fit(X_train, y_train_split, X_val, y_val)
    if metric == 'accuracy': return accuracy_score(y_val, model.predict(X_val))
    if metric == 'rmse': return np.sqrt(mean_squared_error(y_val, model.predict(X_val)))
    y_pred = model.predict_proba(X_val)
    return roc_auc_score(y_val, y_pred) if len(np.unique(y_val)) == 2 else roc_auc_score(y_val, y_pred, multi_class='ovr', average='macro')

def feature_extraction(input_series_train: Union[np.ndarray, List], 
                      y_train: np.ndarray, 
                      input_series_test: Optional[Union[np.ndarray, List]] = None,
                      initial_features: Optional[Tuple[np.ndarray, np.ndarray]] = None,
                      model: Optional[Any] = None, 
                      metric: str = 'auc', 
                      val_size: float = 0.2,
                      n_trials: int = 300, 
                      n_control_points: int = 5,
                      shift_tolerance: int = 0,
                      show_progress: bool = True) -> Dict[str, Any]:
    
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    if isinstance(input_series_train, list):
        input_series_train = np.stack([x.values if hasattr(x, 'values') else x for x in input_series_train], axis=1)
    if isinstance(input_series_test, list):
        input_series_test = np.stack([x.values if hasattr(x, 'values') else x for x in input_series_test], axis=1)
    n_input_series, n_time_points = input_series_train.shape[1], input_series_train.shape[2]
    data_min, data_max = np.min(input_series_train), np.max(input_series_train)
    
    transform_types = ['raw', 'wavelet_db4_level4', 'wavelet_db4_level3', 'fft_magnitude', 'fft_power', 'derivative']
    transformed_train = {}
    for t_type in transform_types:
        transformed = np.zeros_like(input_series_train)
        for i in range(input_series_train.shape[0]):
            for j in range(n_input_series):
                transformed[i, j, :] = apply_transformation(input_series_train[i, j, :], t_type, n_time_points)
        transformed_train[t_type] = transformed
    
    model_features_list = [initial_features[0]] if initial_features else []
    y_train = np.asarray(y_train).flatten()
    
    if metric != 'rmse':
        unique_targets = np.unique(y_train)
        if len(unique_targets) > 2 and not np.array_equal(unique_targets, np.arange(len(unique_targets))):
            y_train = np.array([{v: i for i, v in enumerate(unique_targets)}[y] for y in y_train])
        elif len(unique_targets) == 2 and not np.array_equal(unique_targets, [0, 1]):
            y_train = (y_train == unique_targets[1]).astype(int)
    
    model_type = 'regression' if metric == 'rmse' else 'classification'
    n_classes = len(np.unique(y_train)) if model_type == 'classification' and len(np.unique(y_train)) > 2 else 2
    fast_model = LightGBMModelWrapper(model_type, n_classes=n_classes)

    if model is None:
        model = fast_model
    
    train_idx, val_idx = train_test_split(np.arange(len(y_train)), test_size=val_size, random_state=42)
    overall_best_score = float('inf') if metric == 'rmse' else -float('inf')
    y_train_split, y_val = y_train[train_idx], y_train[val_idx]
    input_series_train_split, input_series_val = input_series_train[train_idx], input_series_train[val_idx]
    
    transformed_train_split = {t_type: transformed_train[t_type][train_idx] for t_type in transform_types}
    transformed_val = {t_type: transformed_train[t_type][val_idx] for t_type in transform_types}
    
    def objective(trial):
        series_idx = trial.suggest_int('series_index', 0, n_input_series - 1) if n_input_series > 1 else 0
        cps = [trial.suggest_float(f'cp{i}', 0, 1) for i in range(n_control_points)]
        width = trial.suggest_int('pattern_width', max(3, n_time_points // 4), n_time_points - 1)
        start = trial.suggest_int('pattern_start', 0, n_time_points // 2)
        shift = trial.suggest_int('shift_tolerance', 0, shift_tolerance) if shift_tolerance > 0 else 0
        pattern_mode = trial.suggest_categorical('pattern_mode', ['relative', 'absolute'])
        transform_type = trial.suggest_categorical('transform_type', transform_types)
        if start + width > n_time_points: return float('-inf') if metric != 'rmse' else float('inf')
        
        current_cps = [cp * (data_max - data_min) + data_min for cp in cps] if pattern_mode == 'absolute' else cps
        pattern = generate_bspline_pattern(current_cps, width)

        train_feat = pattern_to_features(transformed_train_split[transform_type], width, start, series_idx, shift, pattern=pattern)
        val_feat = pattern_to_features(transformed_val[transform_type], width, start, series_idx, shift, pattern=pattern)

        X_train = np.column_stack([base_X_train, train_feat]) if base_X_train.size > 0 else train_feat.reshape(-1, 1)
        X_val = np.column_stack([base_X_val, val_feat]) if base_X_val.size > 0 else val_feat.reshape(-1, 1)

        cached_data = (X_train, X_val, y_train_split, y_val)
        return evaluate_model_performance(fast_model, metric, cached_data)
    
    extracted_patterns = []
    while True:
        base_X_train = np.column_stack([f[train_idx] for f in model_features_list]) if model_features_list else np.empty((len(train_idx), 0))
        base_X_val = np.column_stack([f[val_idx] for f in model_features_list]) if model_features_list else np.empty((len(val_idx), 0))
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=optuna.exceptions.ExperimentalWarning)
            study = optuna.create_study(
                direction='minimize' if metric == 'rmse' else 'maximize',
                sampler=optuna.samplers.TPESampler(n_startup_trials=50, warn_independent_sampling=False, multivariate=True),
                pruner=optuna.pruners.HyperbandPruner()
            )
        study.optimize(objective, n_trials=n_trials, show_progress_bar=show_progress, n_jobs=-1)
        score = study.best_trial.value
        improved = not extracted_patterns or (metric == 'rmse' and score < overall_best_score) or (metric != 'rmse' and score > overall_best_score)
        if not improved: break
        params = study.best_trial.params
        series_idx = params.get('series_index', 0)
        cps = [params[f'cp{i}'] for i in range(n_control_points)]
        start, width = params['pattern_start'], params['pattern_width']
        shift = params.get('shift_tolerance', 0)
        pattern_mode = params.get('pattern_mode', 'relative')
        transform_type = params.get('transform_type', 'raw')
        
        current_cps = [cp * (data_max - data_min) + data_min for cp in cps] if pattern_mode == 'absolute' else cps
        pattern_array = generate_bspline_pattern(current_cps, width)
        
        extracted_patterns.append({'pattern': pattern_array, 'start': start, 'width': width, 'series_idx': series_idx, 'control_points': cps, 'shift_tolerance': shift, 'pattern_mode': pattern_mode, 'transform_type': transform_type})
        
        model_features_list.append(pattern_to_features(transformed_train[transform_type], width, start, series_idx, shift, control_points=current_cps))
        overall_best_score = score
    
    model_features = np.column_stack(model_features_list) if model_features_list else np.empty((len(y_train), 0))
    model.fit(model_features[train_idx], y_train[train_idx], model_features[val_idx], y_train[val_idx])
    
    test_features = None
    if input_series_test is not None:
        transformed_test = {}
        for t_type in transform_types:
            transformed = np.zeros_like(input_series_test)
            for i in range(input_series_test.shape[0]):
                for j in range(n_input_series):
                    transformed[i, j, :] = apply_transformation(input_series_test[i, j, :], t_type, n_time_points)
            transformed_test[t_type] = transformed
        
        test_feats = []
        for p in extracted_patterns:
            cps = p['control_points']
            if p['pattern_mode'] == 'absolute':
                scaled_cps = [c * (data_max - data_min) + data_min for c in cps]
            else:
                scaled_cps = cps
            transform_type = p.get('transform_type', 'raw')
            test_feats.append(pattern_to_features(transformed_test[transform_type], p['width'], p['start'], p['series_idx'], p['shift_tolerance'], control_points=scaled_cps))

        all_test_feats = ([initial_features[1]] if initial_features else []) + test_feats
        test_features = np.column_stack(all_test_feats) if all_test_feats else np.empty((len(input_series_test), 0))
    return {'patterns': extracted_patterns, 'train_features': model_features, 'test_features': test_features, 'model': model}