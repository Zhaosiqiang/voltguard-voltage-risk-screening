"""Validate the current VoltGuard package against the revised claim."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"


REQUIRED_FILES = [
    "README.md",
    "manuscript_draft.md",
    "manuscript_ecm_engineering.md",
    "manuscript_oajpe_minimal.md",
    "experiment_results.md",
    "figure_descriptions.md",
    "submission_strategy.md",
    "submission_variant_strategy.md",
    "submission_ancillaries.md",
    "claim_evidence_matrix.md",
    "Professional_Review_Report.md",
    "Professional_Review_Action_Matrix.md",
    "ecmx_highlights.txt",
    "ecm_highlights.txt",
    "ecmx_cover_letter.md",
    "ecmx_submission_readiness_checklist.md",
    "ecmx_upload_input_packet.md",
    "journal_format_audit.md",
    "submission_manuscript_ecmx.md",
    "submission_manuscript_ecmx.tex",
    "submission_build/submission_manuscript_ecmx.pdf",
    "submission_manuscript_oajpe.md",
    "submission_build/submission_manuscript_oajpe.pdf",
    "submission_manuscript_ecm.md",
    "submission_build/submission_manuscript_ecm.pdf",
    "submission_compile_report.md",
    "author_declaration_gate.md",
    "references.bib",
    "submission_references.md",
    "requirements.txt",
    "experiments/experiment_config.json",
    "experiments/ieee69_feeder.py",
    "experiments/generate_scenarios.py",
    "experiments/evaluate_models.py",
    "experiments/evaluate_control_benchmark.py",
    "experiments/evaluate_asymmetric_conformal.py",
    "experiments/evaluate_calibration_budget_sensitivity.py",
    "experiments/evaluate_ev_conditioning.py",
    "experiments/evaluate_energy_management_value.py",
    "experiments/evaluate_energy_management_value_multiseed.py",
    "experiments/evaluate_energy_management_frontier.py",
    "experiments/evaluate_shift_energy_management_value.py",
    "experiments/evaluate_topology_transfer_bidirectional.py",
    "experiments/evaluate_screened_safe_release.py",
    "experiments/evaluate_screened_safe_release_multiseed.py",
    "experiments/evaluate_family_recalibration.py",
    "experiments/evaluate_feature_ablation.py",
    "experiments/evaluate_forecast_noise_robustness.py",
    "experiments/evaluate_high_pv_hosting_stress.py",
    "experiments/evaluate_high_pv_hosting_frontier.py",
    "experiments/evaluate_paired_seed_deltas.py",
    "experiments/evaluate_physics_consistency.py",
    "experiments/evaluate_pv_shift_recalibration.py",
    "experiments/evaluate_pv_shift_recalibration_energy_value.py",
    "experiments/evaluate_risk_ranking.py",
    "experiments/evaluate_risk_stratified_calibration.py",
    "experiments/evaluate_runtime_benchmark.py",
    "experiments/evaluate_screening_budget.py",
    "experiments/evaluate_screening_budget_multiseed.py",
    "experiments/evaluate_statistical_evidence.py",
    "experiments/evaluate_candidate_action_screening.py",
    "experiments/evaluate_candidate_action_screening_multiseed.py",
    "experiments/evaluate_action_cost_tradeoff.py",
    "experiments/evaluate_action_cost_tradeoff_multiseed.py",
    "experiments/evaluate_oajpe_lindistflow_quantile.py",
    "experiments/evaluate_review_baselines.py",
    "experiments/evaluate_dms_prototype.py",
    "experiments/evaluate_baseline_design_rationale.py",
    "GITHUB_ZENODO_RELEASE_CHECKLIST.md",
    "CITATION.cff",
    ".zenodo.json",
    "LICENSE",
    "experiments/generate_submission_figures.py",
    "experiments/results/scenario_summary.csv",
    "experiments/results/bus_voltage_labels.csv",
    "experiments/results/dataset_split_summary.md",
    "experiments/results/model_voltage_screening_metrics.md",
    "experiments/results/multi_seed_summary.md",
    "experiments/results/paired_seed_delta_summary.csv",
    "experiments/results/paired_seed_delta_summary.md",
    "experiments/results/paired_seed_delta_summary.json",
    "experiments/results/paired_seed_deltas_raw.csv",
    "experiments/results/feature_residual_ablation.csv",
    "experiments/results/feature_residual_ablation.md",
    "experiments/results/feature_residual_ablation_raw.csv",
    "experiments/results/feature_residual_ablation_summary.json",
    "experiments/results/ev_conditioning_ablation.csv",
    "experiments/results/ev_conditioning_ablation.md",
    "experiments/results/ev_conditioning_summary.json",
    "experiments/results/ev_conditioning_family_counts.csv",
    "experiments/results/scenario_level_metrics.md",
    "experiments/results/conformal_ablation_metrics.md",
    "experiments/results/calibration_budget_sensitivity_metrics.csv",
    "experiments/results/calibration_budget_sensitivity_metrics.md",
    "experiments/results/calibration_budget_sensitivity_raw.csv",
    "experiments/results/calibration_budget_sensitivity_summary.json",
    "experiments/results/asymmetric_conformal_metrics.csv",
    "experiments/results/asymmetric_conformal_metrics.md",
    "experiments/results/asymmetric_conformal_family_radii.csv",
    "experiments/results/asymmetric_conformal_summary.json",
    "experiments/results/per_family_conformal_metrics.md",
    "experiments/results/family_recalibration_audit.csv",
    "experiments/results/family_recalibration_audit.md",
    "experiments/results/family_recalibration_summary.json",
    "experiments/results/forecast_noise_robustness_metrics.csv",
    "experiments/results/forecast_noise_robustness_metrics.md",
    "experiments/results/forecast_noise_robustness_raw.csv",
    "experiments/results/forecast_noise_robustness_summary.json",
    "experiments/results/pv_shift_recalibration_metrics.csv",
    "experiments/results/pv_shift_recalibration_metrics.md",
    "experiments/results/pv_shift_recalibration_raw.csv",
    "experiments/results/pv_shift_recalibration_target_splits.csv",
    "experiments/results/pv_shift_recalibration_summary.json",
    "experiments/results/pv_shift_recalibration_energy_value_metrics.csv",
    "experiments/results/pv_shift_recalibration_energy_value_metrics.md",
    "experiments/results/pv_shift_recalibration_energy_value_raw.csv",
    "experiments/results/pv_shift_recalibration_energy_value_summary.json",
    "experiments/results/risk_stratified_calibration_bus.csv",
    "experiments/results/risk_stratified_calibration_bus.md",
    "experiments/results/risk_stratified_calibration_scenario.csv",
    "experiments/results/risk_stratified_calibration_scenario.md",
    "experiments/results/risk_stratified_calibration_summary.json",
    "experiments/results/conformal_sensitivity_metrics.md",
    "experiments/results/operating_value_metrics.md",
    "experiments/results/energy_management_value_metrics.md",
    "experiments/results/energy_management_value_summary.json",
    "experiments/results/energy_management_value_multiseed_metrics.csv",
    "experiments/results/energy_management_value_multiseed_metrics.md",
    "experiments/results/energy_management_value_multiseed_raw.csv",
    "experiments/results/energy_management_value_multiseed_summary.json",
    "experiments/results/energy_management_frontier_metrics.csv",
    "experiments/results/energy_management_frontier_metrics.md",
    "experiments/results/energy_management_frontier_summary.json",
    "experiments/results/shift_energy_management_value_metrics.csv",
    "experiments/results/shift_energy_management_value_metrics.md",
    "experiments/results/shift_energy_management_value_raw.csv",
    "experiments/results/shift_energy_management_value_summary.json",
    "experiments/results/topology_transfer_bidirectional_metrics.csv",
    "experiments/results/topology_transfer_bidirectional_metrics.md",
    "experiments/results/topology_transfer_bidirectional_raw.csv",
    "experiments/results/topology_transfer_bidirectional_summary.json",
    "experiments/results/screened_safe_release_metrics.csv",
    "experiments/results/screened_safe_release_metrics.md",
    "experiments/results/screened_safe_release_summary.json",
    "experiments/results/screened_safe_release_multiseed_metrics.csv",
    "experiments/results/screened_safe_release_multiseed_metrics.md",
    "experiments/results/screened_safe_release_multiseed_raw.csv",
    "experiments/results/screened_safe_release_multiseed_summary.json",
    "experiments/results/screening_budget_metrics.csv",
    "experiments/results/screening_budget_metrics.md",
    "experiments/results/screening_budget_summary.json",
    "experiments/results/screening_budget_multiseed_metrics.csv",
    "experiments/results/screening_budget_multiseed_metrics.md",
    "experiments/results/screening_budget_multiseed_raw.csv",
    "experiments/results/screening_budget_multiseed_summary.json",
    "experiments/results/statistical_evidence_metrics.csv",
    "experiments/results/statistical_evidence_metrics.md",
    "experiments/results/statistical_evidence_raw.csv",
    "experiments/results/statistical_evidence_summary.json",
    "experiments/results/control_grid_search_candidate_actions.csv",
    "experiments/results/candidate_action_screening_metrics.csv",
    "experiments/results/candidate_action_screening_metrics.md",
    "experiments/results/candidate_action_screening_scores.csv",
    "experiments/results/candidate_action_screening_raw_predictions.csv",
    "experiments/results/candidate_action_screening_summary.json",
    "experiments/results/candidate_action_screening_multiseed_metrics.csv",
    "experiments/results/candidate_action_screening_multiseed_metrics.md",
    "experiments/results/candidate_action_screening_multiseed_raw.csv",
    "experiments/results/candidate_action_screening_multiseed_ac_candidates.csv",
    "experiments/results/candidate_action_screening_multiseed_scores.csv",
    "experiments/results/candidate_action_screening_multiseed_raw_predictions.csv",
    "experiments/results/candidate_action_screening_multiseed_summary.json",
    "experiments/results/action_cost_tradeoff_metrics.csv",
    "experiments/results/action_cost_tradeoff_metrics.md",
    "experiments/results/action_cost_tradeoff_summary.json",
    "experiments/results/action_cost_tradeoff_multiseed_metrics.csv",
    "experiments/results/action_cost_tradeoff_multiseed_metrics.md",
    "experiments/results/action_cost_tradeoff_multiseed_raw.csv",
    "experiments/results/action_cost_tradeoff_multiseed_summary.json",
    "experiments/results/runtime_operational_benchmark.csv",
    "experiments/results/runtime_operational_benchmark.md",
    "experiments/results/runtime_operational_summary.json",
    "experiments/results/runtime_ac_grid_raw.csv",
    "experiments/results/physics_consistency_audit.csv",
    "experiments/results/physics_consistency_audit.md",
    "experiments/results/physics_consistency_audit_raw.csv",
    "experiments/results/physics_consistency_summary.json",
    "experiments/results/scenario_risk_ranking_metrics.md",
    "experiments/results/scenario_risk_ranking_summary.json",
    "experiments/results/scenario_risk_ranking_raw.csv",
    "experiments/results/high_pv_hosting_stress_raw.csv",
    "experiments/results/high_pv_hosting_stress_by_feeder.csv",
    "experiments/results/high_pv_hosting_stress_by_feeder.md",
    "experiments/results/high_pv_hosting_stress_summary.json",
    "experiments/results/high_pv_hosting_frontier_raw.csv",
    "experiments/results/high_pv_hosting_frontier_metrics.csv",
    "experiments/results/high_pv_hosting_frontier_metrics.md",
    "experiments/results/high_pv_hosting_frontier_summary.json",
    "experiments/results/runtime_metrics.md",
    "experiments/results/raw_predictions_random_seed7.csv",
    "experiments/results/conformal_scores_random_seed7.csv",
    "experiments/results/control_grid_search_summary.json",
    "experiments/results/control_grid_search_selected_actions.csv",
    "experiments/results/evaluation_summary.json",
    "experiments/results/oajpe_lindistflow_quantile_metrics.csv",
    "experiments/results/oajpe_lindistflow_quantile_metrics.md",
    "experiments/results/oajpe_lindistflow_quantile_summary.json",
    "experiments/results/review_baseline_comparison_metrics.csv",
    "experiments/results/review_baseline_comparison_metrics.md",
    "experiments/results/dms_prototype_weekly_log.csv",
    "experiments/results/dms_prototype_queue_summary.md",
    "experiments/results/dms_prototype_summary.json",
    "experiments/results/baseline_design_rationale_metrics.csv",
    "experiments/results/baseline_design_rationale_metrics.md",
    "experiments/results/baseline_design_rationale_summary.json",
    "experiments/results/oajpe_lindistflow_quantile_raw_seed7.csv",
    "experiments/results/reproducibility_manifest.json",
    "experiments/results/reproducibility_manifest.md",
    "figures/figure_manifest.json",
]

REQUIRED_FIGURES = [
    "fig01_graphical_abstract_workflow",
    "fig02_feeders_and_splits",
    "fig03_conformal_ablation",
    "fig04_per_family_calibration",
    "fig05_shift_generalization",
    "fig06_operating_value",
    "fig07_energy_frontier",
    "fig08_screening_budget",
    "fig09_candidate_action_screening",
    "fig10_risk_ranking_quality",
    "fig11_oajpe_lindistflow_quantile_pipeline",
    "fig12_oajpe_minimal_performance",
]

MULTIPANEL_FIGURE_LABELS = {
    "fig02_feeders_and_splits": ["(a)", "(b)"],
    "fig03_conformal_ablation": ["(a)", "(b)", "(c)"],
    "fig05_shift_generalization": ["(a)", "(b)"],
    "fig06_operating_value": ["(a)", "(b)"],
    "fig07_energy_frontier": ["(a)", "(b)"],
    "fig09_candidate_action_screening": ["(a)", "(b)"],
    "fig10_risk_ranking_quality": ["(a)", "(b)"],
    "fig12_oajpe_minimal_performance": ["(a)", "(b)", "(c)"],
}


def labels_in_order_pattern(labels: list[str]) -> str:
    return ".*?".join(re.escape(label) for label in labels)


def figure_caption_has_subfigure_labels(text: str, name: str, labels: list[str]) -> bool:
    label_pattern = labels_in_order_pattern(labels)
    markdown_pattern = (
        rf"!\[[^\]]*{label_pattern}[^\]]*\]"
        rf"\(figures/{re.escape(name)}\.pdf\)"
    )
    latex_pattern = (
        rf"\\includegraphics[^\n]*\{{figures/{re.escape(name)}\.pdf\}}"
        rf".*?\\caption\{{[^}}]*{label_pattern}[^}}]*\}}"
    )
    return bool(re.search(markdown_pattern, text, flags=re.S) or re.search(latex_pattern, text, flags=re.S))


def contains_any(path: Path, terms: list[str]) -> bool:
    text = path.read_text(encoding="utf-8").lower()
    return any(term.lower() in text for term in terms)


def text_contains_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def section_between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        return ""
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end < 0:
        return text[start:]
    return text[start:end]


def token_between(text: str, token: str, start_marker: str, end_marker: str) -> bool:
    start = text.find(start_marker)
    if start < 0:
        return False
    pos = text.find(token, start)
    if pos < 0:
        return False
    end = text.find(end_marker, start)
    return end < 0 or pos < end


def all_figures_before_references(text: str, names: list[str]) -> bool:
    ref_match = re.search(r"^#{1,2}\s+References\s*$", text, flags=re.M)
    ref_pos = ref_match.start() if ref_match else -1
    return all(
        text.find(f"figures/{name}.pdf") >= 0
        and (ref_pos < 0 or text.find(f"figures/{name}.pdf") < ref_pos)
        for name in names
    )


def has_nonzero_text_rotation(svg_text: str) -> bool:
    for match in re.finditer(r"rotate\((-?\d+(?:\.\d+)?)", svg_text):
        if abs(float(match.group(1))) > 0.01:
            return True
    return False


def has_curved_arrow_path(svg_text: str) -> bool:
    for match in re.finditer(r'<path\s+[^>]*d="([^"]+)"[^>]*marker-end="url\(#arrow\)"', svg_text):
        if re.search(r"[CcQqSsTtAa]", match.group(1)):
            return True
    return False


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    summary = json.loads((RESULTS / "evaluation_summary.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "experiments" / "experiment_config.json").read_text(encoding="utf-8"))
    metrics = pd.read_csv(RESULTS / "evaluation_metrics_all_runs.csv")
    family = pd.read_csv(RESULTS / "per_family_conformal_metrics.csv")
    raw = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    scores = pd.read_csv(RESULTS / "conformal_scores_random_seed7.csv")
    control = json.loads((RESULTS / "control_grid_search_summary.json").read_text(encoding="utf-8"))
    energy_value = json.loads((RESULTS / "energy_management_value_summary.json").read_text(encoding="utf-8"))
    energy_value_multiseed = json.loads(
        (RESULTS / "energy_management_value_multiseed_summary.json").read_text(encoding="utf-8")
    )
    shift_energy_value = json.loads(
        (RESULTS / "shift_energy_management_value_summary.json").read_text(encoding="utf-8")
    )
    topology_transfer_summary = json.loads(
        (RESULTS / "topology_transfer_bidirectional_summary.json").read_text(encoding="utf-8")
    )
    screened_release_summary = json.loads(
        (RESULTS / "screened_safe_release_summary.json").read_text(encoding="utf-8")
    )
    screened_release_multiseed_summary = json.loads(
        (RESULTS / "screened_safe_release_multiseed_summary.json").read_text(encoding="utf-8")
    )
    recalibration_summary = json.loads((RESULTS / "family_recalibration_summary.json").read_text(encoding="utf-8"))
    forecast_noise_summary = json.loads((RESULTS / "forecast_noise_robustness_summary.json").read_text(encoding="utf-8"))
    pv_shift_recalibration_summary = json.loads((RESULTS / "pv_shift_recalibration_summary.json").read_text(encoding="utf-8"))
    pv_shift_recalibration_energy_summary = json.loads(
        (RESULTS / "pv_shift_recalibration_energy_value_summary.json").read_text(encoding="utf-8")
    )
    risk_stratified_summary = json.loads((RESULTS / "risk_stratified_calibration_summary.json").read_text(encoding="utf-8"))
    calibration_budget_summary = json.loads((RESULTS / "calibration_budget_sensitivity_summary.json").read_text(encoding="utf-8"))
    asymmetric_conformal_summary = json.loads((RESULTS / "asymmetric_conformal_summary.json").read_text(encoding="utf-8"))
    paired_delta_summary = json.loads((RESULTS / "paired_seed_delta_summary.json").read_text(encoding="utf-8"))
    feature_ablation_summary = json.loads((RESULTS / "feature_residual_ablation_summary.json").read_text(encoding="utf-8"))
    ev_conditioning_summary = json.loads((RESULTS / "ev_conditioning_summary.json").read_text(encoding="utf-8"))
    budget_summary = json.loads((RESULTS / "screening_budget_summary.json").read_text(encoding="utf-8"))
    screening_budget_multiseed_summary = json.loads(
        (RESULTS / "screening_budget_multiseed_summary.json").read_text(encoding="utf-8")
    )
    statistical_evidence_summary = json.loads(
        (RESULTS / "statistical_evidence_summary.json").read_text(encoding="utf-8")
    )
    energy_frontier_summary = json.loads(
        (RESULTS / "energy_management_frontier_summary.json").read_text(encoding="utf-8")
    )
    candidate_action_summary = json.loads((RESULTS / "candidate_action_screening_summary.json").read_text(encoding="utf-8"))
    candidate_action_multiseed_summary = json.loads(
        (RESULTS / "candidate_action_screening_multiseed_summary.json").read_text(encoding="utf-8")
    )
    action_cost_tradeoff_summary = json.loads((RESULTS / "action_cost_tradeoff_summary.json").read_text(encoding="utf-8"))
    action_cost_tradeoff_multiseed_summary = json.loads(
        (RESULTS / "action_cost_tradeoff_multiseed_summary.json").read_text(encoding="utf-8")
    )
    runtime_operational_summary = json.loads((RESULTS / "runtime_operational_summary.json").read_text(encoding="utf-8"))
    ranking_summary = json.loads((RESULTS / "scenario_risk_ranking_summary.json").read_text(encoding="utf-8"))
    physics_summary = json.loads((RESULTS / "physics_consistency_summary.json").read_text(encoding="utf-8"))
    hosting_summary = json.loads((RESULTS / "high_pv_hosting_stress_summary.json").read_text(encoding="utf-8"))
    hosting_frontier_summary = json.loads(
        (RESULTS / "high_pv_hosting_frontier_summary.json").read_text(encoding="utf-8")
    )
    energy_metrics = pd.read_csv(RESULTS / "energy_management_value_metrics.csv")
    energy_multiseed_metrics = pd.read_csv(RESULTS / "energy_management_value_multiseed_metrics.csv")
    energy_multiseed_raw = pd.read_csv(RESULTS / "energy_management_value_multiseed_raw.csv")
    energy_frontier_metrics = pd.read_csv(RESULTS / "energy_management_frontier_metrics.csv")
    shift_energy_metrics = pd.read_csv(RESULTS / "shift_energy_management_value_metrics.csv")
    shift_energy_raw = pd.read_csv(RESULTS / "shift_energy_management_value_raw.csv")
    topology_transfer_metrics = pd.read_csv(RESULTS / "topology_transfer_bidirectional_metrics.csv")
    topology_transfer_raw = pd.read_csv(RESULTS / "topology_transfer_bidirectional_raw.csv")
    screened_release_metrics = pd.read_csv(RESULTS / "screened_safe_release_metrics.csv")
    screened_release_multiseed_metrics = pd.read_csv(RESULTS / "screened_safe_release_multiseed_metrics.csv")
    screened_release_multiseed_raw = pd.read_csv(RESULTS / "screened_safe_release_multiseed_raw.csv")
    recalibration_metrics = pd.read_csv(RESULTS / "family_recalibration_audit.csv")
    forecast_noise_metrics = pd.read_csv(RESULTS / "forecast_noise_robustness_metrics.csv")
    pv_shift_recalibration_metrics = pd.read_csv(RESULTS / "pv_shift_recalibration_metrics.csv")
    pv_shift_recalibration_energy_metrics = pd.read_csv(
        RESULTS / "pv_shift_recalibration_energy_value_metrics.csv"
    )
    pv_shift_recalibration_energy_raw = pd.read_csv(
        RESULTS / "pv_shift_recalibration_energy_value_raw.csv"
    )
    pv_shift_target_splits = pd.read_csv(RESULTS / "pv_shift_recalibration_target_splits.csv")
    risk_stratified_bus = pd.read_csv(RESULTS / "risk_stratified_calibration_bus.csv")
    risk_stratified_scenario = pd.read_csv(RESULTS / "risk_stratified_calibration_scenario.csv")
    calibration_budget_metrics = pd.read_csv(RESULTS / "calibration_budget_sensitivity_metrics.csv")
    calibration_budget_raw = pd.read_csv(RESULTS / "calibration_budget_sensitivity_raw.csv")
    asymmetric_conformal_metrics = pd.read_csv(RESULTS / "asymmetric_conformal_metrics.csv")
    paired_delta_metrics = pd.read_csv(RESULTS / "paired_seed_delta_summary.csv")
    feature_ablation_metrics = pd.read_csv(RESULTS / "feature_residual_ablation.csv")
    ev_conditioning_metrics = pd.read_csv(RESULTS / "ev_conditioning_ablation.csv")
    budget_metrics = pd.read_csv(RESULTS / "screening_budget_metrics.csv")
    screening_budget_multiseed_metrics = pd.read_csv(RESULTS / "screening_budget_multiseed_metrics.csv")
    screening_budget_multiseed_raw = pd.read_csv(RESULTS / "screening_budget_multiseed_raw.csv")
    statistical_evidence_metrics = pd.read_csv(RESULTS / "statistical_evidence_metrics.csv")
    statistical_evidence_raw = pd.read_csv(RESULTS / "statistical_evidence_raw.csv")
    control_candidates = pd.read_csv(RESULTS / "control_grid_search_candidate_actions.csv")
    candidate_action_metrics = pd.read_csv(RESULTS / "candidate_action_screening_metrics.csv")
    candidate_action_scores = pd.read_csv(RESULTS / "candidate_action_screening_scores.csv")
    candidate_action_raw = pd.read_csv(RESULTS / "candidate_action_screening_raw_predictions.csv")
    candidate_action_multiseed_metrics = pd.read_csv(
        RESULTS / "candidate_action_screening_multiseed_metrics.csv"
    )
    candidate_action_multiseed_raw = pd.read_csv(RESULTS / "candidate_action_screening_multiseed_raw.csv")
    candidate_action_multiseed_ac = pd.read_csv(
        RESULTS / "candidate_action_screening_multiseed_ac_candidates.csv"
    )
    candidate_action_multiseed_scores = pd.read_csv(
        RESULTS / "candidate_action_screening_multiseed_scores.csv"
    )
    candidate_action_multiseed_predictions = pd.read_csv(
        RESULTS / "candidate_action_screening_multiseed_raw_predictions.csv"
    )
    action_cost_tradeoff_metrics = pd.read_csv(RESULTS / "action_cost_tradeoff_metrics.csv")
    action_cost_tradeoff_multiseed_metrics = pd.read_csv(
        RESULTS / "action_cost_tradeoff_multiseed_metrics.csv"
    )
    action_cost_tradeoff_multiseed_raw = pd.read_csv(RESULTS / "action_cost_tradeoff_multiseed_raw.csv")
    runtime_operational_metrics = pd.read_csv(RESULTS / "runtime_operational_benchmark.csv")
    ranking_metrics = pd.read_csv(RESULTS / "scenario_risk_ranking_metrics.csv")
    physics_metrics = pd.read_csv(RESULTS / "physics_consistency_audit.csv")
    hosting_by_feeder = pd.read_csv(RESULTS / "high_pv_hosting_stress_by_feeder.csv")
    hosting_frontier_metrics = pd.read_csv(RESULTS / "high_pv_hosting_frontier_metrics.csv")
    hosting_frontier_raw = pd.read_csv(RESULTS / "high_pv_hosting_frontier_raw.csv")
    review_baseline_metrics = pd.read_csv(RESULTS / "review_baseline_comparison_metrics.csv")
    dms_prototype_log = pd.read_csv(RESULTS / "dms_prototype_weekly_log.csv")
    dms_prototype_summary = json.loads((RESULTS / "dms_prototype_summary.json").read_text(encoding="utf-8"))
    baseline_design_metrics = pd.read_csv(RESULTS / "baseline_design_rationale_metrics.csv")
    manuscript = ROOT / "manuscript_draft.md"
    manuscript_text = manuscript.read_text(encoding="utf-8")
    ecm_source_text = (ROOT / "manuscript_ecm_engineering.md").read_text(encoding="utf-8")
    oajpe_source_text = (ROOT / "manuscript_oajpe_minimal.md").read_text(encoding="utf-8")
    ecmx_submission_text = (ROOT / "submission_manuscript_ecmx.md").read_text(encoding="utf-8")
    ecm_submission_text = (ROOT / "submission_manuscript_ecm.md").read_text(encoding="utf-8")
    oajpe_submission_text = (ROOT / "submission_manuscript_oajpe.md").read_text(encoding="utf-8")
    variant_strategy_text = (ROOT / "submission_variant_strategy.md").read_text(encoding="utf-8")
    ancillaries_text = (ROOT / "submission_ancillaries.md").read_text(encoding="utf-8")
    audit_text = (ROOT / "completion_audit.md").read_text(encoding="utf-8")
    highlights = [
        line.strip()
        for line in (ROOT / "ecmx_highlights.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ecm_highlights = [
        line.strip()
        for line in (ROOT / "ecm_highlights.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cover_letter_text = (ROOT / "ecmx_cover_letter.md").read_text(encoding="utf-8")
    readiness_text = (ROOT / "ecmx_submission_readiness_checklist.md").read_text(encoding="utf-8")
    upload_packet_text = (ROOT / "ecmx_upload_input_packet.md").read_text(encoding="utf-8")
    claim_matrix_text = (ROOT / "claim_evidence_matrix.md").read_text(encoding="utf-8")
    professional_review_action_text = (ROOT / "Professional_Review_Action_Matrix.md").read_text(encoding="utf-8")
    venue_source_text = (ROOT / "venue_source_audit.md").read_text(encoding="utf-8")
    venue_matrix_text = (ROOT / "high_impact_venue_matrix.md").read_text(encoding="utf-8")
    submission_strategy_text = (ROOT / "submission_strategy.md").read_text(encoding="utf-8")
    journal_format_text = (ROOT / "journal_format_audit.md").read_text(encoding="utf-8")
    references_text = (ROOT / "submission_references.md").read_text(encoding="utf-8")
    manifest = json.loads((RESULTS / "reproducibility_manifest.json").read_text(encoding="utf-8"))
    abstract_words = section_between(
        manuscript_text,
        "## Abstract",
        "## 1. Introduction",
    ).split()
    allowed_raster_assets = {
        ROOT / "figures" / "assets" / "active_distribution_scenario_inset.png"
    }
    raster_article_images = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
        and ".venv" not in path.parts
        and "submission_build" not in path.parts
        and path not in allowed_raster_assets
    ]
    figure_manifest = json.loads((ROOT / "figures" / "figure_manifest.json").read_text(encoding="utf-8"))
    svg_texts = {
        name: (ROOT / "figures" / f"{name}.svg").read_text(encoding="utf-8")
        for name in REQUIRED_FIGURES
        if (ROOT / "figures" / f"{name}.svg").exists()
    }
    ecmx_tex = ROOT / "submission_manuscript_ecmx.tex"
    ecmx_md = ROOT / "submission_manuscript_ecmx.md"
    ecmx_pdf = ROOT / "submission_build" / "submission_manuscript_ecmx.pdf"
    ecm_tex = ROOT / "submission_manuscript_ecm.tex"
    ecm_md = ROOT / "submission_manuscript_ecm.md"
    ecm_pdf = ROOT / "submission_build" / "submission_manuscript_ecm.pdf"
    oajpe_tex = ROOT / "submission_manuscript_oajpe.tex"
    oajpe_md = ROOT / "submission_manuscript_oajpe.md"
    oajpe_pdf = ROOT / "submission_build" / "submission_manuscript_oajpe.pdf"
    ecmx_tex_text = ecmx_tex.read_text(encoding="utf-8")
    ecm_tex_text = ecm_tex.read_text(encoding="utf-8")
    oajpe_tex_text = oajpe_tex.read_text(encoding="utf-8")

    primary = metrics[
        (metrics["split_name"] == "random_interpolation")
        & (metrics["seed"] == config["representative_seed"])
        & (metrics["method"] == "VoltGuard topology-aware residual")
        & (metrics["conformal_variant"] == "topology_pv_loading_conditioned")
    ]
    neural = metrics[metrics["method"] == "Neural graph residual ablation"]
    split_names = set(metrics["split_name"].dropna())
    checks = {
        "missing_files": missing,
        "main_feeders_are_33_69": summary.get("main_feeders") == ["33", "69"],
        "supplementary_118_present": summary.get("supplementary_feeders") == ["118"],
        "required_splits_present": {
            "random_interpolation",
            "synthetic_time_block",
            "pv_penetration_shift",
            "topology_heldout_33_to_69",
        }.issubset(split_names),
        "three_evaluation_seeds": summary.get("evaluation_seeds") == [7, 17, 42],
        "paired_seed_delta_present": (
            paired_delta_summary.get("rows") == 5
            and paired_delta_summary.get("random_delta_missed_mean", 1) < 0
            and paired_delta_summary.get("random_delta_recall_mean", 0) > 0
            and paired_delta_summary.get("topology_heldout_delta_missed_mean", 1) <= 0
            and paired_delta_summary.get("topology_heldout_delta_false_alarm_mean", 1) < 0
            and {
                "delta_missed_violations_mean",
                "delta_missed_violations_ci95",
                "delta_recall_mean",
                "delta_false_alarm_rate_mean",
            }.issubset(paired_delta_metrics.columns)
        ),
        "feature_residual_ablation_present": (
            feature_ablation_summary.get("rows") == 4
            and feature_ablation_summary.get("raw_rows") == 12
            and feature_ablation_summary.get("runs_per_variant") == 3
            and feature_ablation_summary.get("full_residual_missed_mean", 999)
            < feature_ablation_summary.get("local_residual_missed_mean", 0)
            and feature_ablation_summary.get("full_residual_rmse_mean", 999)
            < feature_ablation_summary.get("local_residual_rmse_mean", 0)
            and feature_ablation_summary.get("full_residual_rmse_mean", 999)
            < feature_ablation_summary.get("direct_full_rmse_mean", 0)
            and {
                "variant",
                "feature_family",
                "rmse_mean",
                "avg_width_mean",
                "recall_mean",
                "missed_violations_mean",
                "false_alarm_rate_mean",
            }.issubset(feature_ablation_metrics.columns)
        ),
        "ev_conditioning_ablation_present": (
            ev_conditioning_summary.get("rows") == 5
            and ev_conditioning_summary.get("primary_families") == 16
            and ev_conditioning_summary.get("ev_full_families", 0) > ev_conditioning_summary.get("primary_families", 99)
            and ev_conditioning_summary.get("ev_full_min_calibration_samples", 999) < 50
            and ev_conditioning_summary.get("ev_full_empty_test_families", 0) > 0
            and ev_conditioning_summary.get("ev_full_missed", 999) >= ev_conditioning_summary.get("primary_missed", 0)
            and ev_conditioning_summary.get("ev_full_width_delta", 0) > 0
            and ev_conditioning_summary.get("ev_full_recall_delta", 1) <= 0
            and {
                "variant",
                "families",
                "min_calibration_samples",
                "empty_test_families",
                "coverage",
                "recall",
                "missed_violations",
            }.issubset(ev_conditioning_metrics.columns)
        ),
        "primary_row_present": len(primary) == 1,
        "primary_recall_positive": float(primary["recall"].iloc[0]) > 0.95 if len(primary) else False,
        "neural_ablation_present": len(neural) > 0,
        "family_metrics_present": len(family) > 0 and {"coverage", "avg_width", "recall"}.issubset(family.columns),
        "family_recalibration_audit_present": (
            recalibration_summary.get("rows") == 16
            and recalibration_summary.get("undercovered_families") == 5
            and recalibration_summary.get("missed_current_total") == 1
            and recalibration_summary.get("missed_audited_total") == 1
            and recalibration_summary.get("weighted_width_audited", 0)
            > recalibration_summary.get("weighted_width_current", 1)
            and recalibration_summary.get("weighted_false_alarm_audited", 0)
            >= recalibration_summary.get("weighted_false_alarm_current", 1)
            and "feeder=33|pv_bin=0.8|load_bin=low_load" == recalibration_summary.get("worst_family")
            and {
                "coverage_current",
                "coverage_audited",
                "width_audited",
                "missed_recovered",
                "false_alarm_audited",
            }.issubset(recalibration_metrics.columns)
        ),
        "pv_shift_recalibration_present": (
            pv_shift_recalibration_summary.get("rows") == 12
            and pv_shift_recalibration_summary.get("raw_rows") == 36
            and pv_shift_recalibration_summary.get("primary_source_coverage", 1) < 0.80
            and pv_shift_recalibration_summary.get("primary_adapted_fraction") == 0.1
            and pv_shift_recalibration_summary.get("primary_adapted_target_calibration_scenarios", 0) >= 10
            and pv_shift_recalibration_summary.get("primary_adapted_coverage", 0)
            > pv_shift_recalibration_summary.get("primary_source_coverage", 1)
            and pv_shift_recalibration_summary.get("primary_adapted_coverage", 0) > 0.88
            and pv_shift_recalibration_summary.get("primary_adapted_width", 0)
            > pv_shift_recalibration_summary.get("primary_source_width", 1)
            and pv_shift_recalibration_summary.get("primary_adapted_missed") == 0
            and pv_shift_recalibration_summary.get("primary_adapted_scenario_recall") == 1.0
            and {
                "target_fraction",
                "target_calibration_scenarios_mean",
                "coverage_mean",
                "avg_width_mean",
                "recall_mean",
                "false_alarm_rate_mean",
                "missed_violations_mean",
            }.issubset(pv_shift_recalibration_metrics.columns)
            and {"source_only", "source_plus_target_high_pv"}.issubset(set(pv_shift_target_splits["protocol"]))
        ),
        "pv_shift_recalibration_energy_value_present": (
            pv_shift_recalibration_energy_summary.get("rows") == 8
            and pv_shift_recalibration_energy_summary.get("raw_rows") == 24
            and pv_shift_recalibration_energy_summary.get("seeds") == config["evaluation_seeds"]
            and pv_shift_recalibration_energy_summary.get("primary_alpha") == config["primary_alpha"]
            and pv_shift_recalibration_energy_summary.get("adapted_fraction") == 0.1
            and pv_shift_recalibration_energy_summary.get("adapted_target_calibration_scenarios_mean", 0) >= 10
            and pv_shift_recalibration_energy_summary.get("adapted_missed_bus_violations_mean") == 0.0
            and pv_shift_recalibration_energy_summary.get("source_missed_bus_violations_mean", 0) > 0
            and pv_shift_recalibration_energy_summary.get("adapted_risky_scenario_recall_mean") == 1.0
            and pv_shift_recalibration_energy_summary.get("adapted_post_screening_miss_rate_mean") == 0.0
            and pv_shift_recalibration_energy_summary.get("width_increase_vs_source", 0) > 0
            and pv_shift_recalibration_energy_summary.get("screened_safe_delta_vs_source", 1) < 0
            and len(pv_shift_recalibration_energy_raw) == 24
            and {
                "target_fraction",
                "target_calibration_scenarios_mean",
                "screened_safe_scenarios_mean",
                "ac_optimization_calls_avoided_mean",
                "missed_bus_violations_mean",
                "mean_interval_width_mean",
            }.issubset(pv_shift_recalibration_energy_metrics.columns)
        ),
        "forecast_noise_robustness_present": (
            forecast_noise_summary.get("rows") == 12
            and forecast_noise_summary.get("raw_rows") == 12
            and forecast_noise_summary.get("audit_seeds") == [7]
            and {0.0, 0.05, 0.1, 0.2}
            == set(round(float(value), 2) for value in forecast_noise_metrics["forecast_noise_sigma"].unique())
            and forecast_noise_summary.get("primary_clean_recall", 0) > 0.99
            and 0.88 < forecast_noise_summary.get("primary_10pct_coverage", 0) < forecast_noise_summary.get("primary_clean_coverage", 1)
            and forecast_noise_summary.get("primary_10pct_recall", 0) > 0.98
            and forecast_noise_summary.get("primary_10pct_missed", 0) >= 10
            and forecast_noise_summary.get("primary_10pct_scenario_recall") == 1.0
            and {
                "forecast_noise_sigma",
                "rmse_mean",
                "coverage_mean",
                "avg_width_mean",
                "recall_mean",
                "false_alarm_rate_mean",
                "missed_violations_mean",
                "scenario_recall_mean",
            }.issubset(forecast_noise_metrics.columns)
        ),
        "risk_stratified_calibration_present": (
            risk_stratified_summary.get("bus_rows") == 28
            and risk_stratified_summary.get("scenario_rows") == 28
            and risk_stratified_summary.get("primary_violating_bus_recall", 0) > 0.99
            and risk_stratified_summary.get("primary_violating_bus_missed") == 1
            and risk_stratified_summary.get("primary_boundary_safe_bus_false_alarm_rate", 1) < 0.06
            and risk_stratified_summary.get("primary_violating_scenario_recall") == 1.0
            and risk_stratified_summary.get("primary_safe_scenario_false_alarms") == 0
            and {"violating", "boundary_safe", "near_safe", "interior_safe"}
            == set(risk_stratified_bus["risk_stratum"].dropna().unique())
            and {"violating", "boundary_safe", "near_safe", "interior_safe"}
            == set(risk_stratified_scenario["risk_stratum"].dropna().unique())
            and {
                "coverage",
                "avg_width",
                "risk_flag_rate",
                "violation_recall",
                "false_alarm_rate",
            }.issubset(risk_stratified_bus.columns)
            and {
                "scenario_coverage_mean",
                "mean_interval_width",
                "scenario_recall",
                "scenario_false_alarm_rate",
            }.issubset(risk_stratified_scenario.columns)
        ),
        "calibration_budget_sensitivity_present": (
            calibration_budget_summary.get("rows") == 10
            and calibration_budget_summary.get("raw_rows") == 162
            and calibration_budget_summary.get("fractions") == [0.1, 0.25, 0.5, 0.75, 1.0]
            and calibration_budget_summary.get("repeats") == 20
            and calibration_budget_summary.get("primary_10pct_coverage_mean", 0) > 0.90
            and calibration_budget_summary.get("primary_10pct_empty_test_families_mean", 0) > 5.0
            and calibration_budget_summary.get("primary_full_coverage", 0) > 0.93
            and calibration_budget_summary.get("primary_full_empty_test_families") == 0.0
            and calibration_budget_summary.get("primary_full_missed") == 1.0
            and len(calibration_budget_raw) == 162
            and {
                "calibration_fraction",
                "families_observed_calib_mean",
                "empty_test_families_mean",
                "coverage_mean",
                "avg_width_mean",
                "recall_mean",
                "missed_violations_mean",
            }.issubset(calibration_budget_metrics.columns)
        ),
        "asymmetric_conformal_audit_present": (
            asymmetric_conformal_summary.get("rows") == 6
            and asymmetric_conformal_summary.get("family_rows") == 18
            and asymmetric_conformal_summary.get("primary_asymmetric_width", 1)
            < asymmetric_conformal_summary.get("primary_symmetric_width", 0)
            and asymmetric_conformal_summary.get("primary_asymmetric_missed") == 0
            and asymmetric_conformal_summary.get("primary_symmetric_missed") == 1
            and asymmetric_conformal_summary.get("primary_asymmetric_recall", 0)
            >= asymmetric_conformal_summary.get("primary_symmetric_recall", 1)
            and asymmetric_conformal_summary.get("primary_asymmetric_scenario_recall") == 1.0
            and {
                "calibration",
                "coverage",
                "avg_width",
                "width_delta_vs_symmetric",
                "missed_delta_vs_symmetric",
            }.issubset(asymmetric_conformal_metrics.columns)
        ),
        "raw_predictions_present": len(raw) > 0 and {"lower", "upper", "risk_flag"}.issubset(raw.columns),
        "conformal_scores_present": len(scores) > 0 and "nonconformity_score" in scores.columns,
        "control_benchmark_ran": control.get("method") == "AC corrective grid-search benchmark",
        "control_converged": control.get("converged_scenarios") == control.get("test_scenarios"),
        "energy_value_rows": energy_value.get("rows") == 8,
        "energy_value_columns_present": {
            "screened_safe_ratio",
            "ac_optimization_calls_avoided",
            "risky_scenario_recall",
            "post_screening_violation_miss_rate",
            "accepted_pv_proxy_mw",
            "curtailed_pv_proxy_mw",
            "relieved_load_proxy_mw",
            "proxy_action_cost_mw",
        }.issubset(energy_metrics.columns),
        "energy_value_multiseed_present": (
            energy_value_multiseed.get("rows") == 8
            and energy_value_multiseed.get("raw_rows") == 24
            and energy_value_multiseed.get("seeds") == config["evaluation_seeds"]
            and energy_value_multiseed.get("primary_alpha") == config["primary_alpha"]
            and energy_value_multiseed.get("primary_ac_calls_avoided_mean", 0) > 25
            and energy_value_multiseed.get("primary_risky_scenario_recall_mean") == 1.0
            and energy_value_multiseed.get("primary_post_screening_miss_rate_mean") == 0.0
            and energy_value_multiseed.get("primary_missed_risky_scenarios_mean") == 0.0
            and energy_value_multiseed.get("primary_missed_bus_violations_mean", 99)
            < energy_value_multiseed.get("boost_missed_bus_violations_mean", 0)
            and energy_value_multiseed.get("missed_bus_violations_delta_vs_boost", 1) < 0
            and len(energy_multiseed_raw) == 24
            and {
                "screened_safe_scenarios_mean",
                "ac_optimization_calls_avoided_mean",
                "risky_scenario_recall_mean",
                "post_screening_violation_miss_rate_mean",
                "missed_bus_violations_mean",
                "mean_interval_width_mean",
            }.issubset(energy_multiseed_metrics.columns)
        ),
        "energy_management_frontier_present": (
            energy_frontier_summary.get("rows") == 21
            and set(energy_frontier_summary.get("frontier_types", []))
            == {
                "budgeted_ac_triage",
                "candidate_action_pruning",
                "conformal_release",
                "high_pv_hosting",
            }
            and energy_frontier_summary.get("primary_release_calls_avoided_mean", 0) > 27
            and energy_frontier_summary.get("primary_release_missed_risky_scenarios_mean") == 0.0
            and energy_frontier_summary.get("primary_budget_calls_avoided_mean") == 96.0
            and energy_frontier_summary.get("primary_budget_capture_gain_vs_random", 0) > 0.1
            and energy_frontier_summary.get("primary_action_audits_avoided_mean") == 720.0
            and energy_frontier_summary.get("primary_action_extra_violating_buses_mean") == 0.0
            and energy_frontier_summary.get("primary_hosting_accepted_pv_mw", 0) > 390
            and energy_frontier_summary.get("primary_hosting_overvoltage_scenario_reduction_ratio", 0) > 0.67
            and len(energy_frontier_metrics) == 21
            and {
                "frontier",
                "operating_setting",
                "risk_tolerance",
                "ac_calls_avoided_mean",
                "candidate_ac_audits_avoided_mean",
                "accepted_pv_mw_mean",
                "comparison_delta",
            }.issubset(energy_frontier_metrics.columns)
        ),
        "shift_energy_value_present": (
            shift_energy_value.get("rows") == 8
            and shift_energy_value.get("raw_rows") == 24
            and shift_energy_value.get("seeds") == config["evaluation_seeds"]
            and shift_energy_value.get("primary_alpha") == config["primary_alpha"]
            and set(shift_energy_value.get("splits", []))
            == {
                "random_interpolation",
                "synthetic_time_block",
                "pv_penetration_shift",
                "topology_heldout_33_to_69",
            }
            and shift_energy_value.get("voltguard_min_risky_scenario_recall_mean") == 1.0
            and shift_energy_value.get("voltguard_max_post_screening_miss_rate_mean") == 0.0
            and shift_energy_value.get("voltguard_random_ac_calls_avoided_mean", 0) > 25
            and shift_energy_value.get("voltguard_pv_shift_missed_risky_scenarios_mean") == 0.0
            and shift_energy_value.get("voltguard_topology_missed_risky_scenarios_mean") == 0.0
            and shift_energy_value.get("voltguard_topology_bus_recall_mean") == 1.0
            and len(shift_energy_raw) == 24
            and {
                "split_name",
                "ac_optimization_calls_avoided_mean",
                "risky_scenario_recall_mean",
                "post_screening_violation_miss_rate_mean",
                "missed_bus_violations_mean",
                "mean_interval_width_mean",
            }.issubset(shift_energy_metrics.columns)
        ),
        "topology_transfer_bidirectional_present": (
            topology_transfer_summary.get("rows") == 4
            and topology_transfer_summary.get("raw_rows") == 12
            and topology_transfer_summary.get("seeds") == config["evaluation_seeds"]
            and topology_transfer_summary.get("primary_alpha") == config["primary_alpha"]
            and set(topology_transfer_summary.get("directions", [])) == {"33_to_69", "69_to_33"}
            and topology_transfer_summary.get("voltguard_min_scenario_recall_mean") == 1.0
            and topology_transfer_summary.get("voltguard_max_post_screening_miss_rate_mean") == 0.0
            and topology_transfer_summary.get("direction_summary", {})
            .get("33_to_69", {})
            .get("voltguard_missed_bus_violations_mean")
            == 0.0
            and topology_transfer_summary.get("direction_summary", {})
            .get("69_to_33", {})
            .get("voltguard_missed_bus_violations_mean")
            == 0.0
            and topology_transfer_summary.get("direction_summary", {})
            .get("33_to_69", {})
            .get("width_delta_vs_boost", 1)
            < 0
            and topology_transfer_summary.get("direction_summary", {})
            .get("69_to_33", {})
            .get("voltguard_ac_calls_avoided_mean", 0)
            > 50
            and len(topology_transfer_raw) == 12
            and {
                "transfer_direction",
                "rmse_mean",
                "coverage_mean",
                "avg_width_mean",
                "missed_violations_mean",
                "scenario_recall_mean",
                "ac_optimization_calls_avoided_mean",
            }.issubset(topology_transfer_metrics.columns)
        ),
        "screened_safe_release_present": (
            screened_release_summary.get("rows") == 11
            and screened_release_summary.get("point_gate_rows") == 3
            and screened_release_summary.get("conformal_rows") == 8
            and screened_release_summary.get("primary_alpha") == config["primary_alpha"]
            and screened_release_summary.get("primary_released_scenarios") == 27
            and screened_release_summary.get("primary_safe_release_precision") == 1.0
            and screened_release_summary.get("primary_released_risky_scenarios") == 0
            and screened_release_summary.get("primary_released_severity_share") == 0.0
            and screened_release_summary.get("primary_ac_calls_avoided") == 27
            and screened_release_summary.get("point_ldf_released_risky_scenarios", 0) > 0
            and screened_release_summary.get("point_ldf_released_severity_share", 0) > 0
            and {
                "safe_release_precision",
                "released_risky_scenarios",
                "released_severity_share",
                "max_released_severity",
                "released_violating_buses",
                "released_available_pv_mw",
            }.issubset(screened_release_metrics.columns)
        ),
        "screened_safe_release_multiseed_present": (
            screened_release_multiseed_summary.get("rows") == 5
            and screened_release_multiseed_summary.get("raw_rows") == 15
            and screened_release_multiseed_summary.get("seeds") == config["evaluation_seeds"]
            and screened_release_multiseed_summary.get("primary_alpha") == config["primary_alpha"]
            and screened_release_multiseed_summary.get("primary_released_scenarios_mean", 0) > 25
            and screened_release_multiseed_summary.get("primary_safe_release_precision_mean") == 1.0
            and screened_release_multiseed_summary.get("primary_released_risky_scenarios_mean") == 0.0
            and screened_release_multiseed_summary.get("primary_released_risky_scenarios_ci95") == 0.0
            and screened_release_multiseed_summary.get("primary_released_severity_share_mean") == 0.0
            and screened_release_multiseed_summary.get("ldf_point_released_risky_scenarios_mean", 0) > 1.0
            and len(screened_release_multiseed_raw) == 15
            and {
                "released_scenarios_mean",
                "safe_release_precision_mean",
                "released_risky_scenarios_mean",
                "released_risky_scenarios_ci95",
                "released_severity_share_mean",
                "released_violating_buses_mean",
            }.issubset(screened_release_multiseed_metrics.columns)
        ),
        "risk_ranking_metrics_present": (
            ranking_summary.get("rows") == 7
            and ranking_summary.get("primary_average_precision", 0) > 0.98
            and ranking_summary.get("primary_spearman_score_severity", 0) > 0.90
            and {"roc_auc", "average_precision", "spearman_score_severity", "top20_severity_capture", "bottom10_safe_precision"}.issubset(ranking_metrics.columns)
        ),
        "screening_budget_metrics_present": (
            budget_summary.get("rows") == 45
            and budget_summary.get("primary_ac_calls") == 24
            and budget_summary.get("primary_calls_avoided") == 96
            and budget_summary.get("primary_severity_capture", 0) > 0.50
            and budget_summary.get("primary_severity_reduction_ratio", 0) > 0.20
            and {
                "budget_fraction",
                "ac_calls_avoided",
                "severity_capture_under_budget",
                "severity_reduction_ratio",
                "post_policy_violating_scenarios",
                "action_cost_proxy_mw",
            }.issubset(budget_metrics.columns)
        ),
        "screening_budget_multiseed_present": (
            screening_budget_multiseed_summary.get("rows") == 20
            and screening_budget_multiseed_summary.get("raw_rows") == 60
            and screening_budget_multiseed_summary.get("seeds") == config["evaluation_seeds"]
            and screening_budget_multiseed_summary.get("primary_budget_fraction") == 0.2
            and screening_budget_multiseed_summary.get("primary_ac_calls_mean") == 24.0
            and screening_budget_multiseed_summary.get("primary_ac_calls_avoided_mean") == 96.0
            and screening_budget_multiseed_summary.get("primary_severity_capture_mean", 0) > 0.3
            and screening_budget_multiseed_summary.get("random_severity_capture_mean", 1) < 0.25
            and screening_budget_multiseed_summary.get("severity_capture_gain_vs_random_mean", 0) > 0.1
            and screening_budget_multiseed_summary.get("primary_severity_reduction_ratio_mean", 0) > 0.19
            and screening_budget_multiseed_summary.get("primary_post_policy_violating_scenarios_mean", 999) < 90
            and len(screening_budget_multiseed_metrics) == 20
            and len(screening_budget_multiseed_raw) == 60
            and {
                "VoltGuard interval-risk",
                "LinDistFlow point-risk",
                "Oracle realized severity",
                "Random budget expectation",
            }.issubset(set(screening_budget_multiseed_metrics["method"]))
            and {
                "severity_capture_under_budget_mean",
                "severity_reduction_ratio_mean",
                "post_policy_violating_scenarios_mean",
                "post_policy_violating_buses_mean",
            }.issubset(screening_budget_multiseed_metrics.columns)
        ),
        "statistical_evidence_present": (
            statistical_evidence_summary.get("rows") == 20
            and statistical_evidence_summary.get("raw_rows") == 105
            and statistical_evidence_summary.get("bootstrap_draws") == 10000
            and statistical_evidence_summary.get("prediction_units") == 12
            and statistical_evidence_summary.get("prediction_rmse_delta_mean", 1) < 0
            and statistical_evidence_summary.get("prediction_rmse_better_fraction", 0) == 1.0
            and statistical_evidence_summary.get("budget_random_severity_capture_delta_mean", 0) > 0.1
            and statistical_evidence_summary.get("budget_random_severity_capture_better_fraction", 0) == 1.0
            and statistical_evidence_summary.get("budget_lindistflow_post_policy_bus_delta_mean", 1) < 0
            and statistical_evidence_summary.get("budget_lindistflow_post_policy_bus_better_fraction", 0) == 1.0
            and len(statistical_evidence_metrics) == 20
            and len(statistical_evidence_raw) == 105
            and {
                "main_33_69_split_seed_prediction",
                "multiseed_budgeted_ac_triage",
            }.issubset(set(statistical_evidence_metrics["experiment"]))
            and {
                "rmse",
                "avg_width",
                "recall",
                "false_alarm_rate",
                "missed_violations",
                "severity_capture_under_budget",
                "post_policy_violating_buses",
            }.issubset(set(statistical_evidence_metrics["metric"]))
            and {
                "delta_ci95_low",
                "delta_ci95_high",
                "better_unit_fraction",
                "all_units_better",
            }.issubset(statistical_evidence_metrics.columns)
        ),
        "candidate_action_screening_present": (
            candidate_action_summary.get("rows") == 14
            and candidate_action_summary.get("test_scenarios") == 120
            and candidate_action_summary.get("candidate_grid_size") == 9
            and candidate_action_summary.get("primary_top_k") == 3
            and candidate_action_summary.get("primary_candidate_ac_audits") == 360
            and candidate_action_summary.get("primary_candidate_ac_audits_avoided") == 720
            and candidate_action_summary.get("primary_audit_reduction_ratio") > 0.66
            and candidate_action_summary.get("primary_full_best_in_subset_rate") >= 0.9
            and candidate_action_summary.get("primary_extra_violating_scenarios_vs_full") == 0
            and candidate_action_summary.get("primary_extra_violating_buses_vs_full") == 0
            and candidate_action_summary.get("primary_action_cost_delta_vs_full_mw", 0) > 0
            and len(control_candidates) == 1080
            and len(candidate_action_scores) == 1080
            and len(candidate_action_raw) > 50000
            and {
                "policy",
                "top_k_candidates",
                "candidate_ac_audits",
                "candidate_ac_audits_avoided",
                "full_best_in_subset_rate",
                "extra_violating_scenarios_vs_full",
                "extra_violating_buses_vs_full",
                "action_cost_delta_vs_full_mw",
            }.issubset(candidate_action_metrics.columns)
            and int(
                candidate_action_metrics[
                    (candidate_action_metrics["policy"] == "LinDistFlow point-risk")
                    & (candidate_action_metrics["top_k_candidates"] == 3)
                ]["extra_violating_scenarios_vs_full"].iloc[0]
            )
            > 0
            and int(
                candidate_action_metrics[
                    (candidate_action_metrics["policy"] == "Cheapest-first")
                    & (candidate_action_metrics["top_k_candidates"] == 3)
                ]["extra_violating_scenarios_vs_full"].iloc[0]
            )
            >= 20
        ),
        "candidate_action_screening_multiseed_present": (
            candidate_action_multiseed_summary.get("rows") == 4
            and candidate_action_multiseed_summary.get("raw_rows") == 12
            and candidate_action_multiseed_summary.get("seeds") == config["evaluation_seeds"]
            and candidate_action_multiseed_summary.get("test_scenarios_per_seed") == 120
            and candidate_action_multiseed_summary.get("candidate_grid_size") == 9
            and candidate_action_multiseed_summary.get("top_k") == 3
            and candidate_action_multiseed_summary.get("primary_candidate_ac_audits_mean") == 360.0
            and candidate_action_multiseed_summary.get("primary_candidate_ac_audits_avoided_mean") == 720.0
            and candidate_action_multiseed_summary.get("primary_audit_reduction_ratio_mean", 0) > 0.66
            and candidate_action_multiseed_summary.get("primary_extra_violating_scenarios_vs_full_mean")
            == 0.0
            and candidate_action_multiseed_summary.get("primary_extra_violating_buses_vs_full_mean") == 0.0
            and candidate_action_multiseed_summary.get("primary_action_cost_delta_vs_full_mw_mean", 0) > 0
            and candidate_action_multiseed_summary.get("ldf_extra_violating_scenarios_vs_full_mean", 0) > 0
            and candidate_action_multiseed_summary.get("cheapest_extra_violating_scenarios_vs_full_mean", 0)
            > 20
            and candidate_action_multiseed_summary.get("ac_candidate_rows") == 3240
            and candidate_action_multiseed_summary.get("score_rows") == 3240
            and candidate_action_multiseed_summary.get("raw_prediction_rows", 0) > 160000
            and len(candidate_action_multiseed_metrics) == 4
            and len(candidate_action_multiseed_raw) == 12
            and len(candidate_action_multiseed_ac) == 3240
            and len(candidate_action_multiseed_scores) == 3240
            and len(candidate_action_multiseed_predictions) > 160000
            and {
                "policy",
                "candidate_ac_audits_mean",
                "candidate_ac_audits_avoided_mean",
                "extra_violating_scenarios_vs_full_mean",
                "extra_violating_buses_vs_full_mean",
                "action_cost_delta_vs_full_mw_mean",
            }.issubset(candidate_action_multiseed_metrics.columns)
        ),
        "action_cost_tradeoff_present": (
            action_cost_tradeoff_summary.get("rows") == 56
            and action_cost_tradeoff_summary.get("primary_top_k") == 3
            and action_cost_tradeoff_summary.get("primary_cost_weight") == 0.5
            and action_cost_tradeoff_summary.get("primary_candidate_ac_audits") == 360
            and action_cost_tradeoff_summary.get("primary_candidate_ac_audits_avoided") == 720
            and action_cost_tradeoff_summary.get("primary_extra_violating_scenarios_vs_full") == 0
            and action_cost_tradeoff_summary.get("primary_extra_violating_buses_vs_full") == 0
            and abs(action_cost_tradeoff_summary.get("primary_action_cost_delta_vs_full_mw", 1)) < 1e-9
            and action_cost_tradeoff_summary.get("primary_same_action_as_full_rate") == 1.0
            and action_cost_tradeoff_summary.get("risk_first_top3_action_cost_delta_vs_full_mw", 0) > 5.0
            and action_cost_tradeoff_summary.get("over_costed_top3_extra_violating_scenarios_vs_full") == 1
            and action_cost_tradeoff_summary.get("over_costed_top3_extra_violating_buses_vs_full") == 2
            and {
                "cost_weight",
                "top_k_candidates",
                "candidate_ac_audits",
                "candidate_ac_audits_avoided",
                "full_best_in_subset_rate",
                "extra_violating_scenarios_vs_full",
                "extra_violating_buses_vs_full",
                "action_cost_delta_vs_full_mw",
            }.issubset(action_cost_tradeoff_metrics.columns)
        ),
        "action_cost_tradeoff_multiseed_present": (
            action_cost_tradeoff_multiseed_summary.get("rows") == 56
            and action_cost_tradeoff_multiseed_summary.get("raw_rows") == 168
            and action_cost_tradeoff_multiseed_summary.get("seeds") == config["evaluation_seeds"]
            and action_cost_tradeoff_multiseed_summary.get("primary_top_k") == 3
            and action_cost_tradeoff_multiseed_summary.get("primary_cost_weight") == 0.5
            and action_cost_tradeoff_multiseed_summary.get("primary_candidate_ac_audits_mean") == 360.0
            and action_cost_tradeoff_multiseed_summary.get("primary_candidate_ac_audits_avoided_mean") == 720.0
            and action_cost_tradeoff_multiseed_summary.get("primary_extra_violating_scenarios_vs_full_mean")
            == 0.0
            and action_cost_tradeoff_multiseed_summary.get("primary_extra_violating_scenarios_vs_full_max")
            == 0.0
            and action_cost_tradeoff_multiseed_summary.get("primary_extra_violating_buses_vs_full_mean")
            == 0.0
            and action_cost_tradeoff_multiseed_summary.get("primary_extra_violating_buses_vs_full_max")
            == 0.0
            and action_cost_tradeoff_multiseed_summary.get("primary_action_cost_delta_vs_full_mw_mean", 999)
            < 0.2
            and action_cost_tradeoff_multiseed_summary.get("risk_first_top3_action_cost_delta_vs_full_mw_mean", 0)
            > 10.0
            and action_cost_tradeoff_multiseed_summary.get(
                "risk_first_top3_extra_violating_scenarios_vs_full_max", 1
            )
            == 0.0
            and action_cost_tradeoff_multiseed_summary.get(
                "over_costed_top3_extra_violating_scenarios_vs_full_mean", 0
            )
            > 0
            and action_cost_tradeoff_multiseed_summary.get(
                "over_costed_top3_extra_violating_buses_vs_full_mean", 0
            )
            > 0
            and len(action_cost_tradeoff_multiseed_metrics) == 56
            and len(action_cost_tradeoff_multiseed_raw) == 168
            and {
                "cost_weight",
                "top_k_candidates",
                "candidate_ac_audits_mean",
                "candidate_ac_audits_avoided_mean",
                "extra_violating_scenarios_vs_full_max",
                "extra_violating_buses_vs_full_max",
                "action_cost_delta_vs_full_mw_mean",
            }.issubset(action_cost_tradeoff_multiseed_metrics.columns)
        ),
        "runtime_operational_benchmark_present": (
            runtime_operational_summary.get("test_scenarios") == 120
            and runtime_operational_summary.get("full_ac_grid_candidate_actions") == 1080
            and runtime_operational_summary.get("online_screening_ms_per_scenario", 999) < 1.0
            and runtime_operational_summary.get("full_ac_grid_seconds", 0)
            > runtime_operational_summary.get("online_screening_seconds", 999)
            and runtime_operational_summary.get("budget20_speedup", 0) > 4.0
            and runtime_operational_summary.get("screen_then_ac_speedup", 0) > 1.0
            and {
                "workflow",
                "scenarios",
                "seconds",
                "ms_per_scenario",
                "speedup_vs_full_ac",
            }.issubset(runtime_operational_metrics.columns)
        ),
        "physics_consistency_audit_present": (
            physics_summary.get("rows") == 4
            and physics_summary.get("scenario_rows") == 480
            and physics_summary.get("ac_label_drop_rmse_mean", 1) < 0.001
            and physics_summary.get("voltguard_drop_rmse_mean", 1)
            < physics_summary.get("boosting_drop_rmse_mean", 0)
            and {
                "method",
                "variant",
                "drop_rmse_mean",
                "drop_mae_mean",
                "drop_max_abs_p95",
                "violating_only_drop_rmse",
            }.issubset(physics_metrics.columns)
        ),
        "high_pv_hosting_stress_present": (
            hosting_summary.get("scenarios") == 270
            and hosting_summary.get("converged_scenarios") == 270
            and hosting_summary.get("pre_overvoltage_scenarios", 0) > 0
            and hosting_summary.get("post_overvoltage_scenarios", 999)
            < hosting_summary.get("pre_overvoltage_scenarios", 0)
            and hosting_summary.get("post_overvoltage_buses", 999999)
            < hosting_summary.get("pre_overvoltage_buses", 0)
            and hosting_summary.get("curtailed_pv_mw_overvoltage", 0) > 0
            and {"33", "69"} == set(hosting_by_feeder["feeder"].astype(str))
        ),
        "high_pv_hosting_frontier_present": (
            hosting_frontier_summary.get("raw_rows") == 1620
            and hosting_frontier_summary.get("metric_rows") == 24
            and hosting_frontier_summary.get("scenarios") == 270
            and hosting_frontier_summary.get("initial_overvoltage_scenarios") == 132
            and hosting_frontier_summary.get("curtailment_grid") == config["hosting_stress_pv_curtail_grid"]
            and hosting_frontier_summary.get("primary_pv_curtail") == 0.5
            and hosting_frontier_summary.get("primary_overvoltage_scenarios", 999) == 43
            and hosting_frontier_summary.get("primary_overvoltage_buses", 999999) == 552
            and hosting_frontier_summary.get("primary_overvoltage_scenario_reduction_ratio", 0) > 0.65
            and hosting_frontier_summary.get("primary_overvoltage_bus_reduction_ratio", 0) > 0.75
            and hosting_frontier_summary.get("primary_accepted_pv_mw", 0) > 390
            and len(hosting_frontier_raw) == 1620
            and len(hosting_frontier_metrics) == 24
            and {"all_converged", "initial_overvoltage_only", "initial_overvoltage_by_feeder"}
            == set(hosting_frontier_metrics["population"])
            and {"33", "69"} == set(
                hosting_frontier_metrics.loc[
                    hosting_frontier_metrics["population"] == "initial_overvoltage_by_feeder",
                    "feeder",
                ]
                .astype(float)
                .astype(int)
                .astype(str)
            )
            and {
                "accepted_pv_mw",
                "curtailed_pv_mw",
                "overvoltage_scenario_reduction_ratio",
                "overvoltage_bus_reduction_ratio",
            }.issubset(hosting_frontier_metrics.columns)
        ),
        "energy_value_manuscript_tables": (
            "Screened-safe ratio" in manuscript_text
            and "Accepted PV proxy" in manuscript_text
            and "Relieved load proxy" in manuscript_text
            and "same screening-value audit is repeated over the three random seeds" in manuscript_text
            and "primary-level screening audit across the four split" in manuscript_text
            and "bidirectional transfer audit" in manuscript_text
            and "recalibration audit" in manuscript_text.lower()
            and "PV-shift recalibration protocol" in manuscript_text
            and "screened-safe releases fall to 49.67 scenarios" in manuscript_text
            and "paired seed deltas" in manuscript_text.lower()
            and "feature/residual ablation" in manuscript_text.lower()
            and "ev-conditioned ablation" in manuscript_text.lower()
            and "Forecast-Noise Robustness" in manuscript_text
            and "Screened-Safe Release Audit" in manuscript_text
            and "three random seeds" in manuscript_text
            and "Risk-Stratified Calibration" in manuscript_text
            and "Calibration-Budget Sensitivity" in manuscript_text
            and "Asymmetric Conformal" in manuscript_text
            and "Screening-Budget Triage" in manuscript_text
            and "same budgeted triage calculation is then repeated over the three random" in manuscript_text.lower()
            and "Candidate-Action Screening" in manuscript_text
            and "top-three candidate-pruning audit across the three random seeds" in manuscript_text
            and "Risk-Cost Candidate-Action Tradeoff" in manuscript_text
            and "risk-cost audit is also repeated over the same three random seeds" in manuscript_text
            and "Operational Runtime Benchmark" in manuscript_text
            and "Scenario Risk-Ranking Quality" in manuscript_text
            and "Branch-Level Physics Consistency" in manuscript_text
            and "High-PV AC stress" in manuscript_text
            and "High-PV hosting frontier" in manuscript_text
        ),
        "three_submission_versions_distinct": (
            ecmx_submission_text != ecm_submission_text
            and ecmx_submission_text != oajpe_submission_text
            and ecm_submission_text != oajpe_submission_text
            and "VoltGuard: Topology-Aware Voltage-Risk Screening with Conformal Calibration" in ecmx_submission_text
            and "VoltGuard-ECM: A DMS Integration Architecture" in ecm_submission_text
            and "LinDistFlow-Quantile Screen: A Baseline Heuristic" in oajpe_submission_text
            and "Submission Metadata" not in ecmx_submission_text
            and "Submission Metadata" not in ecm_submission_text
            and "Submission Metadata" not in oajpe_submission_text
            and "Figure Placeholders and Descriptions" not in ecmx_submission_text
            and "Figure Placeholders and Descriptions" not in ecm_submission_text
            and "Figure Placeholders and Descriptions" not in oajpe_submission_text
            and "Author and Declaration Readiness Gate" not in ecmx_submission_text
            and "Author and Declaration Readiness Gate" not in ecm_submission_text
            and "Author and Declaration Readiness Gate" not in oajpe_submission_text
            and len(ecmx_submission_text.splitlines()) > len(ecm_submission_text.splitlines())
            and len(ecm_submission_text.splitlines()) > len(oajpe_submission_text.splitlines())
        ),
        "variant_strategy_present": (
            "Three Independent Manuscript Questions" in variant_strategy_text
            and "ECM:X method paper" in variant_strategy_text
            and "ECM DMS integration paper" in variant_strategy_text
            and "OAJPE baseline note" in variant_strategy_text
            and "Do not submit more than one draft" in variant_strategy_text
            and "Forbidden overlap" in variant_strategy_text
            and "No residual learner" in variant_strategy_text
        ),
        "ecm_engineering_layer": (
            "DMS Integration Architecture" in ecm_source_text
            and "input data contract" in ecm_source_text
            and "queue semantics" in ecm_source_text.lower()
            and "fallback rules" in ecm_source_text
            and "Audit record" in ecm_source_text
            and "does not reuse" in ecm_source_text
            and not text_contains_any(
                ecm_source_text,
                ["0.00011", "0.93660", "27.33", "27 of 120", "avoids 96", "5.00", "206.98", "0.254"],
            )
            and "per-family calibration analysis" not in ecm_source_text.lower()
            and "topology-held-out" not in ecm_source_text.lower()
            and "distribution-free" not in ecm_source_text.lower()
        ),
        "oajpe_minimal_layer": (
            "two transparent components" in oajpe_source_text
            and "LinDistFlow Backbone" in oajpe_source_text
            and "One Global Quantile" in oajpe_source_text
            and "RMSE" in oajpe_source_text
            and "scenario-level recall" in oajpe_source_text
            and "0.00140" in oajpe_source_text
            and "0.91356" in oajpe_source_text
            and "0.00474" in oajpe_source_text
            and "No residual learner is fit" in oajpe_source_text
            and "Baseline Design Rationale" in oajpe_source_text
            and "Comparison with VoltGuard" in oajpe_source_text
            and "Flat 1.0 p.u. + global quantile" in oajpe_source_text
            and "Historical bus envelope" in oajpe_source_text
            and "Linear sensitivity regression" in oajpe_source_text
            and "0.93660" in oajpe_source_text
            and "0.94984" not in oajpe_source_text
            and "0.00053" not in oajpe_source_text
            and "27.33" not in oajpe_source_text
            and "27 of 120" not in oajpe_source_text
            and "avoids 96" not in oajpe_source_text
            and "VoltGuard" in oajpe_source_text
            and "per-family calibration analysis" not in oajpe_source_text.lower()
            and "topology-held-out" not in oajpe_source_text.lower()
            and "PV-shift" not in oajpe_source_text
            and "Neural graph residual ablation" not in oajpe_source_text
        ),
        "formal_manuscripts_deoverlapped": (
            not text_contains_any(
                ecm_submission_text,
                ["0.00011", "0.93660", "27.33", "27 of 120", "206.98", "0.254", "5.00x", "avoids 96"],
            )
            and not text_contains_any(
                oajpe_submission_text,
                ["0.94984", "0.00053", "27.33", "27 of 120", "avoids 96"],
            )
            and not text_contains_any(
                ecmx_submission_text,
                [
                    "Candidate-Action Screening Audit",
                    "Risk-Cost Candidate-Action Tradeoff",
                    "Consolidated Energy-Management Frontier",
                    "Operational Runtime Benchmark",
                    "Scenario Risk-Ranking Quality",
                ],
            )
            and "LinDistFlow-only" in oajpe_submission_text
            and "DMS integration architecture" in ecm_submission_text
        ),
        "professional_review_requirements_present": (
            "Scope and Companion-Paper Positioning" in manuscript_text
            and "Comparison with Competing Screening Methods" in ecmx_submission_text
            and "GB-quantile" in ecmx_submission_text
            and "GP-UQ" in ecmx_submission_text
            and set(review_baseline_metrics["method"])
            == {"Gradient-boosted quantile regression", "Gaussian-process UQ baseline"}
            and "Expanded IEEE 118-Bus Stress Audit" in ecmx_submission_text
            and "Failure Mode Analysis" in ecmx_submission_text
            and "Computational Cost and Breakeven Analysis" in ecmx_submission_text
            and "Model maintenance" in manuscript_text
            and "Real-world validation" in manuscript_text
            and "Acronym Table" in ecm_submission_text
            and "DMS Integration Standards and Protocols" in ecm_submission_text
            and "Generalization to Other Screening Methods" in ecm_submission_text
            and "Stakeholder Requirements" in ecm_submission_text
            and "Algorithm 1: Input validation and queue assignment" in ecm_submission_text
            and "Algorithm 2: Fallback rule evaluation" in ecm_submission_text
            and "Algorithm 3: Rolling drift audit" in ecm_submission_text
            and "Prototype Demonstration" in ecm_submission_text
            and dms_prototype_summary.get("simulated_cycles", 0) >= 1000
            and len(dms_prototype_log) >= 1000
            and "Baseline Design Rationale" in oajpe_submission_text
            and "Comparison with VoltGuard" in oajpe_submission_text
            and len(baseline_design_metrics) == 4
            and "Code and Data Availability" in ecmx_submission_text
            and "Code and Data Availability" in ecm_submission_text
            and "Code and Data Availability" in oajpe_submission_text
            and "Zhaosiqiang/voltguard-voltage-risk-screening" in ecmx_submission_text
            and "Zhaosiqiang/voltguard-voltage-risk-screening" in ecm_submission_text
            and "Zhaosiqiang/voltguard-voltage-risk-screening" in oajpe_submission_text
            and "v1.0.0-submission" in ecmx_submission_text
            and "v1.0.0-submission" in ecm_submission_text
            and "v1.0.0-submission" in oajpe_submission_text
            and "10.5281/zenodo.21149702" in ecmx_submission_text
            and "10.5281/zenodo.21149702" in ecm_submission_text
            and "10.5281/zenodo.21149702" in oajpe_submission_text
            and (ROOT / "GITHUB_ZENODO_RELEASE_CHECKLIST.md").exists()
            and (ROOT / "CITATION.cff").exists()
            and (ROOT / ".zenodo.json").exists()
            and (ROOT / "LICENSE").exists()
            and "voltguard-voltage-risk-screening" in (ROOT / "GITHUB_ZENODO_RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
            and "Siqiang" in (ROOT / "CITATION.cff").read_text(encoding="utf-8")
            and "10.5281/zenodo.21149702" in (ROOT / "CITATION.cff").read_text(encoding="utf-8")
            and "Zhao, Siqiang" in (ROOT / ".zenodo.json").read_text(encoding="utf-8")
            and "10.5281/zenodo.21149702" in (ROOT / ".zenodo.json").read_text(encoding="utf-8")
            and "MIT License" in (ROOT / "LICENSE").read_text(encoding="utf-8")
            and "Professional Review Action Matrix" in professional_review_action_text
        ),
        "ancillaries_energy_management_framing": (
            "accepted PV" in ancillaries_text
            and "relieved-load" in ancillaries_text
            and "51 of 120" in ancillaries_text
            and "not as a replacement for AC optimal power flow" in ancillaries_text
        ),
        "ecmx_highlights_ready": (
            3 <= len(highlights) <= 5
            and all(len(item) <= 85 for item in highlights)
            and any("renewable-hosting" in item for item in highlights)
        ),
        "ecm_highlights_ready": (
            3 <= len(ecm_highlights) <= 5
            and all(len(item) <= 85 for item in ecm_highlights)
            and any("DMS" in item for item in ecm_highlights)
        ),
        "journal_specific_format_present": (
            "\\documentclass[\n  preprint,12pt]{elsarticle}" in ecmx_tex_text
            and "\\documentclass[\n  preprint,12pt]{elsarticle}" in ecm_tex_text
            and "\\documentclass[\n  journal]{IEEEtran}" in oajpe_tex_text
            and "\\usepackage[margin=1in]{geometry}" not in oajpe_tex_text
            and "\\section{Introduction}" in ecmx_tex_text
            and "\\section{Engineering Motivation}" in ecm_tex_text
            and "\\section{Introduction}" in oajpe_tex_text
            and "\\section*{Abstract}" in ecmx_tex_text
            and "\\section*{Abstract}" in ecm_tex_text
            and "\\section*{Abstract}" in oajpe_tex_text
            and "\\section*{Index Terms}" in oajpe_tex_text
            and "\\section*{References}" in ecmx_tex_text
            and "\\section*{References}" in ecm_tex_text
            and "\\section*{References}" in oajpe_tex_text
            and "# Figures and Graphical Abstract" not in ecmx_submission_text
            and "# Figures and Graphical Abstract" not in ecm_submission_text
            and "# Figures and Graphical Abstract" not in oajpe_submission_text
        ),
        "svg_figures_generated_and_inserted": (
            figure_manifest.get("canonical_format") == "svg"
            and figure_manifest.get("latex_companion_format") == "pdf"
            and len(figure_manifest.get("figures", [])) == len(REQUIRED_FIGURES)
            and all((ROOT / "figures" / f"{name}.svg").exists() for name in REQUIRED_FIGURES)
            and all((ROOT / "figures" / f"{name}.pdf").exists() for name in REQUIRED_FIGURES)
            and all((ROOT / "figures" / f"{name}.svg").stat().st_size > 1000 for name in REQUIRED_FIGURES)
            and all((ROOT / "figures" / f"{name}.pdf").stat().st_size > 1000 for name in REQUIRED_FIGURES)
            and "figures/fig01_graphical_abstract_workflow.pdf" in ecmx_submission_text
            and "figures/fig05_shift_generalization.pdf" in ecmx_submission_text
            and "figures/fig06_operating_value.pdf" not in ecmx_submission_text
            and "figures/fig10_risk_ranking_quality.pdf" not in ecmx_submission_text
            and "figures/fig01_graphical_abstract_workflow.pdf" in ecm_submission_text
            and "figures/fig02_feeders_and_splits.pdf" not in ecm_submission_text
            and "figures/fig08_screening_budget.pdf" not in ecm_submission_text
            and "figures/fig09_candidate_action_screening.pdf" not in ecm_submission_text
            and "figures/fig10_risk_ranking_quality.pdf" not in ecm_submission_text
            and "figures/fig11_oajpe_lindistflow_quantile_pipeline.pdf" in oajpe_submission_text
            and "figures/fig12_oajpe_minimal_performance.pdf" in oajpe_submission_text
            and "figures/fig02_feeders_and_splits.pdf" not in oajpe_submission_text
            and "figures/fig03_conformal_ablation.pdf" not in oajpe_submission_text
        ),
        "figures_embedded_in_body": (
            all_figures_before_references(ecmx_submission_text, REQUIRED_FIGURES[:5])
            and all_figures_before_references(
                ecm_submission_text,
                ["fig01_graphical_abstract_workflow"],
            )
            and all_figures_before_references(
                oajpe_submission_text,
                [
                    "fig11_oajpe_lindistflow_quantile_pipeline",
                    "fig12_oajpe_minimal_performance",
                ],
            )
            and token_between(
                ecmx_submission_text,
                "figures/fig01_graphical_abstract_workflow.pdf",
                "# Introduction",
                "# Related Work",
            )
            and token_between(
                ecmx_submission_text,
                "figures/fig02_feeders_and_splits.pdf",
                "# Experimental Design",
                "# Results",
            )
            and token_between(
                ecmx_submission_text,
                "figures/fig03_conformal_ablation.pdf",
                "## Conformal Ablation",
                "## Calibration-Budget Sensitivity",
            )
            and token_between(
                ecmx_submission_text,
                "figures/fig04_per_family_calibration.pdf",
                "## Per-Family Calibration Analysis",
                "## Risk-Stratified Calibration and Screening",
            )
            and token_between(
                ecmx_submission_text,
                "figures/fig05_shift_generalization.pdf",
                "## Shift and Scenario-Level Results",
                "# Discussion",
            )
            and token_between(
                ecm_submission_text,
                "figures/fig01_graphical_abstract_workflow.pdf",
                "# System Integration Architecture",
                "# Queue Semantics",
            )
            and token_between(
                oajpe_submission_text,
                "figures/fig11_oajpe_lindistflow_quantile_pipeline.pdf",
                "# Baseline Method",
                "# Experimental Protocol",
            )
            and token_between(
                oajpe_submission_text,
                "figures/fig12_oajpe_minimal_performance.pdf",
                "# Results",
                "# Boundary and Use",
            )
        ),
        "captions_do_not_duplicate_figure_numbers": not text_contains_any(
            ecmx_submission_text + ecm_submission_text + oajpe_submission_text,
            [f"![Figure {idx}." for idx in range(1, 13)],
        ),
        "captions_hide_internal_figure_paths": not text_contains_any(
            ecmx_submission_text + ecm_submission_text + oajpe_submission_text,
            ["Canonical SVG:", "fig01_graphical_abstract_workflow.svg", "fig11_oajpe_lindistflow_quantile_pipeline.svg"],
        ),
        "oajpe_pipeline_figure_is_double_column": (
            "\\begin{figure*}[t]" in oajpe_submission_text
            and "\\includegraphics[width=0.94\\textwidth]{figures/fig11_oajpe_lindistflow_quantile_pipeline.pdf}" in oajpe_submission_text
        ),
        "oajpe_single_column_figures_stay_in_column": (
            "\\includegraphics[width=\\linewidth]{figures/fig12_oajpe_minimal_performance.pdf}" in oajpe_submission_text
            and "\\includegraphics[width=\\linewidth]{figures/fig02_feeders_and_splits.pdf}" not in oajpe_submission_text
            and "fig02_feeders_and_splits.pdf){#fig:fig02_feeders_and_splits width=110%}" not in oajpe_submission_text
            and "fig12_oajpe_minimal_performance.pdf){#fig:fig12_oajpe_minimal_performance width=110%}" not in oajpe_submission_text
        ),
        "multipanel_captions_describe_subfigures": all(
            figure_caption_has_subfigure_labels(
                ecmx_submission_text + "\n" + ecm_submission_text + "\n" + oajpe_submission_text,
                name,
                labels,
            )
            if name in ecmx_submission_text + "\n" + ecm_submission_text + "\n" + oajpe_submission_text
            else True
            for name, labels in MULTIPANEL_FIGURE_LABELS.items()
        ),
        "svg_figures_title_free_and_text_consistent": (
            len(svg_texts) == len(REQUIRED_FIGURES)
            and all(
                all(
                    forbidden not in text
                    for forbidden in [
                        "Figure 1.",
                        "Figure 2.",
                        "Figure 3.",
                        "Figure 4.",
                        "Figure 5.",
                        "Figure 6.",
                        "Figure 7.",
                        "Figure 8.",
                        "Figure 9.",
                        "Figure 10.",
                        "Figure 11.",
                        "Figure 12.",
                        "VoltGuard calibrated voltage-risk screening",
                        "LinDistFlow-Quantile baseline screen",
                    ]
                )
                for text in svg_texts.values()
            )
            and all(
                any(font in text for font in ["Times New Roman", "Times", "DejaVu Serif"])
                for text in svg_texts.values()
            )
            and all("DejaVu Sans" not in text for text in svg_texts.values())
            and not any(has_nonzero_text_rotation(text) for text in svg_texts.values())
            and not any(has_curved_arrow_path(text) for text in svg_texts.values())
            and "active_distribution_scenario_inset" not in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and "DER forecasts + topology + voltage-risk hot spots" in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and "data:image/png;base64," in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'width="842" height="428"' in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'width="712" height="378"' not in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'width="632" height="334"' not in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'width="560" height="292"' not in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'M976 302 H1000' in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'M976 302 H1000" stroke="#68707d" stroke-width="3.2" fill="none" marker-end="url(#smallArrow)"' in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'M815 265 H830' not in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'M735 260 H750' not in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'M682 260 H716' not in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and 'M1652 360 V458' in svg_texts.get(
                "fig01_graphical_abstract_workflow", ""
            )
            and "Forecast scenarios" in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and "Bias" not in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and "data:image/png;base64," in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'width="510" height="300"' in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'width="450" height="264"' not in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'width="390" height="228"' not in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'font-size="25"' in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'M620 248 H634' in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'M620 248 H634" stroke="#68707d" stroke-width="3.2" fill="none" marker-end="url(#smallArrow)"' in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'M558 240 H572' not in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'M510 240 H558' not in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'M1298 300 V382' in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'x="648" y="382" width="850"' in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and 'M1192 438 H1254' in svg_texts.get(
                "fig11_oajpe_lindistflow_quantile_pipeline", ""
            )
            and all(
                all(label in svg_texts.get(name, "") for label in labels)
                for name, labels in MULTIPANEL_FIGURE_LABELS.items()
            )
        ),
        "journal_format_audit_present": (
            "Energy Conversion and Management: X" in journal_format_text
            and "Energy Conversion and Management" in journal_format_text
            and "IEEE Open Access Journal of Power and Energy" in journal_format_text
            and "elsarticle" in journal_format_text
            and "IEEEtran" in journal_format_text
            and "150--200 word" in journal_format_text
        ),
        "ecmx_cover_letter_ready": (
            "Energy Conversion and Management: X" in cover_letter_text
            and "not as a replacement for AC optimal power flow" in cover_letter_text
            and "funding" not in cover_letter_text.lower()
            and "suggested reviewer" not in cover_letter_text.lower()
        ),
        "ecmx_readiness_checklist_present": (
            "Abstract length" in readiness_text
            and "Highlights" in readiness_text
            and "Data/code availability" in readiness_text
            and "manual_input_required" in readiness_text
            and "ecmx_upload_input_packet.md" in readiness_text
        ),
        "ecmx_upload_input_packet_present": (
            "Energy Conversion and Management: X" in upload_packet_text
            and "Elsevier declaration of competing interest tool" in upload_packet_text
            and "531 by 1328 pixels" in upload_packet_text
            and "repository or archive URL" in upload_packet_text
            and "Generative AI / Tool Use" in upload_packet_text
            and "Do not submit while" in upload_packet_text
            and "submission_manuscript_ecmx.md" in upload_packet_text
        ),
        "official_venue_sources_present": (
            "Live public-page spot check on 2026-07-02" in venue_source_text
            and "https://www.sciencedirect.com/journal/energy-conversion-and-management-x/about/insights"
            in venue_source_text
            and "https://www.sciencedirect.com/journal/energy-and-ai/about/insights" in venue_source_text
            and "https://www.sciencedirect.com/journal/advances-in-applied-energy/about/insights"
            in venue_source_text
            and "https://www.sciencedirect.com/journal/applied-energy/about/insights" in venue_source_text
            and "Do not use search-engine snippets" in venue_source_text
            and "ScienceDirect journal and Journal Insights pages" in venue_matrix_text
            and "2026-07-02" in venue_matrix_text
            and "Venue metrics in this file were checked on 2026-07-02" in submission_strategy_text
        ),
        "claim_evidence_matrix_present": (
            "Claim" in claim_matrix_text
            and "Evidence artifact" in claim_matrix_text
            and "Reviewer risk" in claim_matrix_text
            and "Do Not Claim" in claim_matrix_text
            and "Energy Conversion and Management: X" in claim_matrix_text
            and "not an AC feasibility certificate" in claim_matrix_text
            and "Neural graph residual" in claim_matrix_text
            and "topology-held-out" in claim_matrix_text
            and "family recalibration" in claim_matrix_text
            and "calibration_budget_sensitivity_metrics.md" in claim_matrix_text
            and "forecast_noise_robustness_metrics.md" in claim_matrix_text
            and "pv_shift_recalibration_metrics.md" in claim_matrix_text
            and "pv_shift_recalibration_energy_value_metrics.md" in claim_matrix_text
            and "screening layer" in claim_matrix_text
            and "energy_management_frontier_metrics.md" in claim_matrix_text
            and "risk_stratified_calibration_bus.md" in claim_matrix_text
            and "asymmetric_conformal_metrics.md" in claim_matrix_text
            and "model_voltage_screening_metrics.md" in claim_matrix_text
            and "physics_consistency_audit.md" in claim_matrix_text
            and "screening_budget_metrics.md" in claim_matrix_text
            and "screening_budget_multiseed_metrics.md" in claim_matrix_text
            and "statistical_evidence_metrics.md" in claim_matrix_text
            and "shift_energy_management_value_metrics.md" in claim_matrix_text
            and "topology_transfer_bidirectional_metrics.md" in claim_matrix_text
            and "candidate_action_screening_metrics.md" in claim_matrix_text
            and "candidate_action_screening_multiseed_metrics.md" in claim_matrix_text
            and "action_cost_tradeoff_metrics.md" in claim_matrix_text
            and "action_cost_tradeoff_multiseed_metrics.md" in claim_matrix_text
            and "high_pv_hosting_frontier_metrics.md" in claim_matrix_text
        ),
        "numbered_references_present": (
            references_text.count("\n[") >= 10
            and ("to be " + "replaced") not in references_text.lower()
            and "[1]" in manuscript_text
            and ("[10,11]" in manuscript_text or "[11]" in manuscript_text)
        ),
        "reproducibility_manifest_present": (
            manifest.get("target_route") == "Energy Conversion and Management: X"
            and len(manifest.get("result_files", [])) >= 19
            and not any(item.get("path") == "experiments/results/project_validation_summary.json" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/raw_predictions_random_seed7.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/paired_seed_delta_summary.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/feature_residual_ablation.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/ev_conditioning_ablation.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/energy_management_value_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/energy_management_value_multiseed_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/energy_management_frontier_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/shift_energy_management_value_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/topology_transfer_bidirectional_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/screened_safe_release_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/screened_safe_release_multiseed_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/family_recalibration_audit.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/forecast_noise_robustness_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/pv_shift_recalibration_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/pv_shift_recalibration_energy_value_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/risk_stratified_calibration_bus.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/risk_stratified_calibration_scenario.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/calibration_budget_sensitivity_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/asymmetric_conformal_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/screening_budget_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/screening_budget_multiseed_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/screening_budget_multiseed_raw.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/statistical_evidence_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/statistical_evidence_raw.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/candidate_action_screening_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/candidate_action_screening_multiseed_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/control_grid_search_candidate_actions.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/action_cost_tradeoff_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/action_cost_tradeoff_multiseed_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/runtime_operational_benchmark.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/scenario_risk_ranking_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/physics_consistency_audit.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/high_pv_hosting_stress_by_feeder.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/high_pv_hosting_frontier_metrics.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "experiments/results/high_pv_hosting_frontier_raw.csv" for item in manifest.get("result_files", []))
            and any(item.get("path") == "ecmx_upload_input_packet.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "journal_format_audit.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "ecm_highlights.txt" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "figures/figure_manifest.json" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "figures/fig01_graphical_abstract_workflow.svg" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "figures/fig12_oajpe_minimal_performance.svg" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "claim_evidence_matrix.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "submission_variant_strategy.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "manuscript_ecm_engineering.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "manuscript_oajpe_minimal.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "submission_manuscript_ecm.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "submission_manuscript_oajpe.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "venue_source_audit.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "submission_strategy.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "high_impact_venue_matrix.md" for item in manifest.get("submission_files", []))
            and any(item.get("path") == "submission_compile_report.md" for item in manifest.get("submission_files", []))
        ),
        "completion_audit_ecmx_scope": (
            "Energy-management value" in audit_text
            and "shift_energy_management_value_metrics.md/.csv" in audit_text
            and "ECM:X route" in audit_text
            and "fallback, not first target" in audit_text
            and "Claim/evidence/reviewer-risk control" in audit_text
            and "Forecast-noise robustness" in audit_text
            and "PV-shift recalibration audit" in audit_text
            and "pv_shift_recalibration_energy_value_metrics.md/.csv" in audit_text
            and "energy_management_frontier_metrics.md/.csv" in audit_text
            and "topology_transfer_bidirectional_metrics.md/.csv" in audit_text
            and "Risk-stratified boundary audit" in audit_text
            and "Calibration-budget sensitivity" in audit_text
            and "Asymmetric conformal audit" in audit_text
            and "Candidate-action AC-audit pruning" in audit_text
            and "screening_budget_multiseed_metrics.md/.csv" in audit_text
            and "statistical_evidence_metrics.md/.csv" in audit_text
            and "candidate_action_screening_multiseed_metrics.md/.csv" in audit_text
            and "Risk-cost action tradeoff" in audit_text
            and "action_cost_tradeoff_multiseed_metrics.md/.csv" in audit_text
            and "High-PV hosting frontier" in audit_text
            and "high_pv_hosting_frontier_metrics.md/.csv" in audit_text
        ),
        "abstract_under_250_words": len(abstract_words) <= 250,
        "approved_scenario_inset_asset_present": (
            (ROOT / "figures" / "assets" / "active_distribution_scenario_inset.png").exists()
            and (ROOT / "figures" / "assets" / "active_distribution_scenario_inset.png").stat().st_size > 100000
        ),
        "no_raster_article_image_files": len(raster_article_images) == 0,
        "title_no_graph_core": "Graph Residual Learning" not in manuscript_text.splitlines()[0],
        "no_development_phrases": not contains_any(
            manuscript,
            ["if time " + "allows", "plan" + "ned " + "experiments", "inten" + "ded " + "contribution"],
        ),
        "submission_pdf_exists": ecmx_pdf.exists() and ecm_pdf.exists() and oajpe_pdf.exists(),
        "submission_pdf_current": ecmx_pdf.exists()
        and ecmx_tex.exists()
        and ecm_pdf.exists()
        and ecm_tex.exists()
        and oajpe_pdf.exists()
        and oajpe_tex.exists()
        and ecmx_pdf.stat().st_mtime >= ecmx_tex.stat().st_mtime
        and ecm_pdf.stat().st_mtime >= ecm_tex.stat().st_mtime
        and oajpe_pdf.stat().st_mtime >= oajpe_tex.stat().st_mtime,
        "submission_sources_current": ecmx_md.exists()
        and ecmx_tex.exists()
        and ecm_md.exists()
        and ecm_tex.exists()
        and oajpe_md.exists()
        and oajpe_tex.exists()
        and ecmx_md.stat().st_mtime >= manuscript.stat().st_mtime
        and ecm_md.stat().st_mtime >= (ROOT / "manuscript_ecm_engineering.md").stat().st_mtime
        and oajpe_md.stat().st_mtime >= (ROOT / "manuscript_oajpe_minimal.md").stat().st_mtime
        and ecmx_tex.stat().st_mtime >= ecmx_md.stat().st_mtime
        and ecm_tex.stat().st_mtime >= ecm_md.stat().st_mtime
        and oajpe_tex.stat().st_mtime >= oajpe_md.stat().st_mtime,
    }
    status = "pass" if not missing and all(value for key, value in checks.items() if key != "missing_files") else "fail"
    out = {"status": status, "checks": checks}
    (RESULTS / "project_validation_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
