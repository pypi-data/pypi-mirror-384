import math, statistics, itertools, random, json
from dataclasses import dataclass, field
from .utils import cached
from collections import defaultdict
from typing import Callable

@dataclass
class DOtensor:
    data: list  # langsung pakai list of float
    requires_grad: bool = False
    grad: itertools.starmap = None
    _backward: Callable = field(default=lambda: None, repr=False)
    _prev: tuple = field(default_factory=tuple, repr=False)

    # global trace
    _global_trace_enabled: bool = False
    _global_trace_log: list = field(default_factory=list, repr=False)

    def __post_init__(self):
        # pastikan data berupa list of float
        if not isinstance(self.data, list):
            self.data = list(self.data) if hasattr(self.data, "__iter__") else [float(self.data)]
        else:
            self.data = [float(x) for x in self.data]
        # inisialisasi grad kalau perlu
        if self.requires_grad:
            self.grad = list(itertools.repeat(0.0, len(self.data)))
        else:
            self.grad = None

    def __add__(self, other):
        other = other if isinstance(other, DOtensor) else DOtensor(other)
        out = DOtensor(self.data + other.data, requires_grad=(self.requires_grad or other.requires_grad))
        if out.requires_grad:
            def _backward():
                if self.requires_grad:
                    self.grad += out.grad
                if other.requires_grad:
                    other.grad += out.grad
            out._backward = _backward
            out._prev = (self, other)
        if DOtensor._global_trace_enabled:
            DOtensor._global_trace_log.append(("add", self.data, other.data))
        return out

    def __mul__(self, other):
        other = other if isinstance(other, DOtensor) else DOtensor(other)
        out = DOtensor([a * b for a, b in zip(self.data, other.data)], requires_grad=(self.requires_grad or other.requires_grad))
        if out.requires_grad:
            def _backward():
                if self.requires_grad:
                    self.grad = [g + od * og for g, od, og in zip(self.grad, other.data, out.grad)]
                if other.requires_grad:
                    other.grad = [g + sd * og for g, sd, og in zip(other.grad, self.data, out.grad)]
            out._backward = _backward
            out._prev = (self, other)
        if DOtensor._global_trace_enabled:
            DOtensor._global_trace_log.append(("mul", self.data, other.data))
        return out

    def backward(self):
        if not self.requires_grad:
           raise RuntimeError("backward() called on tensor without requires_grad")
        self.grad = [1.0 for _ in self.data]
        stack = [self]
        visited = set()
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                # jalankan fungsi backward dari node ini
                if callable(node._backward):
                    node._backward()
                # tambahkan dependency (node sebelumnya)
                stack.extend(node._prev)

    # tambahan di class DOtensor:
    def __hash__(self):
        return id(self) # supaya bisa masuk ke set / dict
        
    def __repr__(self):
        return f"DOtensor(data={self.data}, grad={self.grad})"

    @staticmethod
    def enable_trace():
        DOtensor._global_trace_enabled = True
        DOtensor._global_trace_log = []

    @staticmethod
    def disable_trace():
        DOtensor._global_trace_enabled = False

    @classmethod
    def get_trace_log(cls):
        return list(cls._global_trace_log)  # copy ringan

# === Modular Layer Base ===
class Layer:
    def forward(self, x): raise NotImplementedError
    def backward(self, grad): raise NotImplementedError
    def update(self, lr): pass

# === Dense Layer ===
class Dense:
    def __init__(self, input_dim, output_dim):
        # bobot dan bias
        self.weights = [[random.gauss(0, 1) * math.sqrt(2.0 / input_dim)
                         for _ in range(output_dim)] for _ in range(input_dim)]
        self.bias = [0.0] * output_dim

    def forward(self, X):
        self.input = X
        def cell(x, j):
            return sum(x[i] * self.weights[i][j] for i in range(len(x))) + self.bias[j]
        return [[*itertools.starmap(cell, [(x, j) for j in range(len(self.bias))])] for x in X]


    def backward(self, grad_output):
        batch = len(grad_output)
        input_dim, output_dim = len(self.weights), len(self.weights[0])
        # grad_w (mean pakai statistics)
        self.grad_w = [
            [statistics.mean(self.input[k][i] * grad_output[k][j] for k in range(batch))
             for j in range(output_dim)]
            for i in range(input_dim)
        ]
        # grad_b
        self.grad_b = [statistics.mean(grad_output[k][j] for k in range(batch)) for j in range(output_dim)]
        # grad_input
        grad_input = [
            [sum(grad_output[k][j] * self.weights[i][j] for j in range(output_dim))
             for i in range(input_dim)]
            for k in range(batch)
        ]
        return grad_input

    def update(self, lr):
        for i in range(len(self.weights)):
            for j in range(len(self.weights[0])):
                self.weights[i][j] -= lr * self.grad_w[i][j]
        for j in range(len(self.bias)):
            self.bias[j] -= lr * self.grad_b[j]

# === Activation Layer ===
class Activation:
    def __init__(self, kind="relu"):
        self.kind = kind
        self.input = None
    @cached
    def forward(self, x):
        self.input = x
        if self.kind == "relu":
            return [[max(0.0, val) for val in row] for row in x]
        elif self.kind == "sigmoid":
            return [[1 / (1 + math.exp(-val)).real for val in row] for row in x]
        elif self.kind == "tanh":
            return [[math.tanh(val).real for val in row] for row in x]
        return x
    @cached
    def backward(self, grad_output):
        if self.kind == "relu":
            return [[g if val > 0 else 0.0 for g, val in zip(g_row, x_row)]
                    for g_row, x_row in zip(grad_output, self.input)]
        elif self.kind == "sigmoid":
            s = [[1 / (1 + math.exp(-val)).real for val in row] for row in self.input]
            return [[g * si * (1 - si) for g, si in zip(g_row, s_row)]
                    for g_row, s_row in zip(grad_output, s)]
        elif self.kind == "tanh":
            t = [[math.tanh(val).real for val in row] for row in self.input]
            return [[g * (1 - ti**2) for g, ti in zip(g_row, t_row)]
                    for g_row, t_row in zip(grad_output, t)]
        return grad_output

# === Dropout (Opsional) ===
class Dropout:
    def __init__(self, rate=0.5):
        self.rate = rate
        self.mask = None

    def forward(self, x):
        # x = list of list (matrix)
        self.mask = [[1.0 if random.getrandbits(1) > self.rate else 0.0 for _ in row] for row in x]
        return [[val * m for val, m in zip(row, mrow)] for row, mrow in zip(x, self.mask)]

    def backward(self, grad_output):
        return [[g * m for g, m in zip(row, mrow)] for row, mrow in zip(grad_output, self.mask)]

# === Custom Model ===
class CustomAIModel:
    def __init__(self, loss="mse"):
        self.layers = []
        self.loss = loss
        self.losses = []
        self.memory_neuron = None
        self.expert_neurons = []

    def add(self, layer):
        self.layers.append(layer)

    def forward(self, x):
        for layer in self.layers:
            x = layer.forward(x)
        return x
    
    def addneuron(self, kind="memory", **kwargs):
        """
        Menambahkan neuron khusus ke model (versi pure python).
        """
        if kind == "memory":
            size = kwargs.get("size", 128)
            self.memory_neuron = [0.0] * size  
            print(f"🧠 Neuron Memory ditambahkan (size={size})")

        elif kind == "attention":
            @cached
            def attention(query, keys, values):
                # dot product manual
                scores = [[sum(qi * kj for qi, kj in zip(q, k)) for k in keys] for q in query]
                # softmax (exp normalize)
                weights = []
                for row in scores:
                    exp_row = [math.exp(s) for s in row]
                    total = sum(exp_row) + 1e-8
                    weights.append([val / total for val in exp_row])
                # weighted sum
                result = []
                for w in weights:
                    result.append([
                        sum(wij * vij for wij, vij in zip(w, col))
                        for col in zip(*values)
                    ])
                return result
            self.attention = attention
            print("🎯 Neuron Attention ditambahkan")

        elif kind == "ntc":  
            @cached          
            def ntc(x, kernel):
                k = len(kernel)
                pad = k // 2
                out = []
                for i in range(len(x)):
                    acc = 0
                    for j in range(k):
                        idx = i + j - pad
                        if 0 <= idx < len(x):
                            acc += x[idx] * kernel[j]
                    out.append(acc)
                return out
            self.ntc = lambda x: ntc(x, kwargs.get("kernel", [1, -1, 1]))
            print("🕒 Neuron Temporal Convolution ditambahkan")

        elif kind == "graph":            
            self.graph = defaultdict(list)
            nodes = kwargs.get("nodes", [0, 1])
            edges = kwargs.get("edges", [(0, 1)])
            for n in nodes:
                self.graph[n]  # init
            for u, v in edges:
                self.graph[u].append(v)
                self.graph[v].append(u)
            print("🔗 Neuron Graph ditambahkan")

        elif kind == "nalu":
            @cached
            def nalu(x):
                eps = 1e-7
                result = []
                for row in x:
                    g = [math.tanh(val) for val in row]
                    Wa = kwargs.get("W_a", [[1.0] for _ in row])
                    Wm = kwargs.get("W_m", [[1.0] for _ in row])
                    # linear part
                    a = [sum(val * w for val, w in zip(row, col)) for col in zip(*Wa)]
                    # multiplicative part
                    m = [math.exp(sum(math.log(abs(val) + eps) * w for val, w in zip(row, col))) for col in zip(*Wm)]
                    # combine
                    out = [gi * ai + (1 - gi) * mi for gi, ai, mi in zip(g, a, m)]
                    result.append(out)
                return result
            self.nalu = nalu
            print("🧮 Neuron NALU (Arithmetic Logic) ditambahkan")

        elif kind == "moe":
            experts = kwargs.get("experts", [lambda x: x])
            gate = kwargs.get("gate", lambda x: [1/len(experts)]*len(experts))
            def moe(x):
                weights = gate(x)
                return sum(w * e(x) for w, e in zip(weights, experts))
            if not hasattr(self, "expert_neurons"):
                self.expert_neurons = []
            self.expert_neurons.append(moe)
            print("👥 Neuron Mixture of Experts ditambahkan")

        elif kind == "spiking":
            def spiking(x, threshold=0.5):
                return [1.0 if val > threshold else 0.0 for val in x]
            self.spiking = spiking
            print("⚡ Neuron Spiking ditambahkan (threshold=0.5)")
        else:
            print(f"❌ Neuron {kind} tidak dikenal.")
    @cached
    def _loss(self, y_pred, y_true):
        if self.loss == "mse":
            return statistics.mean((yp - yt) ** 2 for yp, yt in zip(y_pred, y_true))
        elif self.loss == "cross_entropy":
            epsilon = 1e-8
            vals = []
            for yp, yt in zip(y_pred, y_true):
                vals.append(-(yt * math.log(yp + epsilon) + (1 - yt) * math.log(1 - yp + epsilon)))
            return statistics.mean(vals)
        return 0.0
    @cached
    def _loss_grad(self, y_pred, y_true):
        n = len(y_true)
        if self.loss == "mse":
            return [[2 * (yp - yt) / n for yp, yt in zip(yp_row, yt_row)]
                    for yp_row, yt_row in zip(y_pred, y_true)]
        elif self.loss == "cross_entropy":
            return [[(yp - yt) / n for yp, yt in zip(yp_row, yt_row)]
                    for yp_row, yt_row in zip(y_pred, y_true)]
        return 0.0

    def train(self, X, y, epochs=100, learning_rate=0.01, batch_size=None, verbose=True):
        n = len(X)
        if batch_size is None:
            batch_size = n
        for epoch in range(epochs):
            indices = list(range(n))
            random.shuffle(indices)
            X = [X[i] for i in indices]
            y = [y[i] for i in indices]
            losses = []
            for start in range(0, n, batch_size):
                end = start + batch_size
                x_batch = X[start:end]
                y_batch = y[start:end]
                y_pred = self.forward(x_batch)
                loss = self._loss(y_pred, y_batch)
                losses.append(loss)
                grad = self._loss_grad(y_pred, y_batch)
                for layer in reversed(self.layers):
                    grad = layer.backward(grad)
                for layer in self.layers:
                    if hasattr(layer, "update"):
                        layer.update(learning_rate)
            mean_loss = statistics.mean(losses)
            self.losses.append(mean_loss)
            if verbose:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {mean_loss:.4f}")

    def save_model(self, path):
        config = {
            "loss": self.loss,
            "layers": [
                {
                    "type": type(layer).__name__,
                    "params": {
                        "input_dim": len(layer.weights) if hasattr(layer, "weights") else None,
                        "output_dim": len(layer.weights[0]) if hasattr(layer, "weights") else None,
                        "activation": getattr(layer, "kind", None),
                        "rate": getattr(layer, "rate", None)
                    }
                } for layer in self.layers
           ]
        }
        with open(path + "_config.json", "w") as f:
            json.dump(config, f)
        weights = []
        for layer in self.layers:
            if hasattr(layer, "weights"):
                weights.append({"weights": layer.weights, "bias": layer.bias})
        with open(path + "_weights.json", "w") as f:
            json.dump(weights, f)

    @classmethod
    def load_model(cls, path):
        with open(path + "_config.json", "r") as f:
            config = json.load(f)
        model = cls(loss=config["loss"])
        for layer_cfg in config["layers"]:
            if layer_cfg["type"] == "Dense":
                model.add(Dense(layer_cfg["params"]["input_dim"], layer_cfg["params"]["output_dim"]))
            elif layer_cfg["type"] == "Activation":
                model.add(Activation(layer_cfg["params"]["activation"]))
            elif layer_cfg["type"] == "Dropout":
                model.add(Dropout(layer_cfg["params"]["rate"]))
        with open(path + "_weights.json", "r") as f:
            data = json.load(f)
        idx = 0
        for layer in model.layers:
            if hasattr(layer, "weights"):
                layer.weights = data[idx]["weights"]
                layer.bias = data[idx]["bias"]
                idx += 1
        return model