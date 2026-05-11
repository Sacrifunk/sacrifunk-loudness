# Loudness Report — Bounces

_Generated 2026-05-11T15:07:13Z by `sacrifunk-loudness` v0.1.0_

## Targets

- Integrated loudness: **-14.0 LUFS** ±0.5
- True peak: **≤ -1.0 dBTP**
- Crest factor: **14–18 dB**

## Summary

- **Total files:** 3
- **OK (analyzed):** 3
- **Errors:** 0
- **Mastered OK (within all targets):** 0
- **LUFS off target:** 2
- **True-peak over limit:** 1
- **Crest out of range:** 2

## Per-file results

| File | LUFS | TP (dBTP) | Sample peak | Crest | Duration | Verdict |
|------|-----:|----------:|------------:|------:|---------:|---------|
| `STEP_5_4_smoke_v4_-52.1L_-31.9P_260506-1350.wav` | -52.08 | -31.93 | -31.98 dBFS | 30.1 dB | 2:48 | :warning: LUFS off | crest out of range |
| `STEP_5_4_smoke_v5_-52.1L_-31.9P_260506-1354.wav` | -52.08 | -31.93 | -31.98 dBFS | 30.1 dB | 2:48 | :warning: LUFS off | crest out of range |
| `STEP_5_4_test_-13.7L_-1.0P_260506-1406.wav` | -13.70 | -0.98 | -1.01 dBFS | 15.6 dB | 5:36 | :warning: TP over |

## Detail

### `STEP_5_4_smoke_v4_-52.1L_-31.9P_260506-1350.wav`
- **Path:** `Bounces/STEP_5_4_smoke_v4_-52.1L_-31.9P_260506-1350.wav`
- **Size:** 44,511,496 bytes
- **Sample rate:** 44,100 Hz
- **Channels:** 2
- **Duration:** 2:48 (168.00 s)
- **Integrated loudness:** -52.08 LUFS (target -14.0 ±0.5 → **OFF**)
- **True peak:** -31.93 dBTP (limit -1.0 → OK)
- **Sample peak:** -31.98 dBFS
- **Crest factor:** 30.1 dB (range 14–18 → **OUT**)
- **Verdict:** :warning: LUFS off | crest out of range

### `STEP_5_4_smoke_v5_-52.1L_-31.9P_260506-1354.wav`
- **Path:** `Bounces/STEP_5_4_smoke_v5_-52.1L_-31.9P_260506-1354.wav`
- **Size:** 44,511,496 bytes
- **Sample rate:** 44,100 Hz
- **Channels:** 2
- **Duration:** 2:48 (168.00 s)
- **Integrated loudness:** -52.08 LUFS (target -14.0 ±0.5 → **OFF**)
- **True peak:** -31.93 dBTP (limit -1.0 → OK)
- **Sample peak:** -31.98 dBFS
- **Crest factor:** 30.1 dB (range 14–18 → **OUT**)
- **Verdict:** :warning: LUFS off | crest out of range

### `STEP_5_4_test_-13.7L_-1.0P_260506-1406.wav`
- **Path:** `Bounces/STEP_5_4_test_-13.7L_-1.0P_260506-1406.wav`
- **Size:** 59,470,082 bytes
- **Sample rate:** 44,100 Hz
- **Channels:** 2
- **Duration:** 5:36 (336.47 s)
- **Integrated loudness:** -13.70 LUFS (target -14.0 ±0.5 → OK)
- **True peak:** -0.98 dBTP (limit -1.0 → **OVER**)
- **Sample peak:** -1.01 dBFS
- **Crest factor:** 15.6 dB (range 14–18 → OK)
- **Verdict:** :warning: TP over
