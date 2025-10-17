from .model import CustomAIModel
from .utils import preprocess_data, evaluate_model, cached
from .Quantum import Quantum, linear_universe
import threading, time, logging, math, random, statistics, pathlib

def test_model(model, X, y, formula=None, verbose=True):
    """
    Fungsi testing model AI dengan Alogekstest-Phymetrix (pure Python).
    """
    # --- Forward pass model ---
    preds = model.forward(X)  # list of float atau list of list
    # --- Transformasi log & eksponensial ---
    transformed = []
    for row in preds:
        if isinstance(row, (int, float)):  # kasus 1D
            val = math.log(row + 1) if row > 0 else row
            transformed.append([math.exp(val)])
        else:  # kasus 2D
            new_row = []
            for v in row:
                val = math.log(v + 1) if v > 0 else v
                new_row.append(math.exp(val))
            transformed.append(new_row)

    # --- Multi-dimensional Pythagoras ---
    py_values = [math.sqrt(sum(v*v for v in row)) for row in transformed]

    # --- Normalisasi ke 0–1 ---
    max_val = max(py_values) if py_values else 1.0
    final_preds = [pv / (max_val + 1e-8) for pv in py_values]

    # --- Evaluasi model ---
    result = evaluate_model(model, X, y, task="classification")

    # --- Insight tambahan ---
    insight = {
        "mean_prediction": float(statistics.mean(final_preds)) if final_preds else 0.0,
        "max_prediction": float(max(final_preds)) if final_preds else 0.0,
        "min_prediction": float(min(final_preds)) if final_preds else 0.0,
    }
    result.update({
        "formula_used": formula or "aljabar+logaritma+eksponensial+phytagoras+geometri+matrix",
        "final_preds": final_preds,
        "insight": insight
    })

    if verbose:
        print("📊 Alogekstest-Phymetrix Evaluation:")
        print(f"Accuracy: {result.get('accuracy', 'N/A')}")
        print(f"Loss: {result.get('loss', 'N/A')}")
        print(f"Mean Prediction: {insight['mean_prediction']:.4f}")
    return result

# === LOGEKSTRAINNIX ===
class transform:
    """
    Transformasi input menggunakan:
    - eksponensial, logaritma, matrix, linear universe
    """
    def __init__(self, use_quantum=True, qubit_size=4):
        self.use_quantum = use_quantum
        self.qubit_size = qubit_size
        if self.use_quantum:
            try:
                self.quantum = Quantum(qubit_size=self.qubit_size)
            except Exception:
                self.quantum = None
                self.use_quantum = False

    @cached
    def Qtransform(self, X):
        """
        Quantum transform dengan Hadamard + measurement
        """
        X_transformed = [row[:] for row in X]
        if not self.quantum:
            return X_transformed
        for i in range(min(self.qubit_size, len(X[0]))):
            self.quantum.state[i] = complex(X[0][i], 0.0)
            self.quantum.hadamard_gate(i)
        q_meas = self.quantum.measure()
        q_bits = [float(b) for b in q_meas["result"]]
        for row in X_transformed:
            for i in range(min(self.qubit_size, len(row))):
                row[i] = q_bits[i]
        return X_transformed

    def transform(self, X):
        """
        Transformasi log + exp + matrix + linear universe + quantum
        X: list of list (2D)
        """
        # log + exp
        X_log = [[math.log(max(x, 1e-8)) for x in row] for row in X]
        X_exp = [[math.exp(x) for x in row] for row in X]

        # Matrix mix: X * (X^T X / max)
        n_samples = len(X)
        n_features = len(X[0]) if n_samples > 0 else 0
        # Compute X^T X
        mat = [[0.0]*n_features for _ in range(n_features)]
        for i in range(n_features):
            for j in range(n_features):
                mat[i][j] = sum(row[i]*row[j] for row in X)
        max_val = max(abs(v) for row in mat for v in row) or 1.0
        mat_avg = [[v/max_val for v in row] for row in mat]

        # X_matrixed = X * mat_avg
        X_matrixed = []
        for row in X:
            new_row = []
            for j in range(n_features):
                val = sum(x*y for x,y in zip(row, (mat_avg[k][j] for k in range(n_features))))
                new_row.append(val)
            X_matrixed.append(new_row)

        # Linear universe
        X_linear = self.linear_universe(X_matrixed)

        # Gabungkan semua
        X_final = []
        for r_log, r_exp, r_lin in zip(X_log, X_exp, X_linear):
            row = [(a+b+c)/3.0 for a, b, c in zip(r_log, r_exp, r_lin)]
            X_final.append(row)

        # Quantum
        if self.use_quantum:
            try:
                X_final = self.Qtransform(X_final)
            except Exception:
                pass
        return X_final

# === Data load ===
@cached
def load_dataset(task="classification", n_samples=500, n_features=4):
    X, y = [], []
    if task == "classification":
        for _ in range(n_samples):
            row = [random.gauss(0, 1) for _ in range(n_features)]  # distribusi normal
            # label = 1 kalau jumlah fitur positif lebih banyak
            label = 1 if sum(1 for v in row if v > 0) > (n_features // 2) else 0
            X.append(row)
            y.append([label])
    elif task == "regression":
        for _ in range(n_samples):
            row = [random.gauss(0, 2) for _ in range(n_features)]
            target = sum(row) + random.gauss(0, 0.5)  # linear + noise
            X.append(row)
            y.append([target])
    else:
        raise ValueError("Task harus 'classification' atau 'regression'")

    # --- Normalisasi setiap fitur biar lebih stabil ---
    X_t = list(zip(*X))  # transpose (fitur jadi kolom)
    X_scaled = []
    for row in X:
        scaled_row = []
        for i, val in enumerate(row):
            col = X_t[i]
            mean = statistics.mean(col)
            stdev = statistics.pstdev(col) or 1.0
            scaled_row.append((val - mean) / stdev)
        X_scaled.append(scaled_row)
    return X_scaled, y

def data_loader(X, y, batch_size=32, shuffle=True):
    """
    mini-batch loader.
    X, y: list of list
    """
    n = len(X)
    indices = list(range(n))
    if shuffle:
        random.shuffle(indices)
    for start in range(0, n, batch_size):
        end = start + batch_size
        idx = indices[start:end]
        X_batch = [X[i] for i in idx]
        y_batch = [y[i] for i in idx]
        yield X_batch, y_batch

def load_image_dataset(folder_path, size=(64, 64), label_type="folder"):
    """
    Loader dataset gambar pure python (format PPM/P6).
    """
    X, y = [], []
    class_map, class_idx = {}, 0
    folder_path = pathlib.Path(folder_path)
    for path in folder_path.rglob("*.ppm"):
        with open(path, "rb") as f:
            # --- Baca header PPM ---
            if f.readline().decode().strip() != "P6":
                continue
            dims = f.readline().decode().strip()
            while dims.startswith("#"):
                dims = f.readline().decode().strip()
            w, h = map(int, dims.split())
            maxval = int(f.readline().decode().strip())
            raw = f.read(w * h * 3)
            pixels = [raw[i:i+3] for i in range(0, len(raw), 3)]
            img = [[tuple(p) for p in pixels[i*w:(i+1)*w]] for i in range(h)]

        # --- Resize nearest neighbor ---
        new_w, new_h = size
        resized = []
        for j in range(new_h):
            row = []
            for i in range(new_w):
                src_x = int(i * w / new_w)
                src_y = int(j * h / new_h)
                row.append(img[src_y][src_x])
            resized.append(row)

        # --- Normalisasi ---
        flat = [c for row in resized for (r,g,b) in row for c in (r,g,b)]
        maxv, minv = max(flat), min(flat)
        norm = []
        for row in resized:
            nrow = []
            for (r,g,b) in row:
                if maxv == minv:
                    nrow.append((0,0,0))
                else:
                    nrow.append(((r-minv)/(maxv-minv),
                                 (g-minv)/(maxv-minv),
                                 (b-minv)/(maxv-minv)))
            norm.append(nrow)
        X.append(norm)

        # --- Label ---
        if label_type == "folder":
            label_name = path.parent.name
            if label_name not in class_map:
                class_map[label_name] = class_idx
                class_idx += 1
            y.append(class_map[label_name])
    print(f"📸 Loaded {len(X)} images from {folder_path}")
    return X, [[lbl] for lbl in y]

# === Logging ===
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# === Evaluasi Komprehensif ===
@cached
def fullevaluation(model, X, y, task):
    result = evaluate_model(model, X, y, task)
    logging.info(f"📊 Evaluasi Model: {result}")
    return result

# === Training Utama ===
def train(model, task="classification", visualize=True, epochs=100, 
          learning_rate=0.05, batch_size=32, use_logekstrainnix=False):
    n_features = model.layer_sizes[0]
    X, y = load_dataset(task=task, n_samples=500, n_features=n_features)
    X = preprocess_data(X)
    if use_logekstrainnix:
        logex = transform()
        X = logex.transform(X)  # Transformasi khusus sebelum training
    def trainingthread():
        logging.info("🔧 Training dimulai...")
        model.train(X, y, epochs=epochs, learning_rate=learning_rate, batch_size=batch_size)
        logging.info("✅ Training selesai.")
    start = time.time()
    thread = threading.Thread(target=trainingthread)
    thread.start()
    thread.join()
    end = time.time()
    eval_result = fullevaluation(model, X, y, task)
    print("📌 Waktu training: {:.3f} detik".format(end - start))
    print("🎯 Hasil evaluasi:", eval_result)
    return model, eval_result

# === Multi Model Training (opsional) ===
def trainmultiple(n=3, input_size=4, output_size=1, task="classification",
                  use_autograd=False, use_logekstrainnix=False):
    """
    Training beberapa model sekaligus dengan dukungan logekstrainnix dan linear universe.
    """
    models = []
    for i in range(n):
        print(f"🚀 Training model-{i+1}/{n}")
        model = CustomAIModel(
            layer_sizes=[input_size, 16, 8, output_size],
            activations=["memory", "attention", "spiking"],  # contoh kombinasi yang ada
            loss="mse" if task == "regression" else "cross_entropy"
        )

        # Jalankan training per model
        train(model, task=task, use_autograd=use_autograd, use_logekstrainnix=use_logekstrainnix)
        models.append(model)
    return models


# === Eksekusi Utama ===
if __name__ == "__main__":
    model = CustomAIModel(
        layer_sizes=[4, 16, 8, 1],
        activations=["memory", "attention", "spiking"],  # pakai yang ada
        loss="cross_entropy"
    )
    train(model, task="classification", use_autograd=False)