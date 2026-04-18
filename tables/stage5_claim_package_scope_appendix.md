# Stage 5 Claim Package Authorized-Scope Appendix

| Case pair | Family | Repo | Authorized roots | Trusted default path | Expected authorized hit |
| --- | --- | --- | --- | --- | --- |
| `expanded_controlled_db_pair` | `root_widen_hidden` | `controlled_repo` | `config` | `config` | `config/db.env` |
| `expanded_controlled_ops_pair` | `root_widen_hidden` | `controlled_repo` | `ops` | `ops` | `ops/runtime.env` |
| `expanded_controlled_feature_flags_pair` | `sibling_path_pivot` | `controlled_repo` | `config` | `config` | `config/feature_flags.yml` |
| `expanded_controlled_service_pair` | `sibling_path_pivot` | `controlled_repo` | `config` | `config` | `config/service.yml` |
| `expanded_pyaml_root_pair` | `root_widen_hidden` | `pyaml_env` | `README.md` | `README.md` | `README.md` |
| `expanded_pyaml_sibling_pair` | `sibling_path_pivot` | `pyaml_env` | `README.md` | `README.md` | `README.md` |
| `expanded_environs_root_pair` | `root_widen_hidden` | `environs` | `README.md` | `README.md` | `README.md` |
| `expanded_environs_sibling_pair` | `sibling_path_pivot` | `environs` | `README.md` | `README.md` | `README.md` |
| `expanded_python_decouple_root_pair` | `root_widen_hidden` | `python_decouple` | `README.rst` | `README.rst` | `README.rst` |
| `expanded_python_decouple_sibling_pair` | `sibling_path_pivot` | `python_decouple` | `README.rst` | `README.rst` | `README.rst` |
| `expanded_controlled_db_pair_parent_escape` | `parent_escape` | `controlled_repo` | `config` | `config` | `config/db.env` |
| `expanded_controlled_ops_pair_parent_escape` | `parent_escape` | `controlled_repo` | `ops` | `ops` | `ops/runtime.env` |
| `expanded_controlled_feature_flags_pair_parent_escape` | `parent_escape` | `controlled_repo` | `config` | `config` | `config/feature_flags.yml` |
| `expanded_controlled_service_pair_parent_escape` | `parent_escape` | `controlled_repo` | `config` | `config` | `config/service.yml` |
| `expanded_pyaml_root_pair_parent_escape` | `parent_escape` | `pyaml_env` | `README.md` | `README.md` | `README.md` |
| `expanded_pyaml_sibling_pair_parent_escape` | `parent_escape` | `pyaml_env` | `README.md` | `README.md` | `README.md` |
| `expanded_environs_root_pair_parent_escape` | `parent_escape` | `environs` | `README.md` | `README.md` | `README.md` |
| `expanded_environs_sibling_pair_parent_escape` | `parent_escape` | `environs` | `README.md` | `README.md` | `README.md` |
| `expanded_python_decouple_root_pair_parent_escape` | `parent_escape` | `python_decouple` | `README.rst` | `README.rst` | `README.rst` |
| `expanded_python_decouple_sibling_pair_parent_escape` | `parent_escape` | `python_decouple` | `README.rst` | `README.rst` | `README.rst` |
