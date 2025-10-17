import math, statistics, itertools, concurrent.futures, shelve, platform, types
import logging, gc ,json ,mmap, threading, hashlib, os, weakref, ctypes, marshal
from collections import defaultdict, OrderedDict
from functools import wraps
from itertools import chain
from collections import deque

logging.basicConfig(level=logging.INFO)

def cached(_func=None, *, maxsize=128, threshold=64, mode=None):
    def make_hashable(obj):
        if isinstance(obj, (int, float, str, bytes, tuple, frozenset, type(None))):
            return obj
        if isinstance(obj, list):
            if len(obj) > threshold:
                return ("list", id(obj), len(obj))
            return tuple(map(make_hashable, obj))
        if isinstance(obj, set):
            if len(obj) > threshold:
                return ("set", id(obj), len(obj))
            return frozenset(map(make_hashable, obj))
        if isinstance(obj, dict):
            if len(obj) > threshold:
                return ("dict", id(obj), len(obj))
            return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
        try:
            return hashlib.md5(repr(obj).encode()).hexdigest()
        except Exception:
            return str(id(obj))

    def decorator(func):
        cache = OrderedDict()
        jit_cache = {}
        lock = threading.RLock()
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (
                tuple(map(make_hashable, args)),
                tuple(sorted((k, make_hashable(v)) for k, v in kwargs.items()))
            )
            with lock:
                if key in cache:
                    cache.move_to_end(key)
                    return cache[key]

            # Mode JIT aktif → compile fungsi jadi bytecode & simpan hasil
            if mode == "jit":
                code = func.__code__
                code_bytes = marshal.dumps(code)
                hash_key = hashlib.sha1(code_bytes).hexdigest()
                if hash_key not in jit_cache:
                    compiled = types.FunctionType(code, func.__globals__, func.__name__)
                    jit_cache[hash_key] = compiled
                optimized_func = jit_cache[hash_key]
                result = optimized_func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            with lock:
                cache[key] = result
                if len(cache) > maxsize:
                    cache.popitem(last=False)
            return result
        return wrapper

    # support: @cached, @cached(), dan @cached("jit")
    if isinstance(_func, str) and _func.lower() == "jit":
        return lambda f: decorator(f)
    if callable(_func):
        return decorator(_func)
    return decorator
    
# === 🔧 Scaling (ganti StandardScaler) ===
def scale_data(data):
    """Manual StandardScaler pakai pure Python"""
    n = len(data)
    m = len(data[0])
    means = [sum(row[j] for row in data) / n for j in range(m)]
    stdevs = [
        math.sqrt(sum((row[j] - means[j]) ** 2 for row in data) / n)
        for j in range(m)
    ]
    scaled = [
        [(row[j] - means[j]) / (stdevs[j] if stdevs[j] != 0 else 1) for j in range(m)]
        for row in data
    ]
    return scaled

# === 🔧 Preprocessing Otomatis ===
def preprocess_data(data, n_jobs=-1, optimizer_args=None):
    # --- Konversi ke list of list jika input masih list of scalars ---
    if isinstance(data[0], (int, float)):
        data = [[x] for x in data]
    n_samples = len(data)
    n_features = len(data[0]) if data else 0

    # === Standard Scaler manual (setara fit_transform sklearn) ===
    def scale_batch(batch):
        cols = list(zip(*batch))
        means = [statistics.mean(col) for col in cols]
        stdevs = [statistics.pstdev(col) if statistics.pstdev(col) > 0 else 1.0 for col in cols]
        scaled = [[(x - m) / s for x, m, s in zip(row, means, stdevs)] for row in batch]
        return scaled
    if n_samples > 1000:
        batch_size = 200
        batches = [data[i:i + batch_size] for i in range(0, n_samples, batch_size)]
        # parallel pakai concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=None if n_jobs == -1 else n_jobs) as executor:
            scaled_batches = list(executor.map(scale_batch, batches))
        data_scaled = list(itertools.chain.from_iterable(scaled_batches))
    else:
        data_scaled = scale_batch(data)

    # === Optimizer manual ===
    if optimizer_args is not None:
        w, b, grad_w, grad_b, layer_idx = optimizer_args[:5]
        method = optimizer_args[5] if len(optimizer_args) > 5 else "sgd"
        learning_rate = optimizer_args[6] if len(optimizer_args) > 6 else 0.01
        beta1 = optimizer_args[7] if len(optimizer_args) > 7 else 0.9
        beta2 = optimizer_args[8] if len(optimizer_args) > 8 else 0.999
        epsilon = optimizer_args[9] if len(optimizer_args) > 9 else 1e-8
        state = optimizer_args[10] if len(optimizer_args) > 10 else defaultdict(dict)
        method = method.lower()
        if method == "sgd":
            w_new = [[wij - learning_rate * gwij for wij, gwij in zip(wrow, grow)] for wrow, grow in zip(w, grad_w)]
            b_new = [bj - learning_rate * gbj for bj, gbj in zip(b, grad_b)]

        elif method == "momentum":
            m_w, m_b = state["m_w"], state["m_b"]
            if layer_idx not in m_w:
                m_w[layer_idx] = [[0.0] * len(row) for row in grad_w]
                m_b[layer_idx] = [0.0] * len(grad_b)
            m_w[layer_idx] = [[beta1 * mwij + (1 - beta1) * gwij for mwij, gwij in zip(mrow, grow)]
                              for mrow, grow in zip(m_w[layer_idx], grad_w)]
            m_b[layer_idx] = [beta1 * mbj + (1 - beta1) * gbj for mbj, gbj in zip(m_b[layer_idx], grad_b)]
            w_new = [[wij - learning_rate * mwij for wij, mwij in zip(wrow, mrow)] for wrow, mrow in zip(w, m_w[layer_idx])]
            b_new = [bj - learning_rate * mbj for bj, mbj in zip(b, m_b[layer_idx])]
            state["m_w"], state["m_b"] = m_w, m_b

        elif method == "rmsprop":
            v_w, v_b = state["v_w"], state["v_b"]
            if layer_idx not in v_w:
                v_w[layer_idx] = [[0.0] * len(row) for row in grad_w]
                v_b[layer_idx] = [0.0] * len(grad_b)
            v_w[layer_idx] = [[beta2 * vwij + (1 - beta2) * (gwij ** 2) for vwij, gwij in zip(vrow, grow)]
                              for vrow, grow in zip(v_w[layer_idx], grad_w)]
            v_b[layer_idx] = [beta2 * vbj + (1 - beta2) * (gbj ** 2) for vbj, gbj in zip(v_b[layer_idx], grad_b)]
            w_new = [[wij - learning_rate * gwij / (math.sqrt(vwij) + epsilon)
                      for wij, gwij, vwij in zip(wrow, grow, vrow)]
                     for wrow, grow, vrow in zip(w, grad_w, v_w[layer_idx])]
            b_new = [bj - learning_rate * gbj / (math.sqrt(vbj) + epsilon)
                     for bj, gbj, vbj in zip(b, grad_b, v_b[layer_idx])]
            state["v_w"], state["v_b"] = v_w, v_b

        elif method == "adam":
            m_w, v_w, m_b, v_b = state["m_w"], state["v_w"], state["m_b"], state["v_b"]
            t = state.get("t", 1)
            if layer_idx not in m_w:
                m_w[layer_idx] = [[0.0] * len(row) for row in grad_w]
                v_w[layer_idx] = [[0.0] * len(row) for row in grad_w]
                m_b[layer_idx] = [0.0] * len(grad_b)
                v_b[layer_idx] = [0.0] * len(grad_b)
            m_w[layer_idx] = [[beta1 * mwij + (1 - beta1) * gwij for mwij, gwij in zip(mrow, grow)]
                              for mrow, grow in zip(m_w[layer_idx], grad_w)]
            v_w[layer_idx] = [[beta2 * vwij + (1 - beta2) * (gwij ** 2) for vwij, gwij in zip(vrow, grow)]
                              for vrow, grow in zip(v_w[layer_idx], grad_w)]
            m_b[layer_idx] = [beta1 * mbj + (1 - beta1) * gbj for mbj, gbj in zip(m_b[layer_idx], grad_b)]
            v_b[layer_idx] = [beta2 * vbj + (1 - beta2) * (gbj ** 2) for vbj, gbj in zip(v_b[layer_idx], grad_b)]
            m_w_hat = [[mwij / (1 - beta1 ** t) for mwij in mrow] for mrow in m_w[layer_idx]]
            v_w_hat = [[vwij / (1 - beta2 ** t) for vwij in vrow] for vrow in v_w[layer_idx]]
            m_b_hat = [mbj / (1 - beta1 ** t) for mbj in m_b[layer_idx]]
            v_b_hat = [vbj / (1 - beta2 ** t) for vbj in v_b[layer_idx]]
            t += 1
            state.update({"m_w": m_w, "v_w": v_w, "m_b": m_b, "v_b": v_b, "t": t})
            w_new = [[wij - learning_rate * mwij / (math.sqrt(vwij) + epsilon)
                      for wij, mwij, vwij in zip(wrow, mrow, vrow)]
                     for wrow, mrow, vrow in zip(w, m_w_hat, v_w_hat)]
            b_new = [bj - learning_rate * mbj / (math.sqrt(vbj) + epsilon)
                     for bj, mbj, vbj in zip(b, m_b_hat, v_b_hat)]
        else:
            raise ValueError(f"Optimizer '{method}' tidak dikenali.")

        return data_scaled, (w_new, b_new, state)
    return data_scaled

def evaluate_model(model, data, labels=None, task=None, threshold=0.5, optimizer_args=None):
    # --- Forward pass model ---
    y_pred = model.forward(data)

    # --- Optimizer logic ---
    optimizer_result = None
    if optimizer_args is not None:
        w, b, grad_w, grad_b, layer_idx = optimizer_args[:5]
        method = optimizer_args[5] if len(optimizer_args) > 5 else "sgd"
        learning_rate = optimizer_args[6] if len(optimizer_args) > 6 else 0.01
        beta1 = optimizer_args[7] if len(optimizer_args) > 7 else 0.9
        beta2 = optimizer_args[8] if len(optimizer_args) > 8 else 0.999
        epsilon = optimizer_args[9] if len(optimizer_args) > 9 else 1e-8
        state = optimizer_args[10] if len(optimizer_args) > 10 else defaultdict(dict)
        method = method.lower()

        # pastikan semua berbentuk list
        if not isinstance(grad_w[0], list):
            grad_w = [grad_w]
            w = [w]

        if method == "sgd":
            w_new = [[wij - learning_rate * gwij for wij, gwij in zip(wrow, grow)]
                     for wrow, grow in zip(w, grad_w)]
            b_new = [bj - learning_rate * gbj for bj, gbj in zip(b, grad_b)]
        elif method == "momentum":
            m_w = state.get("m_w", {})
            m_b = state.get("m_b", {})
            if layer_idx not in m_w:
                m_w[layer_idx] = [[0.0 for _ in grow] for grow in grad_w]
                m_b[layer_idx] = [0.0 for _ in grad_b]
            m_w[layer_idx] = [[beta1 * mw + (1 - beta1) * gw for mw, gw in zip(mrow, grow)]
                               for mrow, grow in zip(m_w[layer_idx], grad_w)]
            m_b[layer_idx] = [beta1 * mb + (1 - beta1) * gb for mb, gb in zip(m_b[layer_idx], grad_b)]
            w_new = [[wij - learning_rate * mw for wij, mw in zip(wrow, mrow)]
                     for wrow, mrow in zip(w, m_w[layer_idx])]
            b_new = [bj - learning_rate * mb for bj, mb in zip(b, m_b[layer_idx])]
            state["m_w"], state["m_b"] = m_w, m_b
        elif method == "rmsprop":
            v_w = state.get("v_w", {})
            v_b = state.get("v_b", {})
            if layer_idx not in v_w:
                v_w[layer_idx] = [[0.0 for _ in grow] for grow in grad_w]
                v_b[layer_idx] = [0.0 for _ in grad_b]
            v_w[layer_idx] = [[beta2 * vw + (1 - beta2) * (gw ** 2) for vw, gw in zip(vrow, grow)]
                               for vrow, grow in zip(v_w[layer_idx], grad_w)]
            v_b[layer_idx] = [beta2 * vb + (1 - beta2) * (gb ** 2) for vb, gb in zip(v_b[layer_idx], grad_b)]
            w_new = [[wij - learning_rate * gw / (math.sqrt(vw) + epsilon)
                      for wij, gw, vw in zip(wrow, grow, vrow)]
                     for wrow, grow, vrow in zip(w, grad_w, v_w[layer_idx])]
            b_new = [bj - learning_rate * gb / (math.sqrt(vb) + epsilon)
                     for bj, gb, vb in zip(b, grad_b, v_b[layer_idx])]
            state["v_w"], state["v_b"] = v_w, v_b
        elif method == "adam":
            m_w = state.get("m_w", {})
            v_w = state.get("v_w", {})
            m_b = state.get("m_b", {})
            v_b = state.get("v_b", {})
            t = state.get("t", 1)
            if layer_idx not in m_w:
                m_w[layer_idx] = [[0.0 for _ in grow] for grow in grad_w]
                v_w[layer_idx] = [[0.0 for _ in grow] for grow in grad_w]
                m_b[layer_idx] = [0.0 for _ in grad_b]
                v_b[layer_idx] = [0.0 for _ in grad_b]
            m_w[layer_idx] = [[beta1 * mw + (1 - beta1) * gw for mw, gw in zip(mrow, grow)]
                               for mrow, grow in zip(m_w[layer_idx], grad_w)]
            v_w[layer_idx] = [[beta2 * vw + (1 - beta2) * (gw ** 2) for vw, gw in zip(vrow, grow)]
                               for vrow, grow in zip(v_w[layer_idx], grad_w)]
            m_b[layer_idx] = [beta1 * mb + (1 - beta1) * gb for mb, gb in zip(m_b[layer_idx], grad_b)]
            v_b[layer_idx] = [beta2 * vb + (1 - beta2) * (gb ** 2) for vb, gb in zip(v_b[layer_idx], grad_b)]
            m_w_hat = [[mw / (1 - beta1 ** t) for mw in mrow] for mrow in m_w[layer_idx]]
            v_w_hat = [[vw / (1 - beta2 ** t) for vw in vrow] for vrow in v_w[layer_idx]]
            m_b_hat = [mb / (1 - beta1 ** t) for mb in m_b[layer_idx]]
            v_b_hat = [vb / (1 - beta2 ** t) for vb in v_b[layer_idx]]
            w_new = [[wij - learning_rate * mw / (math.sqrt(vw) + epsilon)
                      for wij, mw, vw in zip(wrow, mrow, vrow)]
                     for wrow, mrow, vrow in zip(w, m_w_hat, v_w_hat)]
            b_new = [bj - learning_rate * mb / (math.sqrt(vb) + epsilon)
                     for bj, mb, vb in zip(b, m_b_hat, v_b_hat)]
            state.update({"m_w": m_w, "v_w": v_w, "m_b": m_b, "v_b": v_b, "t": t + 1})
        else:
            raise ValueError(f"Optimizer '{method}' tidak dikenali.")
        optimizer_result = (w_new, b_new, state)

    # --- Task detection ---
    if labels is not None and task is None:
        unique = set(labels)
        task = "classification" if unique <= {0, 1} else "regression"
        logging.info(f"[Auto Task Detection] Deteksi tugas: {task}")

    # --- Metrics ---
    result = {}
    if labels is None:
        result = {"output_mean": float(sum(y_pred) / len(y_pred))}
    elif task == "regression":
        mse = sum((yp - yt) ** 2 for yp, yt in zip(y_pred, labels)) / len(labels)
        mean_y = sum(labels) / len(labels)
        ss_tot = sum((yt - mean_y) ** 2 for yt in labels)
        ss_res = sum((yp - yt) ** 2 for yp, yt in zip(y_pred, labels))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        mean_err = sum(abs(yp - yt) for yp, yt in zip(y_pred, labels)) / len(labels)
        result.update({"mse": mse, "r2": r2, "mean_error": mean_err})
    elif task == "classification":
        y_class = [1 if yp > threshold else 0 for yp in y_pred]
        tp = sum(1 for yc, yt in zip(y_class, labels) if yc == yt == 1)
        tn = sum(1 for yc, yt in zip(y_class, labels) if yc == yt == 0)
        fp = sum(1 for yc, yt in zip(y_class, labels) if yc == 1 and yt == 0)
        fn = sum(1 for yc, yt in zip(y_class, labels) if yc == 0 and yt == 1)
        accuracy = (tp + tn) / len(labels)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        cm = [[tn, fp], [fn, tp]]
        report = {
            "0": {"precision": tn / (tn + fn) if (tn + fn) else 0.0,
                  "recall": tn / (tn + fp) if (tn + fp) else 0.0},
            "1": {"precision": precision, "recall": recall}
        }
        result.update({"accuracy": accuracy, "precision": precision, "recall": recall,
                       "f1_score": f1, "confusion_matrix": cm, "report": report})
    else:
        raise ValueError("task harus 'regression' atau 'classification'")
    return (result, optimizer_result) if optimizer_result is not None else result

class DOMM:
    def __init__(self, mem_name="MODEL"):
        self.base_name = mem_name
        os.makedirs(self.dir_path, exist_ok=True)

        # Path utama
        self.shelve_file = os.path.join(self.dir_path, self.base_name + ".db")
        self.json_file   = os.path.join(self.dir_path, self.base_name + ".json")
        self.dm_file     = os.path.join(self.dir_path, self.base_name + ".dm")

        # Inisialisasi database
        self.shelf = shelve.open(self.shelve_file)
        deque(maxlen=1000)
        self.experiences = []
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as f:
                try:
                    self.experiences = json.load(f)
                except:
                    self.experiences = []

        # Buat file `.dm` kosong jika belum ada
        if not os.path.exists(self.dm_file):
            with open(self.dm_file, "w") as f:
                f.write(json.dumps({"MODEL": {}, "EXPERIENCE": []}, indent=4))

    # === Cek ukuran file (maks. 20MB)
    def check_size(self):
        total = sum(os.path.getsize(f) for f in 
            chain([self.shelve_file, self.json_file, self.dm_file]) 
            if os.path.exists(f))
        return total <= 20 * 1024 * 1024

    # === Simpan model (ke shelve dan DM)
    def save_model(self, key, model_data):
        """
        Simpan model ke shelve dan DM.
        `model_data` bisa berupa dict / weight / hyperparameter / struktur model.
        """
        if not self.check_size():
            raise Exception("Ukuran file memory melebihi 20MB.")
        self.shelf[key] = model_data
        self.shelf.sync()
        self._update_dm_file()

    # === Load model dari DM atau shelve
    def load_model(self, key):
        self._cache = weakref.WeakValueDictionary()
        return self.shelf.get(key, None)

    # === Hapus model
    def delete_model(self, key):
        if key in self.shelf:
            del self.shelf[key]
        self._update_dm_file()

    # === Hapus semua model
    def clear(self):
        self.shelf.clear()
        gc.collect()
        self._update_dm_file()

    # === Tambah pengalaman (JSON & DM)
    def add_experience(self, state, action, reward):
        if not self.check_size():
            raise Exception("Ukuran file memory melebihi 20MB.")
        exp = {"state": state, "action": action, "reward": reward}
        self.experiences.append(exp)
        with open(self.json_file, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0)
            try:
                data = json.loads(mm.read().decode())
            except:
                data = []
            data.append(exp)
            mm.seek(0)
            mm.write(json.dumps(data).encode())
            mm.flush()
            mm.close()
        self._update_dm_file()

    # === Cari pengalaman
    def search_experience(self, min_reward=0.0):
        return [exp for exp in self.experiences if exp["reward"] >= min_reward]

    # === Hapus semua pengalaman
    def clear_experience(self):
        self.experiences = []
        with open(self.json_file, "w") as f:
            json.dump(self.experiences, f)
        gc.collect()
        self._update_dm_file()

    # === Update file `.dm` utama
    def _update_dm_file(self):
        """
        Gabungkan semua memory (model + experience) ke dalam satu file `.dm`.
        """
        dm_data = {
            "MODEL": dict(self.shelf),
            "EXPERIENCE": self.experiences
        }
        with open(self.dm_file, "w") as f:
            json.dump(dm_data, f, indent=4)

    # === Buat file .dm baru (untuk model lain)
    def create_dm(self, name):
        new_dm = os.path.join(self.dir_path, name + ".dm")
        if os.path.exists(new_dm):
            return "File .dm sudah ada!"
        with open(new_dm, "w") as f:
            json.dump({"MODEL": {}, "EXPERIENCE": []}, f, indent=4)
        return f"File .dm baru berhasil dibuat: {name}.dm"

    # === Tutup database
    def close(self):
        self.shelf.close()

class Adapter:
    # --- Format dasar ---
    @staticmethod
    def json(data):
        if isinstance(data, str):
            return json.loads(data)
        return json.dumps(data)

    @staticmethod
    def csv(data):
        import io, csv
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        if isinstance(data, list):
            for row in data:
                writer.writerow(row)
        return buffer.getvalue()

    # --- Numerical ---
    @staticmethod
    def numpy(data):
        try:
            import numpy as np
            return np.array(data)
        except ImportError:
            return data

    @staticmethod
    def scipyspar(data):
        try:
            from scipy import sparse
            return sparse.csr_matrix(data)
        except ImportError:
            return data

    # --- Data Processing ---
    @staticmethod
    def pandas(data):
        try:
            import pandas as pd
            return pd.DataFrame(data)
        except ImportError:
            return data

    @staticmethod
    def polars(data):
        try:
            import polars as pl
            return pl.DataFrame(data)
        except ImportError:
            return data

    @staticmethod
    def pyarrow(data):
        try:
            import pyarrow as pa
            return pa.array(data)
        except ImportError:
            return data
        
    @staticmethod
    def pygame(data):
        try:
            import pygame
            return pygame(data)
        except ImportError:
            return data

    # --- Audio ---
    @staticmethod
    def librosa(path):
        try:
            import librosa
            return librosa.load(path)
        except ImportError:
            return None

    # --- Vision ---
    @staticmethod
    def pillow(data):
        try:
            from PIL import Image
            return Image.open(data) if isinstance(data, str) else Image.fromarray(data)
        except ImportError:
            return data
        
    class GPU:
        _opencl = None
        _opencl_platforms = None
        _opencl_devices = None
        @staticmethod
        def _load_opencl():
            if Adapter._opencl is not None:
                return Adapter._opencl
            names = []
            system = platform.system().lower()
            if system == "windows":
                names = ["OpenCL.dll"]
            elif system == "darwin":
                # macOS supplies OpenCL.framework
                names = ["/System/Library/Frameworks/OpenCL.framework/OpenCL"]
            else:
                # Linux / others
                names = ["libOpenCL.so", "libOpenCL.so.1", "/usr/lib/x86_64-linux-gnu/libOpenCL.so.1"]
            for nm in names:
                try:
                    lib = ctypes.CDLL(nm)
                    Adapter._opencl = lib
                    return lib
                except Exception:
                    continue
            Adapter._opencl = None
            return None

        @staticmethod
        def gpu_available():
            """
            Return True if a GPU runtime (OpenCL or CUDA driver) is available on the system.
            This is a lightweight check: first attempt OpenCL; if not present, attempt CUDA driver lib.
            """
            if Adapter._load_opencl():
                return True
            # try detecting CUDA driver
            try:
                system = platform.system().lower()
                if system == "windows":
                    ctypes.CDLL("nvcuda.dll")
                else:
                    ctypes.CDLL("libcuda.so")
                return True
            except Exception:
                return False

        @staticmethod
        def gpu_info():
            """
            Return structured info about available GPU platforms/devices.
            Uses OpenCL when available; otherwise returns CUDA driver presence info.
            """
            info = {"opencl": False, "platforms": [], "cuda": False}
            lib = Adapter._load_opencl()
            if lib is not None:
                info["opencl"] = True
                try:
                    # Minimal OpenCL wrappers (we only use clGetPlatformIDs, clGetPlatformInfo, clGetDeviceIDs, clGetDeviceInfo)
                    # Types
                    cl_uint = ctypes.c_uint
                    cl_int = ctypes.c_int
                    cl_platform_id = ctypes.c_void_p
                    cl_device_id = ctypes.c_void_p
                    size_t = ctypes.c_size_t

                    # Functions
                    clGetPlatformIDs = lib.clGetPlatformIDs
                    clGetPlatformIDs.argtypes = [cl_uint, ctypes.POINTER(cl_platform_id), ctypes.POINTER(cl_uint)]
                    clGetPlatformIDs.restype = cl_int

                    # First get platform count
                    num_platforms = cl_uint(0)
                    ret = clGetPlatformIDs(0, None, ctypes.byref(num_platforms))
                    if ret != 0:
                        # Could not query platforms
                        return info
                    nplat = num_platforms.value
                    if nplat == 0:
                        return info
                    platforms = (cl_platform_id * nplat)()
                    ret = clGetPlatformIDs(nplat, platforms, None)
                    if ret != 0:
                        return info

                    # Prepare clGetPlatformInfo
                    clGetPlatformInfo = lib.clGetPlatformInfo
                    clGetPlatformInfo.argtypes = [cl_platform_id, ctypes.c_uint, size_t, ctypes.c_void_p, ctypes.POINTER(size_t)]
                    clGetPlatformInfo.restype = cl_int

                    # constants
                    CL_PLATFORM_NAME = 0x0902
                    CL_PLATFORM_VERSION = 0x0903
                    CL_PLATFORM_VENDOR = 0x0901

                    # Device query
                    clGetDeviceIDs = lib.clGetDeviceIDs
                    clGetDeviceIDs.argtypes = [cl_platform_id, ctypes.c_ulong, cl_uint, ctypes.POINTER(cl_device_id), ctypes.POINTER(cl_uint)]
                    clGetDeviceIDs.restype = cl_int
                    CL_DEVICE_NAME = 0x102B
                    CL_DEVICE_VENDOR = 0x102C
                    CL_DEVICE_TYPE = 0x1000
                    CL_DEVICE_MAX_COMPUTE_UNITS = 0x1002
                    CL_DEVICE_GLOBAL_MEM_SIZE = 0x101F
                    clGetDeviceInfo = lib.clGetDeviceInfo
                    clGetDeviceInfo.argtypes = [cl_device_id, ctypes.c_uint, size_t, ctypes.c_void_p, ctypes.POINTER(size_t)]
                    clGetDeviceInfo.restype = cl_int
                    for p in platforms:
                        # platform name
                        # first query size
                        sz = size_t()
                        clGetPlatformInfo(p, CL_PLATFORM_NAME, 0, None, ctypes.byref(sz))
                        buf = ctypes.create_string_buffer(sz.value)
                        clGetPlatformInfo(p, CL_PLATFORM_NAME, sz, buf, None)
                        pname = buf.value.decode(errors="ignore")
                        clGetPlatformInfo(p, CL_PLATFORM_VERSION, 0, None, ctypes.byref(sz))
                        buf = ctypes.create_string_buffer(sz.value)
                        clGetPlatformInfo(p, CL_PLATFORM_VERSION, sz, buf, None)
                        pver = buf.value.decode(errors="ignore")

                        platform_entry = {"name": pname, "version": pver, "devices": []}

                        # get devices for this platform (ALL types)
                        num_devices = cl_uint(0)
                        ret = clGetDeviceIDs(p, 0xFFFFFFFF, 0, None, ctypes.byref(num_devices))
                        if ret == 0 and num_devices.value > 0:
                            ndev = num_devices.value
                            devs = (cl_device_id * ndev)()
                            ret = clGetDeviceIDs(p, 0xFFFFFFFF, ndev, devs, None)
                            if ret == 0:
                                for d in devs:
                                    # name
                                    clGetDeviceInfo(d, CL_DEVICE_NAME, 0, None, ctypes.byref(sz))
                                    buf = ctypes.create_string_buffer(sz.value)
                                    clGetDeviceInfo(d, CL_DEVICE_NAME, sz, buf, None)
                                    dname = buf.value.decode(errors="ignore")

                                    # vendor
                                    clGetDeviceInfo(d, CL_DEVICE_VENDOR, 0, None, ctypes.byref(sz))
                                    buf = ctypes.create_string_buffer(sz.value)
                                    clGetDeviceInfo(d, CL_DEVICE_VENDOR, sz, buf, None)
                                    dvendor = buf.value.decode(errors="ignore")

                                    # compute units
                                    cu = ctypes.c_uint()
                                    clGetDeviceInfo(d, CL_DEVICE_MAX_COMPUTE_UNITS, ctypes.sizeof(cu), ctypes.byref(cu), None)
                                    # mem size
                                    mem = ctypes.c_ulonglong()
                                    clGetDeviceInfo(d, CL_DEVICE_GLOBAL_MEM_SIZE, ctypes.sizeof(mem), ctypes.byref(mem), None)

                                    device_entry = {
                                        "name": dname,
                                        "vendor": dvendor,
                                        "compute_units": cu.value,
                                        "global_mem_bytes": mem.value
                                    }
                                    platform_entry["devices"].append(device_entry)
                        info["platforms"].append(platform_entry)
                    return info
                except Exception:
                    return info
            # if opencl not available, try to detect CUDA driver presence
            try:
                system = platform.system().lower()
                if system == "windows":
                    ctypes.CDLL("nvcuda.dll")
                else:
                    ctypes.CDLL("libcuda.so")
                info["cuda"] = True
            except Exception:
                info["cuda"] = False
            return info

        @staticmethod
        def opencl_simple_vector_add(a_bytes, b_bytes, dtype="float32"):
            """
            Placeholder: APP-level helper that indicates we *could* run a vector add on GPU.
            Real kernel execution via ctypes is long; here we return a plan/detection object.
            For actual GPU math, prefer `pyopencl` or `numba` if available.
            """
            if not Adapter.gpu_available():
                raise RuntimeError("No GPU runtime available")
            info = Adapter.gpu_info()
            # For now we only return meta and a suggestion; actual execution not implemented
            return {
                "plan": "opencl_vector_add",
                "dtype": dtype,
                "size_bytes": len(a_bytes),
                "platforms": info.get("platforms", []),
                "note": "This helper detects GPU and prepares a plan. For execution use pyopencl or implement specialized ctypes kernels."
            }
