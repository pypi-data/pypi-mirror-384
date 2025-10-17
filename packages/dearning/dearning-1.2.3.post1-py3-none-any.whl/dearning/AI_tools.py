import os, ast, struct, wave, logging, subprocess, platform, math, random
import re, array
from statistics import mean
from pathlib import Path
from .utils import cached

logging.basicConfig(level=logging.INFO)

class DLP:
    def __init__(self, lang="en"):
        self.lang = lang
        # kamus sederhana untuk sentiment
        self.positive_words = {"good", "happy", "love", "great", "excellent", "amazing", "nice"}
        self.negative_words = {"bad", "sad", "hate", "terrible", "awful", "poor", "angry"}
    @cached
    def analyze_sentiment(self, text):
        words = re.findall(r"\w+", text.lower())
        pos_score = sum(1 for w in words if w in self.positive_words)
        neg_score = sum(1 for w in words if w in self.negative_words)
        polarity = (pos_score - neg_score) / (len(words) + 1e-8)
        subjectivity = (pos_score + neg_score) / (len(words) + 1e-8)
        if polarity > 0:
            label = "positive"
        elif polarity < 0:
            label = "negative"
        else:
            label = "neutral"
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "label": label
        }

    def extract_nouns(self, text):
        # fallback sederhana: ambil kata kapital & panjang > 3
        words = text.split()
        nouns = [w.strip(".,!?") for w in words if w.istitle() and len(w) > 3]
        return nouns
    @cached
    def pos_tagging(self, text):
        # aturan sederhana: kata kapital = NNP, ada 'ing' = VBG, default NN
        words = text.split()
        tags = []
        for w in words:
            if w.istitle():
                tags.append((w, "NNP"))
            elif w.endswith("ing"):
                tags.append((w, "VBG"))
            else:
                tags.append((w, "NN"))
        return tags

    def summarize(self, text, max_sentences=2):
        sentences = re.split(r"[.!?]\s+", text)
        return ". ".join(sentences[:max_sentences]) + ("." if len(sentences) > max_sentences else "")
    @cached
    def process(self, text):
        return {
            "sentiment": self.analyze_sentiment(text),
            "nouns": self.extract_nouns(text),
            "pos_tags": self.pos_tagging(text),
            "summary": self.summarize(text)
        }

class RLTools:
    def __init__(self, size=5, terminal_states={(4,4): 1.0}):
        self.size = size
        self.terminal_states = terminal_states
        self.agents = []

    # === Environment ===
    def reset_env(self):
        self.state = (0, 0)
        return self.state

    def get_actions(self):
        return ["up", "down", "left", "right"]

    def step(self, action):
        x, y = self.state
        if action == "up":    x = max(0, x-1)
        if action == "down":  x = min(self.size-1, x+1)
        if action == "left":  y = max(0, y-1)
        if action == "right": y = min(self.size-1, y+1)
        self.state = (x, y)

        reward = self.terminal_states.get(self.state, 0.0)
        done = self.state in self.terminal_states
        return self.state, reward, done

    # === Tambah Agent ===
    def add_q_agent(self, name="q_agent", alpha=0.1, epsilon=0.1, gamma=0.9):
        agent = {
            "name": name,
            "type": "q",
            "q_table": {},
            "alpha": alpha,
            "epsilon": epsilon,
            "gamma": gamma
        }
        self.agents.append(agent)
        return agent

    def add_random_agent(self, name="random"):
        agent = {"name": name, "type": "random"}
        self.agents.append(agent)
        return agent

    # === Agent Logic ===
    def choose_action(self, agent, state):
        actions = self.get_actions()
        if agent["type"] == "random":
            return random.choice(actions)
        if random.random() < agent["epsilon"]:
            return random.choice(actions)
        q_vals = [agent["q_table"].get((state,a),0.0) for a in actions]
        max_q = max(q_vals)
        best_actions = [a for a,q in zip(actions,q_vals) if q==max_q]
        return random.choice(best_actions)

    def update_q(self, agent, state, action, reward, next_state):
        actions = self.get_actions()
        old_q = agent["q_table"].get((state,action), 0.0)
        next_max = max([agent["q_table"].get((next_state,a),0.0) for a in actions])
        new_q = old_q + agent["alpha"]*(reward + agent["gamma"]*next_max - old_q)
        agent["q_table"][(state,action)] = new_q

    # === Jalankan Episode ===
    def run(self, episodes=50):
        for agent in self.agents:
            for ep in range(episodes):
                state = self.reset_env()
                done, total_reward = False, 0
                while not done:
                    action = self.choose_action(agent, state)
                    next_state, reward, done = self.step(action)
                    if agent["type"] == "q":
                        self.update_q(agent, state, action, reward, next_state)
                    state = next_state
                    total_reward += reward
                print(f"Agent {agent['name']} Episode {ep+1}, Total Reward: {total_reward}")

# === TEXT TO SPEECH ===
class TTS:
    def __init__(self, voice=None, rate=150, volume=1.0):
        self.voice = voice
        self.rate = rate
        self.volume = volume

    def speak(self, text, filename="tts_output"):
        """Pure Python wrapper untuk TTS bawaan OS"""
        filepath = Path.cwd() / f"{filename}.wav"
        system_name = platform.system()
        try:
            if system_name == "Windows":
                # Gunakan PowerShell + SAPI.SpVoice
                ps_script = f'''
                Add-Type -AssemblyName System.Speech
                $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $speak.Rate = {int(self.rate/50)}
                $speak.Volume = {int(self.volume*100)}
                $speak.Speak([Console]::In.ReadToEnd())
                '''
                subprocess.run(["powershell", "-Command", ps_script], input=text, text=True)
            elif system_name == "Darwin":  # macOS
                subprocess.run(["say", text])
            elif system_name == "Linux" or "Android" in system_name:
                # espeak output langsung
                cmd = ["espeak", f"-s{self.rate}", f"-a{int(self.volume*200)}"]
                if self.voice:
                    cmd.append(f"-v{self.voice}")
                cmd.append(text)
                subprocess.run(cmd)
            else:
                print("[TTS] Unsupported system.")
        except Exception as e:
            print(f"[TTS] Error: {e}")
# === MEMORY MANAGEMENT ===
MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "Memory", "DATAI.py")
MEMORY_VAR = "memory"

class AImemory:
    def __init__(self):
        self.memory = self._load_memory()

    def _load_memory(self):
        if not os.path.exists(MEMORY_PATH):
            with open(MEMORY_PATH, "w") as f:
                f.write(f"{MEMORY_VAR} = []\n")
            return []

        with open(MEMORY_PATH, "r") as f:
            try:
                content = f.read()
                parsed = ast.parse(content, mode='exec')
                for node in parsed.body:
                    if isinstance(node, ast.Assign) and node.targets[0].id == MEMORY_VAR:
                        return ast.literal_eval(ast.unparse(node.value))
            except Exception as e:
                print("❌ Gagal baca memori:", e)
        return []

    def _save_memory(self):
        with open(MEMORY_PATH, "w") as f:
            f.write(f"{MEMORY_VAR} = {repr(self.memory)}\n")

    def add(self, data):
        if data not in self.memory:
            self.memory.append(data)
            self._save_memory()

    def remove(self, data):
        if data in self.memory:
            self.memory.remove(data)
            self._save_memory()

    def clear(self):
        self.memory = []
        self._save_memory()

    def get_all(self):
        return self.memory

    def contains(self, query):
        return query in self.memory

class image:
    @staticmethod
    def load_image(path=None, target_size=(64, 64), grayscale=False):
        """
        Load image:
        - Jika path .ppm/.pgm → baca dengan pure Python (struct + io)
        - Jika path None → generate dummy pattern
        """
        w, h = target_size
        mode = "L" if grayscale else "RGB"
        if path is None:
            # Fallback: generate dummy pola
            if grayscale:
                data = [((i + j) % 256) / 255.0 for i in range(h) for j in range(w)]
            else:
                data = [((i + j) % 256) / 255.0 for i in range(h) for j in range(w) for _ in range(3)]
            return array("f", data)

        # Buka file biner manual
        with open(path, "rb") as f:
            header = f.readline().strip()
            if header in [b"P5", b"P6"]:  # Netpbm binary (PGM/PPM)
                dims = f.readline().strip()
                while dims.startswith(b"#"):  # skip komentar
                    dims = f.readline().strip()
                width, height = map(int, dims.split())
                maxval = int(f.readline().strip())
                raw = f.read()
                if header == b"P5":  # grayscale
                    pixels = list(raw)
                else:  # RGB
                    pixels = list(raw)

                # Normalisasi ke 0–1
                data = [p / maxval for p in pixels]
                return array("f", data)
            else:
                raise ValueError("Format tidak dikenali (gunakan PGM/PPM atau dummy).")

    @staticmethod
    def flatten_image(img_array):
        return list(img_array)

# === Audio ===
class audio:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.channels = 1
        self.sample_width = 2  # 16-bit PCM
        self.outdir = Path.cwd() / "audio_out"
        self.outdir.mkdir(exist_ok=True)
        print(f"[DOaudio] Initialized at {self.sample_rate}Hz, output -> {self.outdir}")

    # --- Audio Generator ---
    @cached
    def generate_audio(self, freq=440, duration=1.0, amplitude=0.5):
        """Generate sine wave (pure Python)"""
        n_samples = int(self.sample_rate * duration)
        wave_data = []
        for n in range(n_samples):
            t = n / self.sample_rate
            value = amplitude * math.sin(2 * math.pi * freq * t)
            wave_data.append(int(value * 32767))
        return wave_data

    # --- Simple Low-Pass Filter (moving average) ---
    @cached
    def filter_audio(self, audio_data, window_size=5):
        filtered = []
        for i in range(len(audio_data)):
            start = max(0, i - window_size + 1)
            window = audio_data[start:i+1]
            avg = sum(window) / len(window)
            filtered.append(int(avg))
        return filtered

    # --- Save to WAV ---
    def save_audio(self, filename, audio_data):
        filepath = self.outdir / f"{filename}.wav"
        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.sample_rate)
            for sample in audio_data:
                wf.writeframes(struct.pack('<h', sample))  # PCM 16-bit
        print(f"[DOaudio] Saved audio to {filepath}")
        return filepath

    # --- Play using system tools ---
    def play_audio(self, filepath):
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[DOaudio] File {filepath} not found")
            return
        system_name = platform.system()
        try:
            if system_name == "Windows":
                os.startfile(str(filepath))
            elif system_name == "Darwin":  # macOS
                subprocess.run(["afplay", str(filepath)])
            elif system_name == "Linux" or "Android" in system_name:
                subprocess.run(["aplay", str(filepath)])
            else:
                print("[DOaudio] Unsupported system for playback.")
        except Exception as e:
            print(f"[DOaudio] Error playing audio: {e}")

    # --- Request play directly from script ---
    def request_play(self, filename="output", freq=440, duration=1.0):
        """Generate, save, and play audio in one step"""
        data = self.generate_audio(freq=freq, duration=duration)
        filepath = self.save_audio(filename, data)
        self.play_audio(filepath)

# === Video ===
class video:
    @staticmethod
    def _read_color_table(f, size):
        return [tuple(f.read(3)) for _ in range(size)]

    @staticmethod
    def _lzw_decode(data, min_code_size):
        """Sederhana LZW decoder untuk GIF image data"""
        clear_code = 1 << min_code_size
        end_code = clear_code + 1
        code_size = min_code_size + 1
        dict_size = end_code + 1
        dictionary = {i: [i] for i in range(clear_code)}
        dictionary[clear_code] = []
        dictionary[end_code] = []
        bit_buffer, bits_in_buffer = 0, 0
        pos = 0
        result = []
        prev = []

        def read_code():
            nonlocal bit_buffer, bits_in_buffer, pos
            while bits_in_buffer < code_size and pos < len(data):
                bit_buffer |= data[pos] << bits_in_buffer
                bits_in_buffer += 8
                pos += 1
            code = bit_buffer & ((1 << code_size) - 1)
            bit_buffer >>= code_size
            bits_in_buffer -= code_size
            return code
        while True:
            code = read_code()
            if code == clear_code:
                dictionary = {i: [i] for i in range(clear_code)}
                dictionary[clear_code] = []
                dictionary[end_code] = []
                code_size = min_code_size + 1
                dict_size = end_code + 1
                prev = []
                continue
            elif code == end_code:
                break
            elif code in dictionary:
                entry = dictionary[code]
            elif code == dict_size:
                entry = prev + [prev[0]]
            else:
                raise ValueError("LZW decode error")

            result.extend(entry)
            if prev:
                dictionary[dict_size] = prev + [entry[0]]
                dict_size += 1
                if dict_size >= (1 << code_size) and code_size < 12:
                    code_size += 1
            prev = entry
        return result

    @staticmethod
    @cached
    def extract_gif(path, max_frames=10):
        frames = []
        with open(path, "rb") as f:
            header = f.read(6)
            if not header.startswith(b"GIF"):
                raise ValueError("Bukan file GIF")
            # Logical Screen Descriptor
            width, height, packed, bg, aspect = struct.unpack("<HHBBB", f.read(7))
            global_ct_flag = (packed & 0b10000000) >> 7
            global_ct_size = 2 ** ((packed & 0b00000111) + 1)
            gct = video._read_color_table(f, global_ct_size) if global_ct_flag else []
            while len(frames) < max_frames:
                block_introducer = f.read(1)
                if not block_introducer:
                    break
                if block_introducer == b",":
                    # Image Descriptor
                    x, y, w, h, packed = struct.unpack("<HHHHB", f.read(9))
                    local_ct_flag = (packed & 0b10000000) >> 7
                    local_ct_size = 2 ** ((packed & 0b00000111) + 1)
                    lct = video._read_color_table(f, local_ct_size) if local_ct_flag else []
                    color_table = lct if local_ct_flag else gct

                    # Image data
                    lzw_min_code_size = ord(f.read(1))
                    data = bytearray()
                    while True:
                        block_size = ord(f.read(1))
                        if block_size == 0:
                            break
                        data.extend(f.read(block_size))
                    indices = video._lzw_decode(data, lzw_min_code_size)
                    # Map ke RGB
                    frame = []
                    for idx in indices[:w*h]:
                        r, g, b = color_table[idx]
                        frame.extend([r/255, g/255, b/255])
                    frames.append(frame)
                elif block_introducer == b";":  # Trailer
                    break
                else:
                    # Skip extension block
                    while True:
                        block_size = ord(f.read(1))
                        if block_size == 0:
                            break
                        f.read(block_size)
        return frames

# === Pemahaman cepat (analisis ringan) ===
class Qkanalyze:
    @staticmethod
    @cached
    def top_kprobs(preds, k=3):
        """Ambil k probabilitas terbesar dari list"""
        sorted_idx = sorted(range(len(preds)), key=lambda i: preds[i], reverse=True)
        return [(i, float(preds[i])) for i in sorted_idx[:k]]

    @staticmethod
    @cached
    def summarize_array(arr):
        """Ringkasan nilai list 1D/2D (pure python)"""
        # flatten kalau nested list
        flat = [x for row in arr for x in (row if isinstance(row, (list, tuple)) else [row])]
        return {
            "min": float(min(flat)),
            "max": float(max(flat)),
            "mean": float(mean(flat)),
            "shape": (len(arr), len(arr[0]) if isinstance(arr[0], (list, tuple)) else 1)
        }