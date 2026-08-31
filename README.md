# Anatomy of a Wearable Ultrasound System
### From Components to Signals

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ModularUS/anatomy-wearable-US-system/blob/main/wearable_us_student.ipynb)
[![Code DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21023566.svg)](https://doi.org/10.5281/zenodo.21023566)
[![Slides DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21030966.svg)](https://doi.org/10.5281/zenodo.21030966)

A wearable ultrasound system has to do the job of a cart-sized scanner from a patch on
the skin, on a battery small enough to wear. This is a guided, hands-on workshop that
takes one apart — from front-end components to the digitized echo — to show **where the
energy goes, and for what**.

Starting from one real measurement on our **ModulUS** sandbox, you walk the chain both
ways: forward as a cost, backward as a design.

```
echo → frequency → sampling → data rate → power → battery → wearable
└ Ex 1 ┘   └──── Ex 2 ────┘   └──────── Ex 3 ────────┘
```

- **Exercise 1** — read one echo as RF and as envelope; find the frequency it carries.
- **Exercise 2** — digitize it, compute the data rate, watch it slam into the on-chip ADC and wireless-link walls.
- **Exercise 3** — choose what to transmit (RF / envelope / on-device features) to fit a small wearable's power budget, then invert the chain: given the budget, which architectures survive?

## Run it

Click the **Open in Colab** badge — the first cell installs everything and clones the
repo. Nothing to set up by hand.

Locally:

```
pip install -r requirements.txt
pip install git+https://github.com/ModularUS/dasIT   # signal helpers
jupyter lab wearable_us_student.ipynb
```

## Slides

The workshop lecture deck is archived separately on Zenodo (CC BY 4.0):
**[Anatomy of a Wearable Ultrasound System](https://doi.org/10.5281/zenodo.21030966)**.

## What's inside

| file | what |
|---|---|
| `wearable_us_student.ipynb` | the guided exercises (Ex 1–3), with TODO cells |
| `wearable_us_teacher.ipynb` | the same with the TODOs solved (instructor reference) |
| `modulus.py` | the ModulUS digital twin — boards → power / data rate / feasibility |
| `config.yaml` | the system spec; every value carries its reference — edit it to model another system |
| `example_data/` | the demo echo (`modulus_demo.npz`: real RF + envelope) |
| `requirements.txt` | dependencies (all pre-installed on Colab) |

If `example_data/modulus_demo.npz` is absent, the notebook loads a clearly-labeled
synthetic echo so it still runs. The notebook imports the
[dasIT](https://github.com/ModularUS/dasIT) toolbox for the signal-domain helpers.

## License

Dual-licensed by component:

| component | license | file |
|---|---|---|
| Code (`*.py`, `config.yaml`, notebook code cells) | Apache-2.0 | [`LICENSE`](LICENSE) |
| Content (notebook text, figures, slides, demo data, teaching materials) | CC BY 4.0 | [`LICENSE-CONTENT`](LICENSE-CONTENT) |

Apache-2.0 matches the imported [dasIT](https://github.com/ModularUS/dasIT) toolbox and
carries an explicit patent grant. CC BY 4.0 lets others reuse and adapt the teaching
materials, including commercially, with attribution.

**Attribution (CC BY 4.0):** "anatomy-wearable-US-system" by Dr. Christoph Leitner and
Marco Giordano, ETH Zurich, licensed under CC BY 4.0. See [`NOTICE`](NOTICE).

## How to cite

This workshop has two citable artifacts, each archived on Zenodo with its own DOI:

| Artifact | What | DOI |
|---|---|---|
| Code / toolkit | notebooks, `modulus.py`, `config.yaml` | [10.5281/zenodo.21023566](https://doi.org/10.5281/zenodo.21023566) |
| Slides | workshop lecture deck | [10.5281/zenodo.21030966](https://doi.org/10.5281/zenodo.21030966) |

## Reference

C. Leitner, M. Giordano, M. Tanner, F. Villani, M. Magno and L. Benini, "ModulUS: A
Sandbox for High-Resolution Wearable Ultrasound Development," *2025 IEEE International
Ultrasonics Symposium (IUS)*, 2025,
doi: [10.1109/IUS62464.2025.11201551](https://doi.org/10.1109/IUS62464.2025.11201551).
