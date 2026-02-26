# run_prereg_cmb_birefringence_v1_DROPIN_SELFCONTAINED.ps1
# Self-contained runner: writes prereg_cmb_birefringence_v1_DROPIN.py next to this PS1 and runs it.
# Uses backtick (`) continuation. ASCII-safe.

param(
  [double]$BetaCalDeg   = 0.34,
  [double]$SigmaCalDeg  = 0.09,
  [double]$BetaHoldDeg  = 0.215,
  [double]$SigmaHoldDeg = 0.074,
  [double]$KSigma       = 2.0,
  [string]$LabelCal     = "WMAP+Planck",
  [string]$LabelHold    = "ACT_DR6",
  [string]$OutCsv       = "out\cmb_birefringence_prereg_v1.csv",
  [string]$Python       = "py"
)

$ErrorActionPreference="Stop"
$Here=$PSScriptRoot; if([string]::IsNullOrWhiteSpace($Here)){$Here=(Get-Location).Path}
$ScriptPath = Join-Path $Here "prereg_cmb_birefringence_v1_DROPIN.py"

$PySource=@'
#!/usr/bin/env python3
# prereg_cmb_birefringence_v1_DROPIN.py
# No-fit prereg check: lock C_beta from calibration and test on holdout.

import argparse, csv, math, os

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beta_cal_deg", type=float, required=True)
    ap.add_argument("--sigma_cal_deg", type=float, required=True)
    ap.add_argument("--beta_hold_deg", type=float, required=True)
    ap.add_argument("--sigma_hold_deg", type=float, required=True)
    ap.add_argument("--k_sigma", type=float, default=2.0)
    ap.add_argument("--out_csv", type=str, default="out/cmb_birefringence_prereg_v1.csv")
    ap.add_argument("--label_cal", type=str, default="WMAP+Planck")
    ap.add_argument("--label_hold", type=str, default="ACT")
    args = ap.parse_args()

    # Lock (Option A): I(z*) = 1
    C_beta = float(args.beta_cal_deg)

    # Compare with combined uncertainty
    sig = math.sqrt(float(args.sigma_cal_deg)**2 + float(args.sigma_hold_deg)**2)
    diff = float(args.beta_hold_deg) - C_beta
    z = diff / sig if sig > 0 else float("inf")
    thr = float(args.k_sigma)

    verdict = "PASS" if abs(z) <= thr else "FAIL"

    sign_ok = (C_beta == 0.0) or (float(args.beta_hold_deg) == 0.0) or (math.copysign(1.0, C_beta) == math.copysign(1.0, float(args.beta_hold_deg)))
    sign_verdict = "OK" if sign_ok else "MISMATCH"

    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    row = {
        "cal_label": args.label_cal,
        "hold_label": args.label_hold,
        "beta_cal_deg": args.beta_cal_deg,
        "sigma_cal_deg": args.sigma_cal_deg,
        "C_beta_locked_deg": C_beta,
        "beta_hold_deg": args.beta_hold_deg,
        "sigma_hold_deg": args.sigma_hold_deg,
        "diff_deg": diff,
        "sigma_comb_deg": sig,
        "z_score": z,
        "k_sigma": thr,
        "verdict": verdict,
        "sign_verdict": sign_verdict,
    }
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        w.writeheader()
        w.writerow(row)

    print("=== CMB BIREFRINGENCE PREREG (NO FIT) ===")
    print(f"cal   : {args.label_cal}  beta={args.beta_cal_deg} +/- {args.sigma_cal_deg} deg")
    print(f"hold  : {args.label_hold} beta={args.beta_hold_deg} +/- {args.sigma_hold_deg} deg")
    print(f"LOCK  : C_beta = beta_cal = {C_beta} deg")
    print(f"diff  : hold - C_beta = {diff} deg")
    print(f"sigma : sqrt(sig_cal^2 + sig_hold^2) = {sig} deg")
    print(f"z     : {z}")
    print(f"RULE  : PASS if |z| <= {thr}")
    print(f"VERDICT={verdict}  SIGN={sign_verdict}")
    print(f"OUT_CSV={args.out_csv}")

if __name__ == "__main__":
    main()

'@

Set-Content -LiteralPath $ScriptPath -Value $PySource -Encoding UTF8

$OutDir = Split-Path -Parent $OutCsv
if([string]::IsNullOrWhiteSpace($OutDir)){$OutDir="."}
mkdir $OutDir -ErrorAction SilentlyContinue | Out-Null

& $Python -3 `
  -X utf8 `
  $ScriptPath `
  --beta_cal_deg $BetaCalDeg `
  --sigma_cal_deg $SigmaCalDeg `
  --beta_hold_deg $BetaHoldDeg `
  --sigma_hold_deg $SigmaHoldDeg `
  --k_sigma $KSigma `
  --label_cal $LabelCal `
  --label_hold $LabelHold `
  --out_csv $OutCsv
