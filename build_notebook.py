# SPDX-FileCopyrightText: 2026 Dr. Christoph Leitner and Marco Giordano, ETH Zurich
# SPDX-License-Identifier: Apache-2.0
"""Builder for the wearable-ultrasound workshop Colab notebook (notebook-as-code).

Run:  py -3.12 build_notebook.py
Output: wearable_us_student.ipynb + wearable_us_teacher.ipynb at the repo root.

Cells are appended in order; extend CELLS as we build act by act. Keeping the
notebook generated (not hand-edited JSON) gives clean diffs and one source.
"""
import nbformat as nbf
from pathlib import Path

SLUG = "ModularUS/anatomy-wearable-US-system"   # GitHub slug (Colab mirror)
NB_NAME = "wearable_us_student.ipynb"            # student version (TODO blanks)
NB_TEACHER = "wearable_us_teacher.ipynb"         # instructor version (blanks filled)
RAW = f"https://raw.githubusercontent.com/{SLUG}/main"   # raw base for assets/ images
REPO_ROOT = Path(__file__).resolve().parent

nb = nbf.v4.new_notebook()
md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
CELLS = []

# ── C0 · front matter ────────────────────────────────────────────────────
CELLS.append(md(f"""\
# Anatomy of a Wearable Ultrasound System

### From Components to Signals
#### *Dr. Christoph Leitner and Marco Giordano (ETH Zurich, Switzerland)*

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{SLUG}/blob/main/{NB_NAME})

<p align="left"><img src="{RAW}/assets/modulUS.jpg" width="520" alt="The ModulUS wearable-ultrasound platform"></p>

A wearable ultrasound system must do the job of a cart-sized scanner, but using only a patch on the skin, powered by a battery small enough to wear. 
<br> This workshop takes a wearable ultrasound system apart, from front-end components to the digitized signal, to expose **where the energy actually goes, and for what**.
```
size you start from ──────────────────────────► size you design toward
   cart scanner            handheld probe            wearable patch
   ~200 L                     ~200 mL                  ~3 mL
   ≈ a bathtub                ≈ a coffee mug           ≈ a teaspoon
        └─────────  same job, a bathtub poured into a teaspoon (~70,000×)  ─────────┘
```
<br>We run a live acquisition on our **ModulUS** system (a sandbox for wearable-ultrasound development). You then take a hands-on look at the recorded RF and envelope data.
<br>Using that data, you analyse **why receive-channel scaling must be approached carefully** in wearable ultrasound, and what impact excitation frequency has beyond improved resolution.

#### What you will do
```
echo → frequency → sampling → data rate → power → battery → wearable
└─ Exercise 1 ─┘   └─ Exercise 2 ─────┘   └─ Exercise 3 ───────────┘
```
1. ***Exercise 1***: read one real ModulUS echo as **RF** and as **envelope**, and find the frequency it carries.
2. ***Exercise 2***: digitize that echo, compute its **data rate**, and watch it slam into the **on-chip ADC** and **wireless-link** bottlenecks.
3. ***Exercise 3***: weigh what to transmit (**RF**, **envelope**, or **on-device features**) to bring **power** and **battery** within a **small wearable's budget** — and settle on a **receive-channel count it can sustain**.
"""))

# ── C1 · bootstrap (robust on Colab, also runs locally) ──────────────────
CELLS.append(code(f"""\
# === Bootstrap — run me first ===============================================
# Robust on Google Colab (ephemeral VM) and when run locally from the repo.
import sys, os

IN_COLAB = "google.colab" in sys.modules
SLUG = "{SLUG}"                       # GitHub repo (Colab mirror)
REPO = SLUG.split("/")[1]

if IN_COLAB:
    # external toolbox: dasIT signal/plot functions (install once per session).
    # Probe the exact submodule we use — guards against partial/shadowed installs.
    try:
        from dasIT.features import signal as _dasIT_probe  # noqa: F401
        print("dasIT: already available, skipping install")
    except ImportError:
        print("dasIT: not found — installing from GitHub...")
        !pip install -q --force-reinstall --no-deps git+https://github.com/ModularUS/dasIT
        from dasIT.features import signal as _dasIT_probe  # noqa: F401  # fail loudly if still broken
        print("dasIT: installed OK")
    # our sandbox repo: clone so you can browse modulus.py and the demo data.
    # Guard on the module file, not just the dir: a failed/partial clone (e.g.
    # while the repo was private) leaves an empty dir behind that would skip the
    # re-clone and shadow a good checkout. Wipe any stale dir, then clone clean.
    if not os.path.isfile(os.path.join(REPO, "modulus.py")):
        !rm -rf {{REPO}}
        !git clone -q https://github.com/{{SLUG}}
    sys.path.insert(0, REPO)
    DATA = os.path.join(REPO, "example_data", "modulus_demo.npz")
else:
    sys.path.insert(0, ".")          # local: repo root on the path
    DATA = os.path.join("example_data", "modulus_demo.npz")

import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({{"figure.dpi": 110, "font.size": 11, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False}})
from modulus import System, Acq, load_traces
from dasIT.features.signal import fftsignal

print("ready —", "Colab" if IN_COLAB else "local")
"""))

# ── C2 · tools & repositories ────────────────────────────────────────────
CELLS.append(md(f"""\
### Tools & repositories

This notebook stands on two pieces, both pulled in by the bootstrap above:

| what | role here | link |
|---|---|---|
| **dasIT** | signal toolbox — spectra, analytic signal, envelope (`fftsignal`, `analytic_signal`, `envelope`) | [github.com/ModularUS/dasIT](https://github.com/ModularUS/dasIT) |
| **ModulUS sandbox** (this repo) | the system digital-twin you design against — `System`, `Acq`, `modulus.py`, and the demo echo in `example_data/` | [github.com/{SLUG}](https://github.com/{SLUG}) |

Everything runs on Colab as-is — nothing to install by hand. The full method is in the ModulUS paper (see **References** at the end).
"""))

# ── EXERCISE 1 · SIGNAL — the recorded echo ──────────────────────────────
CELLS.append(md("""\
## Exercise 1 · The signal — *what the front-end produces*

Ultrasound is an echo game. The probe sends a short **pulse** (a few cycles of sound) then listens for what bounces back from each tissue boundary. The later an echo arrives, the deeper the reflector that made it.

```
        pulse out  ∿∿►
 ┌────┐ ───────────────────────────────────────────►
 │ Tx │           ║          ║                ║
 │ Rx │ ◄───────────────────────────────────────────
 └────┘  echoes in  ∿         ∿∿               ∿
                   skin     muscle            bone
 t = 0 ───────────────────────────────────────────►  time  (depth = c·t / 2)
```

ModulUS hands you the *same* echo in two forms:

- **RF** — the raw radio-frequency waveform straight off the transducer (Pulse → Core), carrier and all.
- **Envelope** — that same RF after the analog **Echo** board strips the carrier, leaving only the echo's shape.

Both place the reflectors at the same depth. What sets them apart is **bandwidth** — and that single difference is the lever the rest of this notebook turns on. Open one real measurement and look.
"""))

CELLS.append(code("""\
# Load ONE ModulUS measurement (real .npz if present, else a labeled synthetic stand-in)
rf, env, fs = load_traces(DATA)
t_us = np.arange(len(rf)) / fs * 1e6          # time axis [µs]

plt.figure(figsize=(8, 3))
plt.plot(t_us, rf, lw=0.8)
plt.xlabel("time [µs]"); plt.ylabel("amplitude")
plt.title(f"Raw RF echo   (fs = {fs/1e6:.0f} Msps,  {len(rf)} samples)")
plt.tight_layout(); plt.show()
"""))

CELLS.append(code("""\
# Same echo, two representations — in time and in frequency.
# RF and envelope live on different scales, so each panel carries TWO y-axes:
# RF on the LEFT (blue), envelope on the RIGHT (red). Spectra via dasIT's Welch
# helper (returns frequency already in MHz).
f_rf,  P_rf  = fftsignal(rf,  fs)
f_env, P_env = fftsignal(env, fs)
C_RF, C_ENV = "#1f77b4", "#d9534f"

fig, ax = plt.subplots(1, 2, figsize=(10, 3.2))

# time domain — left axis: RF, right axis: envelope
axE0 = ax[0].twinx()
h0  = ax[0].plot(t_us, rf,  lw=0.9, color=C_RF,  label="RF")
h0e = axE0.plot(t_us, env, lw=1.6, color=C_ENV, label="envelope")
ax[0].set_xlabel("time [µs]")
ax[0].set_ylabel("RF amplitude", color=C_RF);       ax[0].tick_params(axis="y", colors=C_RF)
axE0.set_ylabel("envelope amplitude", color=C_ENV); axE0.tick_params(axis="y", colors=C_ENV)
axE0.spines["right"].set_visible(True); axE0.spines["right"].set_color(C_ENV); axE0.grid(False)
ax[0].set_title("time domain")
ax[0].legend(h0 + h0e, [l.get_label() for l in h0 + h0e], loc="upper right")

# spectrum — left axis: RF power, right axis: envelope power
axE1 = ax[1].twinx()
h1  = ax[1].plot(f_rf,  P_rf,  lw=1.2, color=C_RF,  label="RF")
h1e = axE1.plot(f_env, P_env, lw=1.2, color=C_ENV, label="envelope")
ax[1].set_xlabel("frequency [MHz]")
ax[1].set_ylabel("RF power", color=C_RF);       ax[1].tick_params(axis="y", colors=C_RF)
axE1.set_ylabel("envelope power", color=C_ENV); axE1.tick_params(axis="y", colors=C_ENV)
axE1.spines["right"].set_visible(True); axE1.spines["right"].set_color(C_ENV); axE1.grid(False)
ax[1].set_title("spectrum"); ax[1].set_xlim(0, fs/2e6)
ax[1].legend(h1 + h1e, [l.get_label() for l in h1 + h1e], loc="upper right")

plt.tight_layout(); plt.show()
"""))

CELLS.append(code("""\
# TODO (a) — compute the power-weighted MEAN frequency of each spectrum.
# Formula (ModulUS paper, eq. 2):   f_mean = sum(f_i * P_i) / sum(P_i)
# Use the arrays from the previous cell: f_rf, P_rf  and  f_env, P_env.
raw_mean = ...     # <-- replace ... using f_rf and P_rf
env_mean = ...     # <-- replace ... using f_env and P_env

# ---- self-check (do not edit) -------------------------------------------
assert raw_mean is not ... and env_mean is not ..., "fill in raw_mean and env_mean above"
assert env_mean < raw_mean, "the envelope should sit at LOWER frequency than the RF"
ratio = raw_mean / env_mean
print(f"RF mean ~ {raw_mean:.2f} MHz    envelope mean ~ {env_mean:.2f} MHz")
print(f"bandwidth reduction ~ {ratio:.1f}x   (ModulUS paper: 2.9 -> 0.7 MHz ~ 4x)")
assert ratio > 2, "expected a clear (>2x) reduction - check your formula"
print("OK - spectral check passed")
"""))

CELLS.append(md("""\
### Resolution — what can this pulse *resolve*?

Exercise 1 paid for bandwidth in data; the transducer **frequency** buys something back — **spatial resolution**. A shorter pulse (higher frequency) splits two reflectors that a long pulse smears into one:

```
 two reflectors a hair apart:   ║║
   low  f  (long pulse):   ∿∿∿∿∿∿   →  one blob    (can't separate them)
   high f  (short pulse):  ∿∿  ∿∿   →  two echoes  (resolved)
```

Axial resolution is about half the spatial pulse length:

$$ \\text{axial\\_res} = n_\\text{cycles}\\cdot\\frac{\\lambda}{2}, \\qquad \\lambda = \\frac{c}{f_\\text{Tx}}, \\qquad c = 1540\\ \\text{m/s} $$

So higher $f_\\text{Tx}$ → shorter $\\lambda$ → finer detail. The catch, waiting in **Exercise 2**: finer detail is **more data**.


| $f_\\text{Tx}$ | $\\lambda$ | axial res (5 cyc) | resolves about |
|---|---|---|---|
| 1 MHz  | 1.54 mm  | 3.9 mm  | a grape |
| 5 MHz  | 0.31 mm  | 0.77 mm | a sesame seed |
| 10 MHz | 0.154 mm | 0.38 mm | a human hair (~0.07 mm) |
| 15 MHz | 0.103 mm | 0.26 mm | a dust mite |

"""))

CELLS.append(code("""\
# The resolution ladder, straight from the Transducer twin in modulus.py
from modulus import Transducer
print("f_Tx [MHz]   axial res [mm]")
for f in (1e6, 5e6, 10e6, 15e6):
    print(f"   {f/1e6:>5.0f}        {Transducer().axial_res(f)*1e3:.2f}")
"""))

CELLS.append(md(r"""### Resolution isn't free — it costs depth

Higher $f_\text{Tx}$ buys finer resolution, but sound also **attenuates more** as
frequency rises — roughly $\alpha \approx 0.5$ dB/cm/MHz (one-way) in soft tissue.
Whatever your receive chain can still pull out of the noise sets a **dynamic-range
(DR) budget**; that budget gets eaten by the round-trip path loss:

$$ d_\text{max}(f) \;\approx\; \frac{\text{DR}}{2\,\alpha\,f} $$

So picking a frequency is really picking a **(depth, resolution)** pair — and a
wearable that wants to see the carotid (≈2 cm) lives in a very different corner
than one aimed at the bladder (≈8 cm). The grey bands below show what each curve
can actually reach.
"""))

CELLS.append(code("""# Depth-vs-frequency under different dynamic-range budgets, with axial resolution
# read off the second x-axis directly below.
from modulus import C_SOUND, N_CYCLES, ALPHA_DB_CM_MHZ, Transducer
DR_BUDGETS = (10, 30, 50, 70, 90)          # dB — dynamic-range scenarios
f = np.linspace(1, 20, 400)                # f_Tx [MHz]

def axial_res_mm(f_MHz):                   # use the same twin the resolution ladder used
    return Transducer().axial_res(f_MHz * 1e6) * 1e3
def f_from_res(r_mm):                      # inverse, for secondary-axis ticks
    return (N_CYCLES * C_SOUND) / (2 * r_mm * 1e-3) / 1e6

fig, ax = plt.subplots(figsize=(7.8, 4.8))
for DR in DR_BUDGETS:
    ax.plot(f, DR / (2 * ALPHA_DB_CM_MHZ * f), label=f"DR = {DR} dB")

# clinical targets a patch might realistically image
targets = [("carotid",       2.0, 3.0,  3.0),
           ("muscle/tendon", 1.0, 4.0,  1.4),
           ("bladder",       5.0, 10.0, 7.5)]
for name, lo, hi, y_label in targets:
    ax.axhspan(lo, hi, color="#d9d9d9", alpha=0.35)
    ax.text(1.3, y_label, name, ha="left", va="center", fontsize=9, color="#444")

ax.set_xlim(1, 20); ax.set_ylim(0, 12.5)
ax.set_xlabel("transmit frequency  f_Tx  [MHz]")
ax.set_ylabel("reachable depth  [cm]")
ax.set_title("Frequency buys resolution, costs depth\\n"
             f"d_max = DR / (2·α·f),   α = {ALPHA_DB_CM_MHZ} dB/cm/MHz")
ax.grid(alpha=0.3); ax.legend(loc="upper right")

# second x-axis, just below the main one, showing axial resolution at the same f_Tx
secax = ax.secondary_xaxis(-0.22, functions=(axial_res_mm, f_from_res))
secax.set_xlabel(f"axial resolution at that f_Tx  [mm]")
secax.set_xticks([2.0, 1.0, 0.5, 0.3, 0.2])      # clean res values, evenly spread on 1/f
secax.set_xticklabels([f"{r:g}" for r in [2.0, 1.0, 0.5, 0.3, 0.2]])

plt.tight_layout(); plt.show()
"""))

# ── EXERCISE 2 · COST — digitize and move the echo ──────────────────────
CELLS.append(md("""\
## Exercise 2 · The cost — *digitizing and moving the echo*

A clean echo is worthless until you can get it off the probe. Digitizing it sets the **data rate** — and in a wearable, that data rate is a firehose aimed at a drinking straw. Start with **Nyquist**: to capture a signal you must sample at least twice its highest frequency.

```
fs        = 2 · f_Tx                 (RF, ~2× the centre frequency)
t_acq     = 2 · D / c                (round trip to depth D)
N         = fs · t_acq               (samples per A-line)
data_rate = N · bits · PRF · nRx     (bits per second)   ← the number that matters
```

An **A-line** is one pulse-echo trace — one transmit and the echoes it returns; `N` is how
many samples that trace holds. (We take the centre frequency `f_Tx` as the band edge — a
first-order simplification; a real RF front-end oversamples, ≳4·f_Tx.)

Between that firehose and the wearable stand two hard bottlenecks:

| bottleneck | limit | cross it and... |
|---|---|---|
| **ADC bottleneck** | on-chip ADC ~ **5 Msps** | you need an external converter + FPGA (bigger, hungrier) |
| **link bottleneck** | usable BLE ~ **300 kb/s** | the stream will not fit the radio — the straw |

The analog **Echo** board (envelope) already cut bandwidth ~4× in Exercise 1, dropping fs to
5 Msps — just under the ADC bottleneck. But does it clear the **link** bottleneck? Compute it and see.
"""))

CELLS.append(code("""\
# TODO (b) — the data rate decides whether a wireless wearable can even exist.
#   data_rate = N · bits · PRF · nRx       [bits/s]
device = System()
acq = Acq(f_Tx=10e6, bits=12, nRx=8, PRF=100, D=0.03, mode="RF")
d = device.run(acq)       # d.N is computed by the model; acq.bits/PRF/nRx are knobs
data_rate = ...              # <-- replace ... using d.N, acq.bits, acq.PRF, acq.nRx

# ---- self-check (do not edit) -------------------------------------------
assert data_rate is not ..., "fill in data_rate above"
assert abs(data_rate - d.data_rate) < 1, "should match the model (Core.data_rate)"
bottleneck = device.radio.throughput_max_bps
print(f"RF, 8 channels, 100 Hz  ->  {data_rate/1e6:.2f} Mb/s")
print(f"BLE bottleneck {bottleneck/1e3:.0f} kb/s   ->  {data_rate/bottleneck:.0f}x OVER it" if data_rate > bottleneck else "fits")
print("OK - data-rate check passed")
"""))

CELLS.append(code("""\
# The naive choice (RF) vs the analog trick (BWR envelope) — same 10 MHz, 8 ch, 100 Hz.
device = System()
print(f"{'mode':9s}{'fs':>9s}{'data rate':>12s}     ADC       BLE")
for mode in ("RF", "BWR"):
    d = device.run(Acq(10e6, 12, 8, 100, 0.03, mode))
    print(f"{mode:9s}{d.fs/1e6:7.1f}M {d.data_rate/1e6:9.2f} Mb/s   "
          f"{'fits ' if d.fits_onchip else ' EXT ':>5s}     "
          f"{'fits' if d.fits_ble else 'OVER'}")
print()
print("The Echo board fixed the ADC bottleneck (envelope -> 5 Msps). The radio is still flooded.")
"""))

CELLS.append(md("""\
### Stage 1 — beat the pipe (locked in RF)

You're locked in **RF**: every sample ships raw. Your job — get the data rate under the
~300 kb/s BLE pipe using the knobs below. Each sharpens the image a different way, and
each costs:

| knob | turn it up for | like… | what it costs |
|---|---|---|---|
| **nRx** — receive channels | spatial coverage, lateral sharpness | more microphones at a concert | each channel is another stream to power *and* send — linear in both |
| **f_Tx** — centre frequency | finer axial detail (smaller things) | a higher-megapixel camera | double the frequency → double the samples → a bigger file every pulse |
| **PRF** — pulses per second | faster motion, Doppler | filming at 1000 fps vs 25 | more frames = more data, less idle time for the radio and chip to sleep |

There's also a **battery** slider. Try everything — including making the battery bigger.
"""))

CELLS.append(code("""\
# STAGE 1 — you are LOCKED in RF mode. Try to get the data rate under the BLE bottleneck
# by changing anything you like... including the battery. (Drag the sliders.)
from ipywidgets import interact, FloatSlider, IntSlider, Dropdown
device = System()
BOTTLENECK = device.radio.throughput_max_bps / 1e6   # BLE bottleneck [Mb/s], read from the model

def stage1(f_Tx_MHz=10.0, nRx=8, PRF=100, battery_days=1):
    d = device.run(Acq(f_Tx_MHz * 1e6, 12, nRx, PRF, 0.03, "RF"))   # mode LOCKED = RF
    dr = d.data_rate / 1e6
    b = device.battery.size(d.P_avg, days=battery_days)
    plt.figure(figsize=(7, 1.6))
    plt.barh([0], [dr], color=("seagreen" if d.fits_ble else "crimson"))
    plt.axvline(BOTTLENECK, color="k", ls="--"); plt.text(BOTTLENECK * 1.05, 0, f"BLE {BOTTLENECK*1e3:.0f} kb/s", va="center")
    plt.yticks([]); plt.xlabel("data rate [Mb/s]"); plt.xlim(0, max(BOTTLENECK * 2, dr * 1.1))
    plt.title(f"{dr:.2f} Mb/s  ->  {'FITS' if d.fits_ble else 'OVER'}      "
              f"battery {battery_days} d = {b['vol_cm3']:.2f} cm3")
    plt.tight_layout(); plt.show()

interact(stage1,
         f_Tx_MHz=FloatSlider(value=10, min=1, max=15, step=1, description="f_Tx [MHz]"),
         nRx=Dropdown(options=[1, 8, 16, 32], value=8, description="nRx"),
         PRF=IntSlider(value=100, min=1, max=1000, step=1, description="PRF [Hz]"),
         battery_days=IntSlider(value=1, min=1, max=7, description="battery [d]"));
"""))

CELLS.append(md("""\
### A bigger tank won't widen the pipe

The battery slider did nothing to the BLE verdict — by design. A battery is a **tank**:
it stores energy (run-*hours*). The link is a **pipe**: its width is the radio's
throughput, fixed by the radio, not by your energy store. A bigger tank never widens the
pipe.

They touch only through **power**: pushing more bits/s costs radio power (~19 nJ/bit in
the model), draining the tank faster — so data and battery are coupled through *power*,
not the ceiling. (A wider pipe exists — **Wi-Fi**, tens of Mb/s — but it burns 1–2 orders
of magnitude more power than BLE, far past a coin cell: you'd trade the link bottleneck
for a power one.)

So the three knobs above buy link-fit only by giving up image quality. **Exercise 3** adds
the lever that isn't on that list — how you **represent** the echo before it reaches the
radio.
"""))

# ── EXERCISE 3 · SYSTEM — scaling receive channels ──────────────────────
CELLS.append(md("""\
## Exercise 3 · The system — *scaling receive channels*

You proved it: in RF the radio floods the link no matter the battery. Now unlock the
one knob we held back — how the echo is **represented** before it reaches the radio.
Think of it as how you mail a statue:

- **RF** — crate up the whole statue: every sample, the full waveform.
- **BWR** — ship a lightweight cast: the analog envelope, ~4× lighter, shape kept but fine detail (phase) lost.
- **features** — post its dimensions on a card: a handful of numbers per A-line, no waveform at all.

```
per A-line, what you put on the radio:
  RF        ████████████████   the whole statue
  BWR       ████               a light cast — ~4× less
  features  ▌                  dimensions on a card
```

Watch what each does to the **power breakdown**, the **link bottleneck**, and the **battery**
you would have to wear.
"""))

CELLS.append(code("""\
# STAGE 2 — the mode is now UNLOCKED. Flip it to 'features' and watch the radio.
from ipywidgets import interact, FloatSlider, IntSlider, Dropdown
device = System()
CR2032_CM3 = 3.3        # reference coin-cell volume [cm3]

def stage2(f_Tx_MHz=10.0, nRx=8, PRF=100, mode="RF", days=1):
    d = device.run(Acq(f_Tx_MHz * 1e6, 12, nRx, PRF, 0.03, mode))
    P = d.power; b = device.battery.size(d.P_avg, days=days)
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    ax[0].bar(list(P.keys()), [P[k] * 1e3 for k in P],
              color=["#888", "#4a90d9", "#7ab648", "#d9534f"])
    ax[0].set_yscale("log")
    ax[0].set_ylabel("power [mW]"); ax[0].set_title(f"P_avg = {d.P_avg*1e3:.1f} mW")
    ax[1].bar(["this design", "CR2032"], [b["vol_cm3"], CR2032_CM3],
              color=["#d9534f", "#888"])
    ax[1].set_yscale("log")
    ax[1].set_ylabel("volume [cm3]")
    ax[1].set_title(f"{b['vol_cm3']:.2f} cm3  =  {b['n_cr2032']:.1f} CR2032  ({days} d)")
    ble = "FITS" if d.fits_ble else f"{d.data_rate/1e6:.2f} Mb/s OVER"
    adc = "on-chip" if d.fits_onchip else "external/FPGA"
    fig.suptitle(f"mode = {mode}   |   BLE {ble}   |   ADC {adc}   |   "
                 f"FoM {d.fom:.2f} mW/MHz", fontsize=11)
    plt.tight_layout(); plt.show()

interact(stage2,
         f_Tx_MHz=FloatSlider(value=10, min=1, max=15, step=1, description="f_Tx [MHz]"),
         nRx=Dropdown(options=[1, 8, 16, 32], value=8, description="nRx"),
         PRF=IntSlider(value=100, min=1, max=1000, step=1, description="PRF [Hz]"),
         mode=Dropdown(options=["RF", "BWR", "features"], value="RF", description="mode"),
         days=IntSlider(value=1, min=1, max=7, description="battery [d]"));
"""))

CELLS.append(code("""\
# TODO (c) — even the envelope (BWR) floods the radio once you add channels.
# Find the SMALLEST nRx at which BWR breaks the BLE bottleneck (10 MHz, PRF=100 Hz).
device = System()
breaking_nRx = None
for nRx in [1, 2, 4, 8, 16, 32]:
    d = device.run(Acq(10e6, 12, nRx, 100, 0.03, "BWR"))
    if ...:                      # <-- replace ... with the condition "no longer fits BLE"
        breaking_nRx = nRx
        break

# ---- self-check (do not edit) -------------------------------------------
assert breaking_nRx is not None, "fill in the condition above"
print(f"BWR breaks the BLE bottleneck at nRx = {breaking_nRx} channels")
print("Your escape from there? -> features mode: ship numbers, not the waveform.")
"""))

CELLS.append(code("""\
# INVERT THE CHAIN — the design exercise.
# Given a SMALL-WEARABLE budget, which architectures actually survive every constraint:
# fits BLE  AND  fits on-chip ADC  AND  nRx <= 8 (hardware)  AND  battery <= budget.
BUDGET_CM3 = 3.0       # a coin-cell-sized wearable budget
DAYS = 1
device = System(); survivors = []
for mode in ("RF", "BWR", "features"):
    for f_MHz in (2, 5, 10, 15):
        for nRx in (1, 8, 16, 32):
            for PRF in (25, 100, 500, 1000):
                d = device.run(Acq(f_MHz * 1e6, 12, nRx, PRF, 0.03, mode))
                b = device.battery.size(d.P_avg, days=DAYS)
                if (d.fits_ble and d.fits_onchip and d.within_channels
                        and b["vol_cm3"] <= BUDGET_CM3):
                    survivors.append((mode, f_MHz, nRx, PRF,
                                      d.axial_res_mm, b["vol_cm3"]))

print(f"{len(survivors)} architectures fit a {BUDGET_CM3} cm3 wearable budget for {DAYS} day\\n")
print(f"{'mode':9s}{'f_Tx':>6s}{'nRx':>5s}{'PRF':>7s}{'res[mm]':>9s}{'vol[cm3]':>10s}")
for s in sorted(survivors, key=lambda s: (s[4], s[5]))[:15]:
    print(f"{s[0]:9s}{s[1]:>5d}M{s[2]:>5d}{s[3]:>7d}{s[4]:>9.2f}{s[5]:>10.2f}")
print("\\nWhich knob did you have to give up? (Hint: look at how few RF rows survive.)")
"""))

CELLS.append(md("""\
## Recap — and what is still unsolved

We went both ways — forward as a cost, backward as a design:
```
forward (the cost):    resolution → frequency → Nyquist → data → power → battery → wearable
inverse (the design):  wearable → battery → power → data → ... → architecture
```

**Three escape routes from the link bottleneck**

| route | what it buys | what it costs |
|---|---|---|
| lower `f_Tx` | fewer samples | axial resolution |
| analog **BWR** / envelope | ~4× fewer samples, resolution kept | phase (no Doppler) — the ModulUS path |
| on-device **features** | radio collapses | MCU compute budget (edge-AI / PULP) |

**Still open (the next few years):** multi-channel *low-power* acquisition;
phase-preserving BWR (I/Q) for Doppler and displacement; ASIC integration;
transducer + edge-AI co-design. *This is where your research comes in.*
"""))

CELLS.append(md("""\
## References

1. C. Leitner, M. Giordano, M. Tanner, F. Villani, M. Magno and L. Benini,
   "ModulUS: A Sandbox for High-Resolution Wearable Ultrasound Development,"
   *2025 IEEE International Ultrasonics Symposium (IUS)*, Utrecht, Netherlands,
   2025, pp. 1-4, doi: [10.1109/IUS62464.2025.11201551](https://doi.org/10.1109/IUS62464.2025.11201551).
"""))

# ── Emit two notebooks from the same cells: student (blanks) + solutions ──
import copy

# map each TODO blank line -> its filled solution
SOLUTIONS = {
    "raw_mean = ...     # <-- replace ... using f_rf and P_rf":
        "raw_mean = float(np.sum(f_rf * P_rf) / np.sum(P_rf))",
    "env_mean = ...     # <-- replace ... using f_env and P_env":
        "env_mean = float(np.sum(f_env * P_env) / np.sum(P_env))",
    "data_rate = ...              # <-- replace ... using d.N, acq.bits, acq.PRF, acq.nRx":
        "data_rate = d.N * acq.bits * acq.PRF * acq.nRx",
    "    if ...:                      # <-- replace ... with the condition \"no longer fits BLE\"":
        "    if not d.fits_ble:",
}

def write_nb(cells, path):
    n = nbf.v4.new_notebook(); n.cells = cells
    nbf.write(n, str(path))
    print(f"wrote {path}  ({len(cells)} cells)")

# student version (blanks)
write_nb(CELLS, REPO_ROOT / NB_NAME)

# solutions version (filled; TODO -> SOLUTION)
sol_cells = copy.deepcopy(CELLS)
for c in sol_cells:
    if c.cell_type == "markdown":
        c.source = c.source.replace(
            f"/blob/main/{NB_NAME}", f"/blob/main/{NB_TEACHER}")
        continue
    if c.cell_type != "code":
        continue
    for blank, sol in SOLUTIONS.items():
        c.source = c.source.replace(blank, sol)
    c.source = c.source.replace("# TODO (", "# SOLUTION (")
write_nb(sol_cells, REPO_ROOT / NB_TEACHER)
