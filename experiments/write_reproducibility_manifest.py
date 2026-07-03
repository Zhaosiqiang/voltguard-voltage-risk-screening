"""Write a reproducibility manifest for the VoltGuard submission package."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"


RESULT_FILES = [
    "scenario_generation_meta.json",
    "scenario_summary.csv",
    "dataset_split_summary.csv",
    "bus_voltage_labels.csv",
    "evaluation_summary.json",
    "evaluation_metrics_all_runs.csv",
    "model_voltage_screening_metrics.csv",
    "multi_seed_summary.csv",
    "paired_seed_delta_summary.csv",
    "paired_seed_delta_summary.json",
    "paired_seed_deltas_raw.csv",
    "feature_residual_ablation.csv",
    "feature_residual_ablation_raw.csv",
    "feature_residual_ablation_summary.json",
    "ev_conditioning_ablation.csv",
    "ev_conditioning_summary.json",
    "ev_conditioning_family_counts.csv",
    "ev_conditioning_sample_size_outlook.csv",
    "ev_conditioning_sample_size_outlook.md",
    "scenario_level_metrics.csv",
    "conformal_ablation_metrics.csv",
    "calibration_budget_sensitivity_metrics.csv",
    "calibration_budget_sensitivity_raw.csv",
    "calibration_budget_sensitivity_summary.json",
    "asymmetric_conformal_metrics.csv",
    "asymmetric_conformal_family_radii.csv",
    "asymmetric_conformal_summary.json",
    "per_family_conformal_metrics.csv",
    "family_recalibration_audit.csv",
    "family_recalibration_summary.json",
    "forecast_noise_robustness_metrics.csv",
    "forecast_noise_robustness_raw.csv",
    "forecast_noise_robustness_summary.json",
    "pv_shift_recalibration_metrics.csv",
    "pv_shift_recalibration_raw.csv",
    "pv_shift_recalibration_target_splits.csv",
    "pv_shift_recalibration_summary.json",
    "pv_shift_recalibration_energy_value_metrics.csv",
    "pv_shift_recalibration_energy_value_raw.csv",
    "pv_shift_recalibration_energy_value_summary.json",
    "risk_stratified_calibration_bus.csv",
    "risk_stratified_calibration_scenario.csv",
    "risk_stratified_calibration_summary.json",
    "conformal_sensitivity_metrics.csv",
    "operating_value_metrics.csv",
    "energy_management_value_metrics.csv",
    "energy_management_value_multiseed_metrics.csv",
    "energy_management_value_multiseed_raw.csv",
    "energy_management_value_multiseed_summary.json",
    "energy_management_frontier_metrics.csv",
    "energy_management_frontier_metrics.md",
    "energy_management_frontier_summary.json",
    "shift_energy_management_value_metrics.csv",
    "shift_energy_management_value_raw.csv",
    "shift_energy_management_value_summary.json",
    "topology_transfer_bidirectional_metrics.csv",
    "topology_transfer_bidirectional_raw.csv",
    "topology_transfer_bidirectional_summary.json",
    "screened_safe_release_metrics.csv",
    "screened_safe_release_summary.json",
    "screened_safe_release_multiseed_metrics.csv",
    "screened_safe_release_multiseed_raw.csv",
    "screened_safe_release_multiseed_summary.json",
    "screening_budget_metrics.csv",
    "screening_budget_summary.json",
    "screening_budget_multiseed_metrics.csv",
    "screening_budget_multiseed_raw.csv",
    "screening_budget_multiseed_summary.json",
    "statistical_evidence_metrics.csv",
    "statistical_evidence_raw.csv",
    "statistical_evidence_summary.json",
    "runtime_operational_benchmark.csv",
    "runtime_operational_summary.json",
    "runtime_ac_grid_raw.csv",
    "control_grid_search_candidate_actions.csv",
    "candidate_action_screening_metrics.csv",
    "candidate_action_screening_scores.csv",
    "candidate_action_screening_raw_predictions.csv",
    "candidate_action_screening_summary.json",
    "candidate_action_screening_multiseed_metrics.csv",
    "candidate_action_screening_multiseed_raw.csv",
    "candidate_action_screening_multiseed_ac_candidates.csv",
    "candidate_action_screening_multiseed_scores.csv",
    "candidate_action_screening_multiseed_raw_predictions.csv",
    "candidate_action_screening_multiseed_summary.json",
    "action_cost_tradeoff_metrics.csv",
    "action_cost_tradeoff_summary.json",
    "action_cost_tradeoff_multiseed_metrics.csv",
    "action_cost_tradeoff_multiseed_raw.csv",
    "action_cost_tradeoff_multiseed_summary.json",
    "physics_consistency_audit.csv",
    "physics_consistency_audit_raw.csv",
    "physics_consistency_summary.json",
    "high_pv_hosting_stress_raw.csv",
    "high_pv_hosting_stress_by_feeder.csv",
    "high_pv_hosting_stress_summary.json",
    "high_pv_hosting_frontier_raw.csv",
    "high_pv_hosting_frontier_metrics.csv",
    "high_pv_hosting_frontier_summary.json",
    "scenario_risk_ranking_metrics.csv",
    "scenario_risk_ranking_summary.json",
    "scenario_risk_ranking_raw.csv",
    "raw_predictions_random_seed7.csv",
    "conformal_scores_random_seed7.csv",
    "runtime_metrics.csv",
    "control_grid_search_summary.json",
    "control_grid_search_selected_actions.csv",
]

SOURCE_FILES = [
    "experiments/experiment_config.json",
    "experiments/generate_scenarios.py",
    "experiments/evaluate_models.py",
    "experiments/evaluate_control_benchmark.py",
    "experiments/evaluate_sensitivity.py",
    "experiments/evaluate_asymmetric_conformal.py",
    "experiments/evaluate_calibration_budget_sensitivity.py",
    "experiments/evaluate_family_recalibration.py",
    "experiments/evaluate_paired_seed_deltas.py",
    "experiments/evaluate_feature_ablation.py",
    "experiments/evaluate_ev_conditioning.py",
    "experiments/evaluate_energy_management_value.py",
    "experiments/evaluate_energy_management_value_multiseed.py",
    "experiments/evaluate_energy_management_frontier.py",
    "experiments/evaluate_shift_energy_management_value.py",
    "experiments/evaluate_topology_transfer_bidirectional.py",
    "experiments/evaluate_screened_safe_release.py",
    "experiments/evaluate_screened_safe_release_multiseed.py",
    "experiments/evaluate_forecast_noise_robustness.py",
    "experiments/evaluate_risk_ranking.py",
    "experiments/evaluate_pv_shift_recalibration.py",
    "experiments/evaluate_pv_shift_recalibration_energy_value.py",
    "experiments/evaluate_risk_stratified_calibration.py",
    "experiments/evaluate_screening_budget.py",
    "experiments/evaluate_screening_budget_multiseed.py",
    "experiments/evaluate_statistical_evidence.py",
    "experiments/evaluate_candidate_action_screening.py",
    "experiments/evaluate_candidate_action_screening_multiseed.py",
    "experiments/evaluate_action_cost_tradeoff.py",
    "experiments/evaluate_action_cost_tradeoff_multiseed.py",
    "experiments/evaluate_runtime_benchmark.py",
    "experiments/evaluate_physics_consistency.py",
    "experiments/evaluate_high_pv_hosting_stress.py",
    "experiments/evaluate_high_pv_hosting_frontier.py",
    "experiments/generate_submission_figures.py",
    "experiments/validate_project.py",
    "experiments/ieee69_feeder.py",
    "requirements.txt",
]

SUBMISSION_FILES = [
    "manuscript_draft.md",
    "manuscript_ecm_engineering.md",
    "manuscript_oajpe_minimal.md",
    "submission_variant_strategy.md",
    "submission_manuscript_ecmx.md",
    "submission_manuscript_ecmx.tex",
    "submission_build/submission_manuscript_ecmx.pdf",
    "submission_manuscript_ecm.md",
    "submission_manuscript_ecm.tex",
    "submission_build/submission_manuscript_ecm.pdf",
    "submission_manuscript_oajpe.md",
    "submission_manuscript_oajpe.tex",
    "submission_build/submission_manuscript_oajpe.pdf",
    "submission_compile_report.md",
    "submission_references.md",
    "references.bib",
    "ecmx_highlights.txt",
    "ecm_highlights.txt",
    "ecmx_cover_letter.md",
    "ecmx_submission_readiness_checklist.md",
    "ecmx_upload_input_packet.md",
    "oajpe_upload_input_packet.md",
    "journal_format_audit.md",
    "claim_evidence_matrix.md",
    "completion_audit.md",
    "submission_strategy.md",
    "venue_source_audit.md",
    "high_impact_venue_matrix.md",
    "author_declaration_gate.md",
]

FIGURE_FILES = [
    str(path.relative_to(ROOT))
    for path in sorted((ROOT / "figures").glob("*"))
    if path.suffix.lower() in {".svg", ".pdf", ".json"}
] + [
    str(path.relative_to(ROOT))
    for path in sorted((ROOT / "figures" / "assets").glob("*"))
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
]


def file_record(path: Path) -> dict:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def records(paths: list[str], base: Path = ROOT) -> list[dict]:
    out = []
    for rel in paths:
        path = base / rel
        if path.exists():
            out.append(file_record(path))
    return out


def main() -> int:
    config = json.loads((ROOT / "experiments" / "experiment_config.json").read_text(encoding="utf-8"))
    evaluation_summary = json.loads((RESULTS / "evaluation_summary.json").read_text(encoding="utf-8"))
    manifest = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target_route": "Energy Conversion and Management: X",
        "claim_boundary": "VoltGuard is a calibrated screening layer, not an AC feasibility certificate or OPF/MPC replacement.",
        "configuration": config,
        "evaluation_summary": evaluation_summary,
        "validation_summary_note": "Run validate_project.py after manifest generation; project_validation_summary.json is not checksummed because the validator rewrites it.",
        "reproduction_commands": [
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/generate_scenarios.py --feeders 33 69 118 --scenarios 300 --seed 42",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_models.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_control_benchmark.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_sensitivity.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_asymmetric_conformal.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_calibration_budget_sensitivity.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_family_recalibration.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_paired_seed_deltas.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_feature_ablation.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_ev_conditioning.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_energy_management_value.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_energy_management_value_multiseed.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_energy_management_frontier.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_shift_energy_management_value.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_topology_transfer_bidirectional.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_screened_safe_release.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_screened_safe_release_multiseed.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_forecast_noise_robustness.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_risk_ranking.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_pv_shift_recalibration.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_pv_shift_recalibration_energy_value.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_risk_stratified_calibration.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_screening_budget.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_screening_budget_multiseed.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_statistical_evidence.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_candidate_action_screening.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_candidate_action_screening_multiseed.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_action_cost_tradeoff.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_action_cost_tradeoff_multiseed.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_runtime_benchmark.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_physics_consistency.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_high_pv_hosting_stress.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_high_pv_hosting_frontier.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/write_submission_manuscript.py",
            "VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/validate_project.py",
        ],
        "source_files": records(SOURCE_FILES),
        "result_files": records(RESULT_FILES, RESULTS),
        "submission_files": records(SUBMISSION_FILES + FIGURE_FILES),
    }
    out_json = RESULTS / "reproducibility_manifest.json"
    out_json.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = [
        "# Reproducibility Manifest",
        "",
        f"Generated UTC: {manifest['generated_utc']}",
        "",
        f"Target route: {manifest['target_route']}",
        "",
        "Validation: run `VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/validate_project.py` after manifest generation.",
        "",
        "## Reproduction Commands",
        "",
    ]
    for command in manifest["reproduction_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Artifact Counts", ""])
    lines.append(f"- Source files: {len(manifest['source_files'])}")
    lines.append(f"- Result files: {len(manifest['result_files'])}")
    lines.append(f"- Submission files: {len(manifest['submission_files'])}")
    lines.extend(["", "## Key Result Artifacts", ""])
    for record in manifest["result_files"]:
        lines.append(f"- `{record['path']}` ({record['bytes']} bytes, sha256 `{record['sha256'][:16]}...`)")
    (RESULTS / "reproducibility_manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "wrote", "json": str(out_json), "result_files": len(manifest["result_files"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
