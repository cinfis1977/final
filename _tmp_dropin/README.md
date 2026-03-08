# Drop-in: DATA_RECON provider + model_params.json (BOM-less)

Files:
- `CODE/ch_model_prob_provider_v1_DATARECON.py`
- `out/nist_ch/model_params.json`

Use:
```powershell
py -3 .\CODE\nist_ch_model_scorecard_v1_DROPIN.py `
  --in_dir ".\out\nist_ch" `
  --provider ".\CODE\ch_model_prob_provider_v1_DATARECON.py" `
  --params_json ".\out\nist_ch\model_params.json" `
  --out_csv ".\out\nist_ch\MODEL_SCORECARD_DATARECON.csv" `
  --out_md  ".\out\nist_ch\MODEL_SCORECARD_DATARECON.md"
```

Note: This is NOT a model. It reconstructs probabilities from empirical outputs so J_model == J_data.
