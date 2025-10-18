# Dependencies (install psann from PyPI)
import importlib
import subprocess
import sys


def _maybe_install(module: str, package: str | None = None) -> None:
    try:
        importlib.import_module(module)
    except ImportError:
        target = package or module
        print(f"[deps] Installing {target}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", target])


_DEPENDENCIES = [
    ("psann", "psann"),
    ("torch", "torch"),
    ("torchvision", "torchvision"),
    ("torchaudio", "torchaudio"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("sklearn", "scikit-learn"),
]
for module_name, package_name in _DEPENDENCIES:
    _maybe_install(module_name, package_name)



# Configuration â€” adjust as needed
TASKS = ['jena', 'beijing', 'eaf']  # choose any subset of: 'jena', 'beijing', 'eaf'
SEEDS = [7,8]                       # a couple of light replications
EPOCHS = 10                         # keep small to stay light
DEVICE = 'auto'                     # 'auto' | 'cpu' | 'cuda'
PR_SNAPSHOTS = False                # set True to record end Jacobian PR on Jena


# Light test runner (bundled version of colab_tests_light/run_light_probes.py)
import math, os, random, json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from psann.conv import PSANNConv1dNet
from psann.nn import PSANNNet
from psann.utils import choose_device, seed_all as psann_seed_all
from sklearn.metrics import r2_score, mean_absolute_error

try:
    from IPython.display import display
except ImportError:
    display = None

def _ensure_torch_dynamo_stub() -> None:
    import importlib, sys, types

    try:
        dynamo = importlib.import_module("torch._dynamo")
    except Exception:
        dynamo = None
    if dynamo is not None and getattr(dynamo, "disable", None):
        return

    stub = types.ModuleType("torch._dynamo")

    def _disable(fn=None, recursive=True):
        if fn is None:
            def decorator(f):
                return f
            return decorator
        return fn

    stub.disable = _disable
    sys.modules["torch._dynamo"] = stub
    torch._dynamo = stub  # type: ignore[attr-defined]


_ensure_torch_dynamo_stub()

PROJECT_ROOT = Path(os.getcwd())
DATA_ROOT = Path(os.getenv('PSANN_DATA_ROOT', PROJECT_ROOT / 'datasets')).resolve()
RESULTS_ROOT = (PROJECT_ROOT / 'colab_results_light').resolve()
RESULTS_ROOT.mkdir(parents=True, exist_ok=True)


REQUIRED_DATASETS = [
    DATA_ROOT / 'Beijing Air Quality',
    DATA_ROOT / 'Industrial Data from the Electric Arc Furnace',
]


def _datasets_ready() -> bool:
    for path in REQUIRED_DATASETS:
        if not path.exists():
            return False
        if path.is_dir() and not any(path.rglob('*')):
            return False
    return True
JENA_ZIP_URL = 'https://storage.googleapis.com/tensorflow/tf-keras-datasets/jena_climate_2009_2016.csv.zip'

def ensure_jena_dataset() -> Path:
    base = DATA_ROOT / 'Jena Climate 2009-2016'
    csv = base / 'jena_climate_2009_2016.csv'
    if csv.exists():
        return csv
    base.mkdir(parents=True, exist_ok=True)
    tmp_zip = base / 'jena_climate_2009_2016.csv.zip'
    import urllib.request, zipfile
    try:
        print(f'[data] Downloading Jena Climate dataset to {base} ...')
        urllib.request.urlretrieve(JENA_ZIP_URL, tmp_zip)
        with zipfile.ZipFile(tmp_zip, 'r') as zf:
            zf.extractall(base)
    except Exception as exc:
        print(f'[warn] Failed to download Jena dataset: {exc}')
    finally:
        if tmp_zip.exists():
            tmp_zip.unlink()
    if csv.exists():
        return csv
    matches = list(base.glob('**/jena_climate_2009_2016.csv'))
    if matches:
        return matches[0]
    raise FileNotFoundError(f'Could not locate Jena climate CSV under {base}')

def seed_all(seed: int) -> None:
    psann_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def pick_device(arg: str) -> torch.device:
    return choose_device(arg)

def _fix_backslash_artifacts(root: Path) -> None:
    # Move files like 'datasets\Human Activity Recognition\...txt' into proper subfolders under datasets/
    for leftover in root.iterdir():
        name = leftover.name
        if "\\\\" in name and name.lower().startswith('datasets'):
            # Normalise to forward slashes and build destination path
            rel = Path(*Path(name.replace('\\', '/')).parts)
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                leftover.replace(dest)
                print(f'[fix] Moved stray {leftover} -> {dest}')
            except Exception as e:
                print(f'[warn] Could not move {leftover}: {e}')

def maybe_extract_datasets_zip() -> None:
    # First, fix any previously extracted stray files with backslashes in their names
    _fix_backslash_artifacts(PROJECT_ROOT)
    # Skip extraction only when required datasets are already present
    if _datasets_ready():
        return
    zip_path = PROJECT_ROOT / 'datasets.zip'
    if not zip_path.exists():
        print(f'[warn] Required datasets missing under {DATA_ROOT} and datasets.zip not found.')
        return
    import zipfile
    print(f'[info] Extracting {zip_path} to {PROJECT_ROOT}/datasets (robust normalisation)...')
    with zipfile.ZipFile(zip_path, 'r') as z:
        for zi in z.infolist():
            name = zi.filename
            # Normalise path separators and strip leading './'
            norm = name.replace('\\', '/').lstrip('./')
            parts = [p for p in norm.split('/') if p not in ('',)]
            if not parts:
                continue
            if parts[0].lower() != 'datasets':
                parts = ['datasets'] + parts
            dest = PROJECT_ROOT.joinpath(*parts)
            if zi.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(zi) as src, open(dest, 'wb') as f:
                    f.write(src.read())
    # Final pass to relocate any leftover stray files created by other tools
    _fix_backslash_artifacts(PROJECT_ROOT)

class PSANNConvSpine(nn.Module):
    def __init__(self, in_ch: int, hidden: int, depth: int, kernel_size: int, horizon: int, aggregator: str='last'):
        super().__init__()
        self.aggregator = aggregator
        self.core = PSANNConv1dNet(
            in_channels=in_ch,
            out_dim=hidden,
            hidden_layers=depth,
            conv_channels=hidden,
            hidden_channels=hidden,
            kernel_size=kernel_size,
            segmentation_head=True,
        )
        self.head = nn.Linear(hidden, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.core(x.transpose(1,2))
        if self.aggregator == 'last':
            pooled = features[:, :, -1]
        else:
            pooled = features.mean(dim=-1)
        return self.head(pooled)

class MLPRegressor(nn.Module):
    def __init__(self, in_dim: int, hidden: int, depth: int, out_dim: int):
        super().__init__()
        self.net = PSANNNet(
            input_dim=in_dim,
            output_dim=out_dim,
            hidden_layers=depth,
            hidden_units=hidden,
            hidden_width=hidden,
            activation_type='relu',
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, f = x.shape
        return self.net(x.reshape(b, t * f))

@dataclass
class TrainSpec:
    model: str
    hidden: int
    depth: int
    kernel_size: int = 5
    epochs: int = 10
    lr: float = 1e-3
    batch_size: int = 256
    patience: int = 3

def count_params(m: nn.Module) -> int: return sum(p.numel() for p in m.parameters() if p.requires_grad)

def train_regressor(model, train_X, train_y, val_X, val_y, spec: TrainSpec, device):
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=spec.lr)
    loss_fn = nn.MSELoss()
    tX, ty = torch.from_numpy(train_X).float().to(device), torch.from_numpy(train_y).float().to(device)
    vX, vy = torch.from_numpy(val_X).float().to(device), torch.from_numpy(val_y).float().to(device)
    best_state, best_val, bad = None, math.inf, 0
    n = tX.size(0)
    for ep in range(spec.epochs):
        model.train()
        perm = torch.randperm(n, device=device)
        for i in range(0, n, spec.batch_size):
            idx = perm[i:i+spec.batch_size]
            xb, yb = tX.index_select(0, idx), ty.index_select(0, idx)
            opt.zero_grad(); loss = loss_fn(model(xb), yb); loss.backward(); opt.step()
        model.eval();
        with torch.no_grad(): vloss = loss_fn(model(vX), vy).item()
        if vloss < best_val - 1e-6: best_val, best_state, bad = vloss, {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}, 0
        else: bad += 1
        if bad >= spec.patience: break
    if best_state is not None: model.load_state_dict(best_state)
    return model, {'best_val_mse': best_val}

def evaluate_regressor(model, X, y, device):
    model.eval(); X_t = torch.from_numpy(X).float().to(device)
    with torch.no_grad(): pred = model(X_t).cpu().numpy()
    rmse = float(np.sqrt(np.mean((pred - y)**2)))
    mae = float(mean_absolute_error(y.reshape(-1), pred.reshape(-1)))
    r2  = float(r2_score(y.reshape(-1), pred.reshape(-1)))
    return {'rmse': rmse, 'mae': mae, 'r2': r2}

def build_windows(frame: pd.DataFrame, feature_cols: List[str], target_col: str, context: int, horizon: int, stride: int = 1, limit: Optional[int] = None):
    X, y = frame[feature_cols].values.astype(np.float32), frame[target_col].values.astype(np.float32)
    T = len(frame); idxs = [(t-context, t, t, t+horizon) for t in range(context, T-horizon+1, stride)]
    if limit is not None: idxs = idxs[:limit]
    Xw = np.stack([X[s:e,:] for (s,e,_,__) in idxs], axis=0)
    Yw = np.stack([y[s2:e2] for (_,__,s2,e2) in idxs], axis=0)
    return Xw, Yw

def split_train_val_test(X, y, val_frac=0.15, test_frac=0.15):
    n = X.shape[0]; n_test = int(n*test_frac); n_val = int(n*val_frac); n_train = n - n_val - n_test
    return X[:n_train], y[:n_train], X[n_train:n_train+n_val], y[n_train:n_train+n_val], X[n_train+n_val:], y[n_train+n_val:]

def load_jena_light(context=72, horizon=36, subset_days=120):
    # Robustly resolve Jena folder and CSV (handles hyphen/en-dash variants)
    def _norm(s: str) -> str:
        trans = {
            'â€“': '-',  # en dash
            'â€”': '-',  # em dash
            'â€‘': '-',  # non-breaking hyphen
            'âˆ’': '-',  # minus sign
        }
        return ''.join(trans.get(ch, ch) for ch in s).lower()

    base = DATA_ROOT / 'Jena Climate 2009-2016'
    csv = base / 'jena_climate_2009_2016.csv'
    if not csv.exists():
        try:
            csv = ensure_jena_dataset()
        except FileNotFoundError:
            csv = None
    if csv is None or not Path(csv).exists():
        # Search any directory under DATA_ROOT that looks like Jena Climate
        candidates = [d for d in DATA_ROOT.iterdir() if d.is_dir() and 'jena' in _norm(d.name)]
        found = None
        for d in candidates:
            # Exact CSV name first
            hits = list(d.rglob('jena_climate_2009_2016.csv'))
            if hits:
                found = hits[0]; break
            # Fallback: any CSV containing 'jena' and '2016'
            hits = list(d.rglob('*jena*climate*2016*.csv'))
            if hits:
                found = hits[0]; break
        if found is None:
            raise FileNotFoundError(f'Could not find Jena climate CSV under {DATA_ROOT}')
        csv = found
    df = pd.read_csv(csv)
    target_col = next((c for c in df.columns if c.strip().lower().startswith('t ') or 'degc' in c.lower()), None)
    if target_col is None: raise RuntimeError('Could not find temperature column (e.g., T (degC))')
    num_df = df.select_dtypes(include=[np.number]).copy()
    if subset_days is not None: num_df = num_df.tail(subset_days * 144)
    num_df = (num_df - num_df.mean()) / (num_df.std().replace(0, 1.0))
    feature_cols = list(num_df.columns)
    Xw, Yw = build_windows(num_df, feature_cols, target_col, context, horizon)
    return split_train_val_test(Xw, Yw)

def load_beijing_light(station_name='Guanyuan', context=24, horizon=6, subset_days=120):
    base = DATA_ROOT / 'Beijing Air Quality'
    station_file = None
    for p in base.glob('PRSA_Data_*_20130301-20170228.csv'):
        if station_name.lower() in p.name.lower(): station_file = p; break
    if station_file is None: raise FileNotFoundError(f'Could not find station file containing {station_name}')
    df = pd.read_csv(station_file)
    target_col = 'PM2.5' if 'PM2.5' in df.columns else df.select_dtypes(include=[np.number]).columns[0]
    num_df = df.select_dtypes(include=[np.number]).copy().ffill().bfill().fillna(0.0)
    if subset_days is not None: num_df = num_df.tail(subset_days * 24)
    num_df = (num_df - num_df.mean()) / (num_df.std().replace(0, 1.0))
    feature_cols = list(num_df.columns)
    Xw, Yw = build_windows(num_df, feature_cols, target_col, context, horizon)
    return split_train_val_test(Xw, Yw)

def load_eaf_temp_lite(context=16, horizon=1, heats_limit=5, min_rows=120):
    path = DATA_ROOT / 'Industrial Data from the Electric Arc Furnace' / 'eaf_temp.csv'
    df = pd.read_csv(path)
    if not {'HEATID','DATETIME','TEMP'}.issubset(df.columns):
        raise RuntimeError('Missing expected columns in eaf_temp.csv')
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce')
    df = df.dropna(subset=['DATETIME']).sort_values(['HEATID','DATETIME'])
    heats_df = df.groupby('HEATID').size().reset_index(name='n').sort_values('n', ascending=False)
    selected = heats_df.query('n >= @min_rows').head(heats_limit)
    if selected.empty:
        fallback = heats_df.head(heats_limit)
        if fallback.empty:
            raise RuntimeError('No heats found in eaf_temp.csv')
        print(f"[warn] No EAF heats with >= {min_rows} rows; using top {len(fallback)} heats with >= {int(fallback['n'].min())} rows instead.")
        selected = fallback
    parts = []
    for hid in selected['HEATID']:
        seg = df[df['HEATID'] == hid].copy()
        num_cols = ['TEMP'] + (['VALO2_PPM'] if 'VALO2_PPM' in seg.columns else [])
        seg_num = seg[num_cols]
        seg_num = (seg_num - seg_num.mean()) / (seg_num.std().replace(0, 1.0))
        Xw, Yw = build_windows(seg_num, feature_cols=num_cols, target_col='TEMP', context=context, horizon=horizon)
        if Xw.size == 0:
            continue
        parts.append((Xw, Yw))
    if not parts:
        raise RuntimeError('No EAF heats with sufficient rows found for lite run')
    X = np.concatenate([p[0] for p in parts], axis=0)
    Y = np.concatenate([p[1] for p in parts], axis=0)
    return split_train_val_test(X, Y)

def jacobian_pr(model: nn.Module, X_sample: np.ndarray, device: torch.device):
    model.eval()
    x = torch.from_numpy(X_sample).float().to(device)
    x.requires_grad_(True)
    y = model(x)
    grads = torch.autograd.grad(y.sum(), x, create_graph=False, retain_graph=False)[0]
    J = grads.detach().cpu().numpy().reshape(x.size(0), -1)
    try: s = np.linalg.svd(J, compute_uv=False)
    except np.linalg.LinAlgError:
        M = J @ J.T; evals, _ = np.linalg.eigh(M); s = np.sqrt(np.clip(evals, 0, None))[::-1]
    top_sv = float(s[0]) if s.size>0 else 0.0; sum_sv = float(s.sum()); pr = float((sum_sv**2)/(np.sum(s**2)+1e-8))
    return top_sv, sum_sv, pr

def run_light_task(task: str, seeds: List[int], device: torch.device, epochs: int, pr_snapshots: bool, metrics_rows: List[dict]):
    if task == 'jena':
        train_X, train_y, val_X, val_y, test_X, test_y = load_jena_light(72,36,120)
        in_ch, horizon = train_X.shape[-1], train_y.shape[-1]
        specs = [('psann_conv', TrainSpec('psann_conv', hidden=48, depth=2, kernel_size=5, epochs=epochs)), ('mlp', TrainSpec('mlp', hidden=64, depth=2, epochs=epochs))]
        for seed in seeds:
            seed_all(seed)
            for name, spec in specs:
                model = PSANNConvSpine(in_ch, spec.hidden, spec.depth, spec.kernel_size, horizon) if spec.model=='psann_conv' else MLPRegressor(train_X.shape[1]*in_ch, spec.hidden, spec.depth, horizon)
                model, info = train_regressor(model, train_X, train_y, val_X, val_y, spec, device)
                test_metrics = evaluate_regressor(model, test_X, test_y, device)
                metrics_rows.append({'task':'jena_light','model':name,'seed':seed,'params':count_params(model), **info, **test_metrics})
                if pr_snapshots and name=='psann_conv':
                    idx = np.random.choice(test_X.shape[0], size=min(32, test_X.shape[0]), replace=False)
                    top_sv, sum_sv, pr = jacobian_pr(model, test_X[idx], device)
                    pr_df = pd.DataFrame([{'task':'jena_light','model':name,'seed':seed,'phase':'end','top_sv':top_sv,'sum_sv':sum_sv,'pr':pr}])
                    pr_out = RESULTS_ROOT / 'jacobian_pr.csv'; mode = 'a' if pr_out.exists() else 'w'
                    pr_df.to_csv(pr_out, index=False, mode=mode, header=(mode=='w'))
    elif task == 'beijing':
        train_X, train_y, val_X, val_y, test_X, test_y = load_beijing_light('Guanyuan',24,6,120)
        in_ch, horizon = train_X.shape[-1], train_y.shape[-1]
        specs = [('psann_conv', TrainSpec('psann_conv', hidden=64, depth=2, kernel_size=5, epochs=epochs)), ('mlp', TrainSpec('mlp', hidden=96, depth=2, epochs=epochs))]
        for seed in seeds:
            seed_all(seed)
            for name, spec in specs:
                model = PSANNConvSpine(in_ch, spec.hidden, spec.depth, spec.kernel_size, horizon) if spec.model=='psann_conv' else MLPRegressor(train_X.shape[1]*in_ch, spec.hidden, spec.depth, horizon)
                model, info = train_regressor(model, train_X, train_y, val_X, val_y, spec, device)
                test_metrics = evaluate_regressor(model, test_X, test_y, device)
                metrics_rows.append({'task':'beijing_light','model':name,'seed':seed,'params':count_params(model), **info, **test_metrics})
    elif task == 'eaf':
        train_X, train_y, val_X, val_y, test_X, test_y = load_eaf_temp_lite(16,1,5,120)
        in_ch, horizon = train_X.shape[-1], train_y.shape[-1]
        specs = [('psann_conv', TrainSpec('psann_conv', hidden=32, depth=2, kernel_size=3, epochs=max(epochs,8))), ('mlp', TrainSpec('mlp', hidden=48, depth=2, epochs=max(epochs,8)))]
        for seed in seeds:
            seed_all(seed)
            for name, spec in specs:
                model = PSANNConvSpine(in_ch, spec.hidden, spec.depth, spec.kernel_size, horizon) if spec.model=='psann_conv' else MLPRegressor(train_X.shape[1]*in_ch, spec.hidden, spec.depth, horizon)
                model, info = train_regressor(model, train_X, train_y, val_X, val_y, spec, device)
                test_metrics = evaluate_regressor(model, test_X, test_y, device)
                metrics_rows.append({'task':'eaf_temp_lite','model':name,'seed':seed,'params':count_params(model), **info, **test_metrics})
    else:
        raise ValueError(f'Unknown task: {task}')

def run_all(tasks, seeds, epochs, device_str, pr_snapshots):
    maybe_extract_datasets_zip()
    device = pick_device(device_str)
    print(f'[env] DATA_ROOT={DATA_ROOT}')
    print(f'[env] RESULTS_ROOT={RESULTS_ROOT}')
    print(f'[env] device={device}')
    metrics_rows: List[dict] = []
    for task in tasks:
        print(f'[run] task={task}')
        run_light_task(task, seeds, device, epochs, pr_snapshots, metrics_rows)
    if metrics_rows:
        df = pd.DataFrame(metrics_rows)
        out = RESULTS_ROOT / 'metrics.csv'
        df.to_csv(out, index=False)
        head = df.head()
        if display is not None:
            display(head)
        else:
            print(head)
        print(f'[done] Wrote metrics to {out}')
    else:
        print('[warn] No metrics collected')






# Run
run_all(TASKS, SEEDS, EPOCHS, DEVICE, PR_SNAPSHOTS)