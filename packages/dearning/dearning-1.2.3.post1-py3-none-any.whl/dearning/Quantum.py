import math, cmath, random, itertools, statistics, logging, time
import os, atexit, gc, weakref, tracemalloc, heapq
from .utils import cached
from itertools import cycle, islice, product, starmap
from decimal import Decimal, getcontext
from fractions import Fraction
from multiprocessing import Pool, cpu_count
from array import array


@cached
def linear_universe(self, X):
    n_samples = len(X)
    n_features = len(X[0]) if n_samples > 0 else 0
    result = []
    for row in X:
        # 1. Linear + kuadrat + 0.5x
        base_row = [(x + x**2 + 0.5 * x) for x in row]

        # 2. Cross terms
        cross_terms = [
            sum(starmap(lambda j, k: row[j] * row[k], [(i, j) for j in range(i + 1, n_features)]))
            for i in range(n_features)
        ]

        # 3. Regresi linear sederhana
        mean_feature = sum(row) / n_features if n_features > 0 else 0
        reg_linear_simple = [mean_feature] * n_features

        # 4. Regresi linear ganda
        reg_linear_multi = []
        for i in range(n_features):
            dot_val = sum(row[j] * (j + 1) for j in range(n_features))
            reg_linear_multi.append(dot_val / (n_features or 1))

        # 5. Polynomial (nonlinear)
        reg_poly = [x**2 + 0.1 * x**3 for x in row]

        # 6. Linearization
        min_val, max_val = min(row), max(row)
        if max_val - min_val != 0:
            linearized = [(x - min_val) / (max_val - min_val) for x in row]
        else:
            linearized = [0.0 for _ in row]

        # 7. Interpolation
        interpolated = []
        for i in range(n_features - 1):
            interpolated.append((row[i] + row[i + 1]) / 2)
        if n_features > 0:
            interpolated.append(row[-1])

        # 8. Math-based ops
        math_ops = []
        for x in row:
            try:
                val = (
                    math.sin(x) +
                    math.cos(x) +
                    (math.log(abs(x) + 1)) +  # log stabil
                    math.exp(min(x, 10)) +    # cegah overflow exp
                    math.sqrt(abs(x)) +
                    math.pow(x, 2/3)          # pangkat pecahan
                )
                if not math.isfinite(val):
                    val = 0.0
            except Exception:
                val = 0.0
            math_ops.append(val)

        # 9. Gabungkan semua
        row_out = []
        for i in range(n_features):
            val = (
                base_row[i]
                + 0.1 * cross_terms[i]
                + 0.2 * reg_linear_simple[i]
                + 0.3 * reg_linear_multi[i]
                + 0.5 * reg_poly[i]
                + 0.2 * linearized[i]
                + 0.1 * interpolated[i]
                + 0.4 * math_ops[i]
            )
            row_out.append(val)
        result.append(row_out)
    return result

class Quan:
    @staticmethod
    @cached
    def tambah(a, b): return a + b
    @staticmethod
    @cached
    def kurang(a, b): return a - b
    @staticmethod
    @cached
    def kali(a, b): return a * b
    @staticmethod
    @cached
    def bagi(a, b): return a / b if b != 0 else None
    @staticmethod
    @cached
    def kuadrat(x): return x**2
    @staticmethod
    @cached
    def akar(x): return math.sqrt(x)

    @staticmethod
    @cached
    def trigono(x):
        return {
            "sin": math.sin(x),
            "cos": math.cos(x),
            "tan": math.tan(x),
            "asin": math.asin(x),
            "acos": math.acos(x),
            "atan": math.atan(x)
        }

    @staticmethod
    @cached
    def logeks(x, base=math.e):
        return {"log": math.log(x, base), "exp": math.exp(x)}

    @staticmethod
    @cached
    def Tphytagoras(a, b, c=0):
        return math.sqrt(a**2 + b**2 + c**2)

    @staticmethod
    @cached
    def matrix_mul(A, B):
        n, m, p = len(A), len(A[0]), len(B[0])
        if m != len(B):
            raise ValueError("Ukuran matriks tidak sesuai untuk dikalikan")
        def cell(i, j):
            return sum(A[i][k] * B[k][j] for k in range(m))
        # hasilkan generator baris, tiap baris juga generator
        return (
            starmap(cell, ((i, j) for j in range(p)))
            for i in range(n)
        )

    getcontext().prec = 50 
    @staticmethod
    @cached
    def matrix_inv(A):
        n = len(A)
        mat = [[Decimal(x) for x in row] for row in A]
        identity = [[Decimal(int(i == j)) for i in range(n)] for j in range(n)]
        for i in range(n):
            # cari pivot (full pivoting)
            max_row = max(range(i, n), key=lambda r: abs(mat[r][i]))
            if mat[max_row][i] == 0:
                raise ValueError("Matriks singular, tidak bisa dibalik")
            if max_row != i:
                mat[i], mat[max_row] = mat[max_row], mat[i]
                identity[i], identity[max_row] = identity[max_row], identity[i]
            # normalkan baris pivot
            pivot = mat[i][i]
            mat[i] = [mij / pivot for mij in mat[i]]
            identity[i] = [idj / pivot for idj in identity[i]]
            # eliminasi baris lain
            for k in range(n):
                if k != i:
                    factor = mat[k][i]
                    mat[k] = [m - factor * p for m, p in zip(mat[k], mat[i])]
                    identity[k] = [idk - factor * idi for idk, idi in zip(identity[k], identity[i])]
        # convert balik ke float stabil
        return [[float(x) for x in row] for row in identity]

    @staticmethod
    @cached
    def luas_lingkaran(r):
        return math.pi * r**2
    @staticmethod
    @cached
    def volume_bola(r):
        return (4/3) * math.pi * (r**3)

    @staticmethod
    @cached
    def statistik(data):
        data = list(data)
        return {
            "mean": statistics.mean(data) if data else 0.0,
            "median": statistics.median(data) if data else 0.0,
            "stdev": statistics.pstdev(data) if len(data) > 0 else 0.0
        }

    @staticmethod
    @cached
    def peluang(event, sample):
        return Fraction(event, sample)

    @staticmethod
    @cached
    def turunan(f, x, h=1e-5):
        return (f(x + h) - f(x - h)) / (2 * h)

    @staticmethod
    @cached
    def integral(f, a, b, n=1000):
        dx = (b - a) / n
        area = 0.0
        for i in range(n):
            area += f(a + i*dx) * dx
        return area

    @staticmethod
    @cached
    def ratio(a, b):
        return Fraction(a, b)

    # ======= Absolute Quan additions =======
    @staticmethod
    @cached
    def Erelatif(m_vector, c: float = 299792458.0):
        """
        E = m c^2
        m_vector: scalar atau iterable
        """
        if isinstance(m_vector, (int, float)):
            return m_vector * (c ** 2)
        return [float(m) * (c ** 2) for m in m_vector]

    @staticmethod
    @cached
    def Efoton(f_vector, h: float = 6.62607015e-34):
        """
        E = h f
        f_vector: scalar atau iterable
        """
        if isinstance(f_vector, (int, float)):
            return float(h) * f_vector
        return [float(h) * float(f) for f in f_vector]

    @staticmethod
    @cached
    def compress_array(x, M=None):
        if isinstance(x, (int, float)):
            arr = [float(x)]
        else:
            arr = list(map(float, x))
        eps = 1e-12
        if M is None:
            if len(arr) == 0:
                M = 1.0
            else:
                median = statistics.median([abs(v) for v in arr]) + eps
                M = max(median, eps)
        result = []
        for val in arr:
            result.append(math.copysign(math.log1p(abs(val) / M), val))
        return result if len(result) > 1 else result[0]

    @staticmethod
    @cached
    def build_C_vector(N, T_vals=None, P3_vals=None, L_vals=None, M_vals=None, GeomAlg_vals=None, 
                       S_vals=None, Calc_vals=None, B_vals=None, fallback_random=False):
        def _safe_vec(v, N):
            if v is None:
                return [0.0] * N
            if isinstance(v, (int, float)):
                return [float(v)] * N
            v = list(map(float, v))
            if len(v) < N:
                return list(islice(cycle(v), N))  # ulang sampai panjang N
            return v[:N]
        rand = [random.gauss(0, 1) for _ in range(N)] if fallback_random else [0.0] * N
        T = _safe_vec(T_vals, N)
        P3 = _safe_vec(P3_vals, N)
        L = _safe_vec(L_vals, N)
        M_ = _safe_vec(M_vals, N)
        GeomAlg = _safe_vec(GeomAlg_vals, N)
        S = _safe_vec(S_vals, N)
        Calc = _safe_vec(Calc_vals, N)
        B = _safe_vec(B_vals, N)
        combined = [T[i] + P3[i] + L[i] + M_[i] + GeomAlg[i] + S[i] + Calc[i] + B[i] + rand[i] for i in range(N)]
        compressed = Quan.compress_array(combined)
        # return sebagai complex (dengan imajiner 0)
        return [complex(val, 0.0) for val in compressed]
    
    @staticmethod
    @cached
    def build_H_eff(E_rel_vec, E_ph_vec, interaction_matrix=None, coupling_scale=1e-6, cutoff=None):
        E_rel = list(map(float, E_rel_vec))
        E_ph = list(map(float, E_ph_vec))
        N = len(E_rel)
        # Matriks diagonal utama
        H = [[0j for _ in range(N)] for _ in range(N)]
        for i in range(N):
            H[i][i] = complex(E_rel[i] + E_ph[i], 0.0)
        if interaction_matrix is not None:
            # adaptasi ukuran
            A = [[0.0 for _ in range(N)] for _ in range(N)]
            rows = len(interaction_matrix)
            cols = len(interaction_matrix[0])
            for i in range(min(N, rows)):
                for j in range(min(N, cols)):
                    A[i][j] = float(interaction_matrix[i][j])

            # cutoff
            if cutoff is not None:
                for i in range(N):
                    for j in range(N):
                        if abs(A[i][j]) < float(cutoff):
                            A[i][j] = 0.0
            # tambahkan ke H
            for i in range(N):
                for j in range(N):
                    H[i][j] += coupling_scale * complex(A[i][j], 0.0)
        return H

    @staticmethod
    @cached
    def expm_apply(H, state, steps=20):
        N = len(state)
        # Hermitian symmetrize
        Hc = [[(H[i][j] + H[j][i].conjugate())/2 for j in range(N)] for i in range(N)]
        iH = [[1j * Hc[i][j] for j in range(N)] for i in range(N)]
        # helper matrix multiply
        def matmul(A, B):
            def dot(i, j): return sum(A[i][k]*B[k][j] for k in range(N))
            return [list(starmap(dot, [(i, j) for j in range(N)])) for i in range(N)]
        def matvec(A, v):
            def dot(i): return sum(A[i][k]*v[k] for k in range(N))
            return list(starmap(dot, [(i,) for i in range(N)]))

        # scaling and squaring: reduce norm for stability
        normH = max(abs(iH[i][j]) for i in range(N) for j in range(N))
        s = max(0, int(math.log2(normH)))  # scale factor
        A = [[val/(2**s) for val in row] for row in iH]
        # series expansion
        I = [[1 if i==j else 0 for j in range(N)] for i in range(N)]
        U = [row[:] for row in I]
        term = [row[:] for row in I]
        fact = 1
        for k in range(1, steps+1):
            term = matmul(term, A)
            fact *= k
            for i in range(N):
                for j in range(N):
                    U[i][j] += term[i][j]/fact
        # undo scaling
        for _ in range(s):
            U = matmul(U, U)
        return matvec(U, state)

    @staticmethod
    @cached
    def qft(state):
        N = len(state)
        result = []
        for k in range(N):
            s = 0
            for n in range(N):
                s += state[n] * cmath.exp(2j * math.pi * k * n / N)
            result.append(s / math.sqrt(N))
        return result

    @staticmethod
    def variational_layer(state, phase_params=None):
        N = len(state)
        if phase_params is None:
            phase = [random.gauss(0.0, 0.01) for _ in range(N)]
        elif isinstance(phase_params, (int, float)):
            phase = [float(phase_params)] * N
        else:
            phase = list(itertools.islice(itertools.cycle(phase_params), N))
        return [amp * cmath.exp(1j * theta) for amp, theta in zip(state, phase)]

    @staticmethod
    @cached
    def normalize(state, eps=1e-12):
        s = 0.0
        for x in state:
            s += (x.real*x.real + x.imag*x.imag)
        norm = math.sqrt(s)
        if norm <= eps:
            return state
        inv = 1.0 / norm
        for i in range(len(state)):
            state[i] *= inv
        return state

    @staticmethod
    def measure_topk(state, top_k=5):
        probs = [abs(x)**2 for x in state]
        total = math.fsum(probs)
        if total <= 0:
            probs = [1/len(probs)]*len(probs)
        else:
            probs = [p/total for p in probs]
        idx = random.choices(range(len(probs)), weights=probs, k=1)[0]
        bitstr = format(idx, f"0{int(math.log2(len(probs)))}b")

        # top-k via heap
        k = min(top_k, len(probs))
        top = heapq.nlargest(k, enumerate(probs), key=lambda x: x[1])
        stats = {
            "mean": statistics.mean(probs),
            "median": statistics.median(probs),
            "stdev": statistics.pstdev(probs) if len(probs) > 1 else 0.0
        }
        return {
            "result_index": idx,
            "result_bitstring": bitstr,
            "probabilities": probs,
            "top_k": top,
            "stats": stats
        }

    @staticmethod
    @cached
    def fft(x):
        # x: list of complex, len N power of two
        N = len(x)
        # bit-reversal permutation
        j = 0
        for i in range(1, N):
            bit = N >> 1
            while j & bit:
                j ^= bit
                bit >>= 1
            j |= bit
            if i < j:
                x[i], x[j] = x[j], x[i]
        # Danielson-Lanczos
        m = 2
        while m <= N:
            theta = -2j * math.pi / m
            w_m = cmath.exp(theta)
            for k in range(0, N, m):
                w = 1+0j
                for j in range(m//2):
                    t = w * x[k + j + m//2]
                    u = x[k + j]
                    x[k + j] = u + t
                    x[k + j + m//2] = u - t
                    w *= w_m
            m *= 2
        return x

    @staticmethod
    @cached
    def linspace(start, stop, num):
        return [start + i * (stop - start)/(num - 1) for i in range(num)] if num > 1 else [start]

    @staticmethod
    @cached
    def mean(vec):
        return sum(vec) / len(vec) if vec else 0.0

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Quantum:
    """
    Quantum Infinity (level 10) - Pure Python version
    """
    def __init__(self, qubit_size=4, n_cores=2, seed=None, use_absolute=True):
        self.qubit_size = int(qubit_size)
        self.state = self.initialize()
        self.gates = []
        self.entangled_pairs = []
        self.n_cores = max(1, min(int(n_cores), cpu_count()))
        self._rng = random.Random(seed)
        self._pool = None
        self.debug_compact = True
        self._damping = 0.995
        self.use_absolute = bool(use_absolute)
        atexit.register(self.close_pool)

    # === Representation ===
    def initialize(self):
        n = 2**self.qubit_size
        self._real = array('d', [0.0] * n)
        self._imag = array('d', [0.0] * n)
        self._real[0] = 1.0
        self._imag[0] = 0.0

    # --- helper: kron ---
    @cached
    def kron(A, B):
        return [[a*b for a, b in product(rowA, rowB)] for rowA in A for rowB in B]

    # --- helper: matrix-vector multiply ---
    @cached
    def matvec(A_flat, v_real, v_imag, n, m):
        out_r = array('d', [0.0]*n)
        out_i = array('d', [0.0]*n)
        for i in range(n):
            sumr = 0.0; sumi = 0.0
            base = i*m
            for k in range(m):
                ar = A_flat[base + k]  # assume real matrix
                vr = v_real[k]; vi = v_imag[k]
                sumr += ar * vr
                sumi += ar * vi
            out_r[i] = sumr
            out_i[i] = sumi
        return out_r, out_i

    # === Gates ===
    @cached
    def apply_gate(self, gate, qubit_index, damping=1.0):
        # gate: [[g00,g01],[g10,g11]] each complex (tuple of (r,i) or complex)
        n = 1 << self.qubit_size
        stride = 1 << qubit_index
        real = self._real
        imag = self._imag
        g00 = complex(gate[0][0]); g01 = complex(gate[0][1])
        g10 = complex(gate[1][0]); g11 = complex(gate[1][1])
        for base in range(0, n, 2*stride):
            for i in range(base, base + stride):
                ar = real[i]; ai = imag[i]
                br = real[i + stride]; bi = imag[i + stride]
                # compute a' = g00*a + g01*b
                a_pr = (g00.real*ar - g00.imag*ai) + (g01.real*br - g01.imag*bi)
                a_pi = (g00.real*ai + g00.imag*ar) + (g01.real*bi + g01.imag*br)
                # compute b' = g10*a + g11*b
                b_pr = (g10.real*ar - g10.imag*ai) + (g11.real*br - g11.imag*bi)
                b_pi = (g10.real*ai + g10.imag*ar) + (g11.real*bi + g11.imag*br)
                # damping and assign
                real[i], imag[i] = a_pr * damping, a_pi * damping
                real[i + stride], imag[i + stride] = b_pr * damping, b_pi * damping

    @cached
    def hadamard(self, index):
        H = [[1, 1], [1, -1]]
        H = [[x / math.sqrt(2) for x in row] for row in H]
        self.apply_gate(H, index)

    @cached
    def pauli_x(self, index):
        X = [[0, 1], [1, 0]]
        self.apply_gate(X, index)
    @cached
    def pauli_y(self, index):
        Y = [[0, -1j], [1j, 0]]
        self.apply_gate(Y, index)
    @cached
    def pauli_z(self, index):
        Z = [[1, 0], [0, -1]]
        self.apply_gate(Z, index)

    @cached
    def cnot(state, control, target):
        N = len(state)
        for i in range(N):
            if (i >> control) & 1:
                j = i ^ (1 << target)  # flip target bit
                # swap amplitudes (careful to avoid double-swap)
                if i < j:
                    state[i], state[j] = state[j], state[i]

    @cached
    def entangle(self, q1, q2):
        pair = (int(q1), int(q2))
        if pair not in self.entangled_pairs:
            self.entangled_pairs.append(pair)

    # === Measurement / summary ===
    def measure(self, top_k=5):
        probs = [abs(x) ** 2 for x in self.state]
        total = sum(probs)
        if total <= 0:
            probs = [1 / len(probs)] * len(probs)
        else:
            probs = [p / total for p in probs]
        idx = random.choices(range(len(probs)), weights=probs, k=1)[0]
        result = format(idx, f'0{self.qubit_size}b')
        # entanglement enforcement
        if self.entangled_pairs:
            rlist = list(result)
            for q1, q2 in self.entangled_pairs:
                if rlist[q1] != rlist[q2]:
                    rlist[q2] = rlist[q1]
            result = "".join(rlist)

        # top-k with heap
        k = min(int(top_k), len(probs))
        top_idx = heapq.nlargest(k, enumerate(probs), key=lambda x: x[1])
        top_idx_desc = [(i, float(p)) for i, p in top_idx]
        probs_array = array('d', probs)
        stats = {
            "mean": float(statistics.mean(probs)),
            "median": float(statistics.median(probs)),
            "stdev": float(statistics.pstdev(probs)) if len(probs) > 1 else 0.0
        }
        return {
            "result": result,
            "probabilities": probs_array,
            "top_k": top_idx_desc,
            "total_prob_sum": float(total),
            "stats": stats
        }
    
    # === Worker for multiprocessing (uses Quan utilities) ===
    @staticmethod
    def _worker_update_seeded(seed, state_chunk, factor, damping):
        rng = random.Random(seed)
        chunk = list(state_chunk)
        # bikin noise mirip normal distribution (Box-Muller transform)
        noise = []
        for _ in chunk:
            # normal approx: mean=0, std=0.001*max(1,|factor|)
            std = 0.001 * max(1.0, abs(factor))
            u1, u2 = rng.random(), rng.random()
            z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2 * math.pi * u2)
            noise.append(z * std)
        # update: (chunk * factor + noise) * damping
        updated = []
        for val, n in zip(chunk, noise):
            new_val = (val * factor + n) * damping
            updated.append(new_val)
        return updated

    class helpers:
        # === Multiprocessing update ===
        def unstable_multiprocessing_update(self, factor: float = 1.0):
            if not self.state:
                return
            n_cores = max(1, min(2, int(self.n_cores)))

            # manual array split (pure python)
            chunk_size = max(1, len(self.state) // n_cores)
            chunks = [self.state[i:i + chunk_size] for i in range(0, len(self.state), chunk_size)]
            seeds = [self._rng.randint(0, 2**31 - 1) for _ in chunks]
            args = [(s, c, float(factor), float(self._damping)) for s, c in zip(seeds, chunks)]
            if self._pool is None:
                os.environ.setdefault("OMP_NUM_THREADS", "1")
                self._pool = Pool(processes=n_cores, maxtasksperchild=200)
            results = self._pool.starmap(Quantum._worker_update_seeded, args)
            self.state = list(itertools.chain.from_iterable(results))
            # normalize vector (l2 norm)
            norm_val = math.sqrt(sum(abs(x) ** 2 for x in self.state))
            if norm_val > 0:
                self.state = [x / norm_val for x in self.state]

        # === Helper memory ===
        @cached
        def helper_memory(self, enable_trace: bool = True, compress: bool = True):
            gc.collect()
            state_ref = weakref.ref(self.state)
            if compress and self.state is not None:
                # turunkan presisi: ubah complex128 → complex32 (simulasi, tetap python complex)
                self.state = [complex(float(val.real), float(val.imag)) for val in self.state]
            snapshot_info = None
            if enable_trace:
                try:
                    tracemalloc.start()
                    snapshot = tracemalloc.take_snapshot()
                    top_stats = snapshot.statistics("lineno")
                    snapshot_info = [
                        (str(stat.traceback[0]), stat.size / 1024)
                        for stat in top_stats[:5]
                    ]
                    tracemalloc.stop()
                except Exception:
                    snapshot_info = None
            return {
                "state_ref_alive": state_ref() is not None,
                "dtype": "complex (python built-in)",
                "length": len(self.state),
                "snapshot": snapshot_info
            }

    # === Absolute-Quan evolution (pure python) ===
    @cached
    def evolve_absolute(self, m_vec=None, f_vec=None, interaction_matrix=None, coupling_scale=1e-6, cutoff=None,
                        apply_qft=True, apply_variational=True, phase_params=None, compress_M=None, eps_regularizer=None):
        N = len(self.state)
        m_vec = [0.0] * N if m_vec is None else m_vec
        f_vec = [0.0] * N if f_vec is None else f_vec
        # untuk demo: Erel, Eph dummy pakai jumlah sederhana
        Erel = sum(m_vec) * coupling_scale
        Eph = sum(f_vec) * coupling_scale

        # build Hamiltonian dummy
        H = [[(Erel + Eph) if i == j else 0 for j in range(N)] for i in range(N)]

        # apply exp(iH) (aproksimasi: diag matrix)
        try:
            new_state = []
            for i, val in enumerate(self.state):
                phase = H[i][i] if i < len(H) else 0
                new_state.append(val * cmath.exp(1j * phase))
            self.state = new_state
        except Exception:
            avg_diag = sum(H[i][i] for i in range(min(N, len(H)))) / N
            self.state = [val * cmath.exp(1j * avg_diag) for val in self.state]
        if apply_qft:
            self.state = [x / math.sqrt(N) for x in Quan.fft(self.state)]
        if apply_variational:
            # dummy variational: shift phases
            shift = (phase_params or 0.1)
            self.state = [val * cmath.exp(1j * shift) for val in self.state]

        # compress + restore phases
        real_part = [val.real for val in self.state]
        compressed = Quan.compress_array(real_part, M=compress_M)
        # expand kembali ke panjang N dengan repeat
        expanded = (compressed * (N // len(compressed) + 1))[:N]
        phases = [cmath.phase(val) for val in self.state]
        self.state = [expanded[i] * cmath.exp(1j * phases[i]) for i in range(N)]
        if eps_regularizer is None:
            eps_regularizer = max(1e-12, 1e-12 * (N ** 0.5))
        self.state = Quan.normalize(self.state, eps_adaptive=eps_regularizer)
        return self.state

    # === Grover (pure python) ===
    def grover(self, oracle_mask_or_fn):
        N = len(self.state)
        if callable(oracle_mask_or_fn):
            mask = oracle_mask_or_fn(self.state)
        else:
            mask = [bool(x) for x in oracle_mask_or_fn]
        # hadamard on each qubit → approx as balanced superposition
        H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
             [1 / math.sqrt(2), -1 / math.sqrt(2)]]

        # (demo: apply sekali untuk semua qubit)
        superpos = []
        for val in self.state:
            superpos.extend([H[0][0]*val + H[0][1]*val, H[1][0]*val + H[1][1]*val])
        self.state = superpos[:N]
        iterations = int(math.floor(math.pi/4 * math.sqrt(N)))
        for _ in range(iterations):
            # oracle: flip phase
            self.state = [(-val if mask[i] else val) for i, val in enumerate(self.state)]
            mean_amp = Quan.mean(self.state)
            self.state = [2*mean_amp - val for val in self.state]
        return self.measure()

    @cached
    def shor(self, n):
        return f"Factoring {n} (simulated)"

    @cached
    def qft(self):
        N = len(self.state)
        self.state = [x / math.sqrt(N) for x in self.fft(self.state)]
        self.state = self.normalize(self.state)
        return self.measure()

    def vqe(self, cost_function, iterations: int = 10):
        loss = None
        for i in range(int(iterations)):
            # simulasi absolute evolve (dummy)
            if self.use_absolute:
                self.state = [val * (1 - 1e-6) for val in self.state]
            self.state = [val * (0.99 + 0.01*random.random()) for val in self.state]
            loss = float(cost_function(self.state))
            if self.debug_compact:
                _log.info(f"[VQE] iter={i+1}/{iterations} loss={loss:.6f}")
        return {"state": self.state, "loss": loss}

    def qaoa(self, hamiltonian, iterations: int = 10):
        N = len(self.state)
        for i in range(int(iterations)):
            try:
                # simple exponentiation of diagonal Hamiltonian
                U = self.expm_diag(hamiltonian)
                self.state = self.matrix_mul(U, self.state)
            except Exception:
                mean_diag = sum(hamiltonian[i][i] for i in range(N)) / N
                self.state = [val * cmath.exp(-1j * mean_diag) for val in self.state]

            # simulasi unstable update
            self.state = [val * 0.99 for val in self.state]
        return self.measure()

    # === Debug / helper ===
    def debug_state(self, top_n: int = 5):
        meas = self.measure(top_k=top_n)
        _log.info("🔹 Quantum State Summary:")
        _log.info(f"  bitstring (sampled) : {meas['result']}")
        _log.info(f"  top_{top_n}          : {meas['top_k']}")
        stats = meas.get("stats", {})
        _log.info(f"  probs mean/median/stdev : {stats.get('mean'):.6e} / {stats.get('median'):.6e} / {stats.get('stdev'):.6e}")
        _log.info(f"  gates applied count     : {len(self.gates)}")
        _log.info(f"  entangled pairs         : {self.entangled_pairs}")

    def compact_summary(self, top_n: int = 5):
        meas = self.measure(top_k=top_n)
        return {
            "sampled_bitstring": meas["result"],
            "top_k": meas["top_k"],
            "stats": meas["stats"],
            "gates_applied": len(self.gates),
            "entangled_pairs": list(self.entangled_pairs)
        }

    # === Pool management ===
    def close_pool(self):
        if getattr(self, "_pool", None) is not None:
            try:
                self._pool.close()
                self._pool.join()
            except Exception:
                pass
            self._pool = None

    @cached
    def reset(self):
        self.state = self.initialize()
        self.gates.clear()
        self.entangled_pairs.clear()

    @cached
    def summary(self):
        state_norm = math.sqrt(sum(abs(x)**2 for x in self.state))
        stats = {
            "qubit_size": self.qubit_size,
            "gates_applied": len(self.gates),
            "entangled_pairs": list(self.entangled_pairs),
            "state_norm": float(state_norm)
        }
        return stats

if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    q = Quantum(qubit_size=5, n_cores=2, seed=42, use_absolute=True)
    try:
        print("Before:", q.compact_summary(top_n=3))
        t0 = time.perf_counter()
        q.unstable_multiprocessing_update(factor=1.0)
        t1 = time.perf_counter()
        print("Multiproc update took", t1 - t0)
        # one Absolute-Quan evolve step (example small mass/freq)
        N = len(q.state)
        m_vec = Quan.linspace(0.1, 0.5, N)
        f_vec = Quan.linspace(1e12, 1e13, N)
        q.evolve_absolute(m_vec=m_vec, f_vec=f_vec, coupling_scale=1e-6)
        print("After evolve:", q.compact_summary(top_n=3))
    finally:
        q.close_pool()