# PASS run commands

- timestamp_utc: 2026-03-03T00:17:17.0958708Z
- run_dir: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\\pass_runs\20260303_031717


- pytest_integration_artifacts_mastereq_tests
  - cmd: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\.venv\\Scripts\\python.exe -m pytest -q integration_artifacts/mastereq/tests

  - exit_code: 0

- pytest_mastereq_tests
  - cmd: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\.venv\\Scripts\\python.exe -m pytest -q mastereq/tests

  - exit_code: 0

- dm_paper_run
  - cmd: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\.venv\\Scripts\\python.exe run_dm_paper_run.py --out_dir out\\dm_paper --kfold 2 --seed 2026

  - exit_code: 0

- em_paper_run
  - cmd: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\.venv\\Scripts\\python.exe run_em_paper_run.py --out_dir out\\em_paper

  - exit_code: 0

- strong_c5a_paper_run
  - cmd: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\.venv\\Scripts\\python.exe run_strong_c5a_paper_run.py --out_dir out\\strong_c5a

  - exit_code: 0

