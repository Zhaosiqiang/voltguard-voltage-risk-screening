# VoltGuard: Topology-Aware Voltage-Risk Screening with Conformal Calibration for Active Distribution Networks

## Abstract

High photovoltaic penetration, electric-vehicle charging, and flexible demand
make voltage-risk screening in active distribution networks increasingly
uncertain. VoltGuard provides a calibrated screening layer that combines a
squared-voltage LinDistFlow physical backbone, topology-aware residual
learning, and topology/PV/loading conditioned split conformal calibration. The
method converts pre-dispatch operating forecasts into voltage-risk intervals
that are sharp enough for scenario triage while maintaining high recall of
voltage-limit crossings. Experiments on IEEE 33-bus and IEEE 69-bus
distribution feeders, with an expanded IEEE 118-bus stress audit, show that
topology/PV/loading conditioned calibration improves the
coverage-sharpness-risk tradeoff relative to global conformal calibration,
tree-based point screens, and a neural graph residual ablation. On the
representative 33/69 random split, VoltGuard achieves 0.00011 p.u. RMSE,
93.66% empirical coverage for nominal 90% intervals, 99.89% bus-level
violation recall, and one missed bus-level violation. Across three random
seeds, the method reduces mean missed violations from 1.67 to 0.33 while
cutting mean interval width from 0.00127 to 0.00049 p.u. Runtime measurements
show 0.254 ms/scenario online screening versus 1725 ms/scenario for the
AC-audited grid-search backend, making VoltGuard a practical front end for
prioritizing downstream AC analysis.

## 1. Introduction

Active distribution networks are increasingly operated close to voltage limits
while being asked to host more renewable generation. Rooftop PV,
electric-vehicle charging, flexible loads, storage, and feeder switching create
operating points that vary faster than classical planning margins were designed
to handle. Voltage violations are costly in both directions: undervoltage
degrades service quality and equipment operation, whereas overvoltage can force
renewable curtailment or protection actions. The resulting problem is not only
a voltage-estimation problem: operators need calibrated uncertainty around
voltage-risk estimates before deciding which scenarios deserve downstream AC
analysis.

Machine-learning voltage predictors are attractive because they can rapidly map
forecasts and pseudo-measurements to voltage estimates. However, point accuracy
is not enough for operation. A predictor with low RMSE can still miss rare
voltage-limit crossings, and a globally conservative interval can produce so
many false alarms that the operator no longer trusts it. The useful operational
object is therefore a calibrated voltage-risk interval: an interval that is
sharp enough to screen many safe scenarios, yet conservative enough to reduce
missed violations near the 0.95-1.05 p.u. operating band.

This paper frames the task as calibrated voltage-risk screening. The proposed
method, VoltGuard, uses a LinDistFlow physical backbone to encode feeder
structure, learns a topology-aware residual correction from available operating
features, and then uses split conformal calibration to convert residual errors
into voltage intervals. The contribution is positive and operational: a fast,
auditable screen that ranks scenarios and buses before AC analysis is invoked.

The contribution is intentionally not "a stronger GNN." A lightweight neural
graph residual is included as an ablation, but the selected estimator is the
topology-aware residual learner with conditioned conformal calibration because
it gives the best risk-sharpness tradeoff in the executed experiments.

The paper makes three contributions:

1. A reproducible physics-informed topology-aware residual model that corrects
   a squared-voltage LinDistFlow backbone using only operating information
   available before AC labels are observed.
2. A topology/PV/loading conditioned split conformal calibration procedure with
   shrinkage fallback for voltage-risk intervals.
3. A focused screening evaluation on IEEE 33-bus and IEEE 69-bus distribution
   feeders showing how calibrated intervals affect coverage, interval width,
   false alarms, and missed-voltage-risk behavior.

The remaining audits, including EV-conditioning sensitivity, calibration-budget
checks, candidate-action pruning, and high-PV hosting stress, are supporting
application extensions. They are not used to define the central method claim.

### 1.1 Scope and Companion-Paper Positioning

This manuscript is the core screening-method paper. A companion DMS integration
paper specifies deployment contracts, queue semantics, fallback rules, and
operator audit records for using calibrated voltage-risk screens in control
centers. A separate LinDistFlow-global-quantile note defines a minimal
reference baseline. The three papers are parallel companion studies: this
paper answers how to estimate calibrated voltage-risk intervals, the DMS paper
answers how such intervals should be embedded in operations, and the baseline
note answers what a transparent physical proxy plus one pooled quantile can
achieve.

VoltGuard gives calibrated voltage-risk intervals under a stated
feeder/scenario/split/calibration protocol. It complements AC power flow, OPF,
and MPC by deciding which scenarios deserve immediate downstream analysis. AC
feasibility, final dispatch, protection action, and closed-loop control remain
the responsibility of those downstream tools.

## 2. Related Work

Classical distribution-voltage assessment uses AC power flow, distribution
state estimation, optimal power flow, Volt-VAR control, and conservative
operating margins. Distribution feeder reconfiguration and DistFlow-style
approximations trace back to radial-feeder power-flow models used for loss
reduction and load balancing [1]. LinDistFlow and related approximations are
valuable because they expose how downstream active and reactive power flows
drive voltage drops. Their accuracy degrades under losses, reverse power flow,
unmodeled imbalance, and uncertain injections, but they remain useful physical
backbones for fast screening. OPF and distributed control remain the stronger
corrective layers when an operating point requires actual dispatch decisions
[2,3].

Physics-informed learning for power systems embeds network equations, line
parameters, topology, or power-flow residuals into data-driven predictors. This
improves interpretability and can reduce the burden on a black-box model.
Recent physics-informed graph learning work for power-system state estimation
also illustrates the value of combining electrical structure with learnable
corrections [4]. In this work, the residual target is deliberately smaller than
direct voltage prediction: the learner corrects a physical voltage proxy rather
than replacing feeder physics.

Graph neural networks are natural for power grids because buses and lines form
a graph. General graph-convolution and inductive representation-learning
methods provide the modeling background for message passing on networks [5,6].
Many grid-learning studies emphasize point prediction, state estimation, or OPF
acceleration. This paper treats graph-neural modeling as relevant background
but not as the main claim. The executed neural graph residual is retained as an
ablation and is not used to justify the title or contribution.

Conformal prediction converts arbitrary predictors into calibrated prediction
sets or intervals under exchangeability assumptions [7,8]. Conformalized
quantile regression further shows why interval efficiency matters, not only
nominal coverage [9]. Recent conformalized GNN work highlights two difficulties
that matter here: graph-structured samples may not be exchangeable in the usual
i.i.d. sense, and intervals can become too wide if calibration ignores topology
or operating regime [10,11]. VoltGuard addresses this operationally by
conditioning calibration on feeder, PV, and loading families, then reporting
per-family coverage and interval width rather than hiding all calibration
behavior in a single global number.

Table 1 positions the paper relative to representative technical lines. The
comparison is not a claim that every cited method solves the same screening
task; it identifies the missing combination that motivates VoltGuard.

| Line of work | Physics model | Topology-aware learning | Calibrated interval | Screening/DMS interface |
|---|---:|---:|---:|---:|
| AC OPF and distribution control [2,3,14-16] | yes | model based | no | corrective backend |
| Learning-assisted OPF/control [17,18,20] | partial | sometimes | usually no | dispatch-oriented |
| Physics-aware state estimation [4,19] | yes | yes | usually no | estimation-oriented |
| Conformal prediction and CQR [7-9,22-24] | model agnostic | no | yes | task agnostic |
| Conformalized GNNs [10,11] | no explicit feeder physics | yes | yes | graph prediction |
| VoltGuard | LinDistFlow backbone | yes | topology/PV/loading conditioned | voltage-risk screening |

## 3. Problem Formulation

Consider a distribution feeder

$$
\mathcal{G}=(\mathcal{N},\mathcal{E}),
$$

where $\mathcal{N}$ is the bus set and $\mathcal{E}$ is the branch set. A root
or slack bus $0$ defines branch orientation: each branch $(i,j)\in\mathcal{E}$
is directed from upstream bus $i$ toward downstream bus $j$. Each branch has
resistance $r_{ij}$ and reactance $x_{ij}$. Let $v_{i,t}$ be voltage magnitude
at bus $i$ in scenario $t$, and let

$$
u_{i,t}=v_{i,t}^2
$$

be squared voltage magnitude. The slack voltage is fixed to
$v_{0,t}=1.0$ p.u. in the executed simulations, hence $u_{0,t}=1.0$.

The operating features available before screening are load forecasts or
pseudo-measurements $p^d_{i,t}, q^d_{i,t}$, PV forecasts $p^g_{i,t}$, EV-load
indicators, feeder topology, and local/neighbor electrical features. Net
injection is written as

$$
p_{i,t}=p^d_{i,t}-p^g_{i,t}, \qquad q_{i,t}=q^d_{i,t}-q^g_{i,t}.
$$

Positive $p_{i,t}$ denotes net demand. AC power-flow labels
$v^\star_{i,t}$ are used only for supervised training, calibration scoring, and
test evaluation. Test labels are never used to construct features or conformal
radii.

The goal is to produce calibrated voltage intervals

$$
\widehat{\mathcal{I}}^{1-\alpha}_{i,t}
= [\hat v^L_{i,t},\hat v^U_{i,t}]
$$

that are sharp enough for operation while limiting missed voltage violations.
The bus-level risk flag is

$$
\rho_{i,t} =
\mathbf{1}\{\hat v^L_{i,t}<v^{\min}\ \mathrm{or}\ \hat v^U_{i,t}>v^{\max}\},
$$

with $v^{\min}=0.95$ p.u. and $v^{\max}=1.05$ p.u. The scenario-level flag is

$$
\rho_t^{\max} = \max_{i\in\mathcal{N}}\rho_{i,t}.
$$

For prioritization, VoltGuard also computes a scenario-level interval risk
score

$$
\eta_t =
\max_{i\in\mathcal{N}}
\left[
\max(0,v^{\min}-\hat v^L_{i,t}),
\max(0,\hat v^U_{i,t}-v^{\max})
\right].
$$

Large $\eta_t$ means that at least one calibrated bus interval crosses a
voltage limit by a larger margin, so the scenario should be considered earlier
by downstream AC-audited corrective optimization.

## 4. Methodology

### 4.1 LinDistFlow Backbone

For each scenario, approximate downstream branch flows are computed from the
forecast net injections and the oriented radial feeder tree:

$$
\hat P_{ij,t} = \sum_{k\in\mathcal{D}(j)} p_{k,t}, \qquad
\hat Q_{ij,t} = \sum_{k\in\mathcal{D}(j)} q_{k,t},
$$

where $\mathcal{D}(j)$ is the downstream subtree rooted at bus $j$. The
squared-voltage LinDistFlow recursion is

$$
\hat u^{lin}_{j,t} =
\hat u^{lin}_{i,t} - 2(r_{ij}\hat P_{ij,t}+x_{ij}\hat Q_{ij,t}),
\qquad \hat u^{lin}_{0,t}=1.
$$

The voltage-magnitude proxy is

$$
\hat v^{lin}_{i,t}=\sqrt{\max(\hat u^{lin}_{i,t},\epsilon)},
$$

where $\epsilon>0$ prevents numerical issues. The executable prototype computes
this squared-voltage backbone explicitly and stores both $\hat u^{lin}_{i,t}$
and $\hat v^{lin}_{i,t}$. These quantities are used as residual targets and
model inputs together with bus position, voltage base, degree, load, PV, net
demand, neighbor load/PV/net demand, load scale, PV penetration, and EV scale.
No test AC voltage label is used to build the LinDistFlow proxy, conformal
radius, or test-time risk flag.

### 4.2 Topology-Aware Residual Learner

VoltGuard predicts a voltage-magnitude residual

$$
\Delta \hat v_{i,t}=f_\theta(x_{i,t},z_{i,t},g_i),
$$

where $x_{i,t}$ contains local bus operating features, $z_{i,t}$ contains
neighbor-aggregated electrical features, and $g_i$ contains topology features
such as normalized bus index, slack indicator, voltage base, and degree. The
final point estimate is

$$
\hat v_{i,t} = \hat v^{lin}_{i,t} + \Delta \hat v_{i,t}.
$$

In the executable implementation, $f_\theta$ is an ExtraTrees residual learner
trained on $v^\star_{i,t}-\hat v^{lin}_{i,t}$. This choice is deliberate: it
is stable on the executed feeder/scenario families and outperforms the
lightweight neural graph residual on the point-error, interval-width, and
false-alarm metrics used for the selected model.

### 4.3 Physics-Informed Objective

The supervised residual objective is

$$
\mathcal{L}_{sup}
= \frac{1}{|\mathcal{T}||\mathcal{N}|}
\sum_{t\in\mathcal{T}}\sum_{i\in\mathcal{N}}
\left(\hat v_{i,t}-v^\star_{i,t}\right)^2 .
$$

The physics residual used to define the reproducible model class is a
branch-level voltage-drop mismatch in squared-voltage space:

$$
\mathcal{R}_{drop}
= \frac{1}{|\mathcal{T}||\mathcal{E}|}
\sum_{t\in\mathcal{T}}\sum_{(i,j)\in\mathcal{E}}
\left(
\hat u_{j,t}-\hat u_{i,t}
+2(r_{ij}\hat P_{ij,t}+x_{ij}\hat Q_{ij,t})
\right)^2 .
$$

Here $\hat u_{i,t}=\hat v_{i,t}^2$ after residual correction, and
$\hat P,\hat Q$ are computed from forecast injections and feeder orientation,
not from test labels. A smoothness penalty may be added as

$$
\mathcal{R}_{smooth}
= \frac{1}{|\mathcal{T}||\mathcal{E}|}
\sum_{t,(i,j)}
\frac{(\hat v_{i,t}-\hat v_{j,t})^2}{r_{ij}^2+x_{ij}^2+\epsilon}.
$$

The full conceptual objective is

$$
\mathcal{L}
= \mathcal{L}_{sup}
+\lambda_{drop}\mathcal{R}_{drop}
+\lambda_{smooth}\mathcal{R}_{smooth}.
$$

The current tree-based residual implementation realizes the same philosophy
through physics-derived inputs and residual targets rather than through
gradient-based neural optimization of all penalty terms. The physics residual
is still reported explicitly so that a neural or differentiable implementation
can reproduce the same objective without changing the paper's model boundary.

### 4.4 Split Conformal Calibration

For a calibration set $\mathcal{C}$ disjoint from training and testing, the
nonconformity score is

$$
s_{i,t}=|v^\star_{i,t}-\hat v_{i,t}|.
$$

For nominal miscoverage $\alpha$, global split conformal calibration uses

$$
\hat q_{1-\alpha}
= \mathrm{Quantile}_{\lceil (|\mathcal{C}|+1)(1-\alpha)\rceil/|\mathcal{C}|}
\{s_{i,t}:(i,t)\in\mathcal{C}\}.
$$

The global interval is

$$
\widehat{\mathcal{I}}^{1-\alpha}_{i,t}
= [\hat v_{i,t}-\hat q_{1-\alpha},
   \hat v_{i,t}+\hat q_{1-\alpha}].
$$

The finite-sample conformal statement relies on exchangeability between
calibration and test samples [7,8]. In this paper, that means the stated
feeder/scenario family, split rule, and calibration protocol. The paper does
not claim unconditional safety under arbitrary topology switching, time drift,
PV distribution shift, or field deployment.

### 4.5 Topology/PV/Loading Conditioned Calibration

Voltage residual distributions vary by feeder, PV level, and loading regime.
VoltGuard therefore partitions calibration samples into families

$$
g(i,t)=\{\mathrm{feeder},\mathrm{PV\ bin},\mathrm{load\ bin}\}.
$$

For each family $g$, a family quantile $\hat q_{g,1-\alpha}$ is computed. To
avoid overconfident intervals in small families, VoltGuard uses shrinkage toward
the global quantile:

$$
\tilde q_{g,1-\alpha}
= \omega_g\hat q_{g,1-\alpha}
+(1-\omega_g)\hat q_{1-\alpha},
\qquad
\omega_g=\frac{n_g}{n_g+n_0},
$$

where $n_g$ is the number of calibration samples in family $g$ and $n_0$ is the
minimum-group scale. The experiments compare global, PV-conditioned,
topology-conditioned, topology+PV+loading conditioned, and no-shrinkage
variants. EV scale is included in the point-estimator feature set, but it is
not automatically used as a conformal grouping key because it can fragment
family sample sizes. The EV-conditioned ablation in the results tests this
choice directly.

### 4.6 Two-Stage Operating Interface

VoltGuard is a screening layer. It does not select final dispatch as an OPF or
MPC controller. In the two-stage interface:

1. VoltGuard produces calibrated bus-level intervals and scenario-level risk
   flags.
2. Risky scenarios are passed to an AC-audited corrective layer, such as
   discrete grid search, OPF, or MPC.
3. When the downstream layer has limited compute budget, scenarios are ranked
   by $\eta_t$ so that larger interval-limit crossings are audited first.

The simple risk-trigger action used for diagnostic operating value applies 10%
flexible-load relief when undervoltage risk appears and 10% PV curtailment when
overvoltage risk appears. A stronger AC-audited grid search is then reported as
a downstream corrective benchmark.

## 5. Experimental Design

The main experiments use IEEE 33-bus and IEEE 69-bus distribution feeders. IEEE
118-bus is retained as a supplementary stress test because it is not a canonical
distribution feeder. For each feeder, 300 AC-solvable scenarios are generated
with randomized load scale, PV penetration, EV demand, and PV siting. AC power
flow provides reference labels.

Four split protocols are executed:

- Random interpolation: scenario-disjoint 60/20/20 train/calibration/test split.
- Synthetic time-block: scenario IDs are treated as ordered blocks.
- PV-penetration shift: low/medium PV scenarios train, medium-high PV
  calibrates, and high PV tests.
- Topology-held-out transfer: IEEE 33-bus trains the residual learner, while
  IEEE 69-bus calibration and testing evaluate feeder transfer.

The main random split is repeated with seeds 7, 17, and 42. The representative
run uses seed 7, and all raw predictions, conformal scores, family labels, and
risk flags are saved for that run.

Baselines include the squared-voltage LinDistFlow physical backbone, random
forest, gradient boosting, boosting plus global conformal calibration,
VoltGuard conformal variants, and a neural graph residual ablation. These
baselines cover three screening families requested by reviewers: transparent
physical screening, standard tree-based machine learning, and graph-neural
residual learning. Metrics are bus-level MAE/RMSE, coverage, interval width,
violation precision/recall/F1, false-alarm rate, missed violations,
scenario-level recall/false alarms, and family-level calibration behavior.
Downstream operating audits remain project artifacts outside the main method
submission.

For readability, result tables use compact labels: LDF denotes the
LinDistFlow physical backbone, Boost-GC denotes boosting with global conformal
calibration, T/PV/L denotes topology/PV/loading conditioning, and GNN ablation
denotes the neural graph residual diagnostic.

### 5.5 Comparison with State-of-the-Art Screening Baselines

The experiments include six competing or diagnostic approaches. LinDistFlow is
the direct physical proxy and represents a voltage-sensitivity-style screen
without learning. Random forest and gradient boosting are standard tabular ML
screens using the same pre-dispatch features. Boosting plus global conformal
calibration is a conformalized point-prediction baseline. The neural graph
residual ablation tests whether message passing is competitive under the same
data budget. VoltGuard is the proposed topology-aware residual learner with
topology/PV/loading conditioned conformal calibration. The comparison table in
Section 6 reports the same error, coverage, width, false-negative, and
false-alarm quantities for these methods.

## 6. Results

### 6.1 Representative Random-Split Results

On the representative IEEE 33/69 random split, VoltGuard with
topology+PV+loading conditioned calibration achieves the strongest screening
tradeoff among the selected main estimators.

| Method | Conformal variant | RMSE | Coverage | Width | Recall | False alarm | Missed |
|---|---|---:|---:|---:|---:|---:|---:|
| LinDistFlow physical backbone | none | 0.00140 | -- | -- | 0.91640 | 0.00000 | 77 |
| Random forest | none | 0.00023 | -- | -- | 0.99023 | 0.00019 | 9 |
| Gradient boosting | none | 0.00041 | -- | -- | 0.97286 | 0.00000 | 25 |
| Boosting point + global conformal | global | 0.00041 | 0.90850 | 0.00110 | 0.99674 | 0.00250 | 3 |
| VoltGuard topology-aware residual | topology+PV+loading | 0.00011 | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1 |
| Neural graph residual ablation | topology | 0.00171 | 0.91340 | 0.00540 | 0.99783 | 0.02327 | 2 |

The neural ablation attains high recall but with substantially wider intervals,
higher RMSE, and higher false-alarm rate. It is therefore kept as an ablation,
not as the main estimator.

### 6.2 Branch-Level Physics Consistency Audit

Because VoltGuard corrects a LinDistFlow-style voltage proxy, we audit whether
the saved voltage predictions remain consistent with the branch-level
voltage-drop relation used in the methodology. For each representative test
scenario, feeder branches are oriented from the slack bus, downstream
forecast net injections are aggregated, and the residual

$$
\hat u_j-\hat u_i+2(r_{ij}\hat P_{ij}+x_{ij}\hat Q_{ij})
$$

is computed on each branch. This is a LinDistFlow consistency audit, not an AC
feasibility certificate; the AC-label row is not zero because the proxy ignores
losses and other full AC effects.

| Method | Variant | Scenarios | Drop RMSE | Drop MAE | 95% max-abs drop residual | Violating-only drop RMSE |
|---|---|---:|---:|---:|---:|---:|
| AC power-flow label | reference | 120 | 0.000238 | 0.000101 | 0.002516 | 0.000272 |
| Boosting point + global conformal | global | 120 | 0.000563 | 0.000379 | 0.004631 | 0.000621 |
| VoltGuard topology-aware residual | topology+PV+loading | 120 | 0.000250 | 0.000122 | 0.002395 | 0.000279 |
| Neural graph residual ablation | topology | 120 | 0.003139 | 0.002437 | 0.014201 | 0.002904 |

VoltGuard substantially reduces the branch-drop RMSE relative to boosting plus
global conformal and remains close to the AC-label audit residual, while the
neural graph residual is substantially less consistent with the LinDistFlow
drop relation. This supports the paper's physics-informed claim in the narrow
sense used here: residual learning is anchored to a real LinDistFlow backbone,
operating features, and topology in a way that improves calibrated screening
without moving far from the physical voltage-drop structure.

### 6.3 Multi-Seed Random-Split Statistics

Across three random seeds, VoltGuard reduces missed violations relative to
boosting plus global conformal while maintaining near-nominal coverage.

| Method | Variant | RMSE mean | Coverage mean | Width mean | Recall mean | False alarm mean | Missed mean | Runs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Boosting point + global conformal | global | 0.00076 | 0.90468 | 0.00127 | 0.99811 | 0.00240 | 1.67 | 3 |
| VoltGuard topology-aware residual | topology+PV+loading | 0.00017 | 0.92397 | 0.00049 | 0.99964 | 0.00171 | 0.33 | 3 |

The confidence intervals are reported in `multi_seed_summary.md`. The main
interpretation is not that every seed dominates on every metric, but that
conditioned calibration improves the risk-recall tradeoff without relying on a
GNN claim.

We also report paired seed deltas relative to boosting plus global conformal,
using the same split seed before averaging. Positive deltas mean VoltGuard is
larger; negative deltas are better for RMSE, width, false alarms, and missed
violations. On the random interpolation split, VoltGuard reduces missed
bus-level violations by 1.33 on average, increases recall by 0.00152, and
narrows intervals by 0.00078 p.u. On synthetic time-block splits, the paired
missed-violation reduction is also 1.33. Under PV-shift, VoltGuard keeps recall
slightly higher while coverage drops below nominal, reflecting the deliberately
shifted test distribution. Under topology-held-out 33-to-69 transfer, missed
violations are unchanged while intervals and false alarms are lower, but this
is still a protocol-specific transfer result rather than a topology-invariant
safety guarantee.

| Split | Runs | Delta coverage | Delta width | Delta recall | Delta false alarm | Delta missed |
|---|---:|---:|---:|---:|---:|---:|
| random interpolation | 3 | 0.01928 | -0.00078 | 0.00152 | -0.00070 | -1.33 |
| synthetic time-block | 3 | 0.04025 | -0.00058 | 0.00140 | -0.00110 | -1.33 |
| PV-penetration shift | 3 | -0.02652 | -0.00044 | 0.00064 | -0.00016 | -0.33 |
| topology-held-out 33-to-69 | 3 | 0.00242 | -0.00078 | 0.00000 | -0.00129 | 0.00 |

### 6.4 Feature/Residual Ablation

We add a feature/residual ablation to test whether the main estimator is
actually topology-aware or merely a generic tree ensemble. All variants use the
same topology/PV/loading conformal calibration and three random seeds. The
local-only residual learner uses only bus-level operating quantities; the
local+topology variant adds bus position, voltage base, degree, slack
indicator, and feeder code; the full variant also includes neighbor
load/PV/net-demand features. A direct full ExtraTrees model tests whether the
residual formulation matters once the same full feature family is available.

| Variant | Feature family | Runs | RMSE | Coverage | Width | Recall | False alarm | Missed |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| direct | full topology/electrical | 3 | 0.00029 | 0.91111 | 0.00073 | 0.99848 | 0.00298 | 1.33 |
| residual | local operating only | 3 | 0.00073 | 0.92195 | 0.00207 | 0.99621 | 0.00373 | 3.33 |
| residual | local+topology | 3 | 0.00022 | 0.91694 | 0.00071 | 0.99964 | 0.00298 | 0.33 |
| residual | full topology/electrical | 3 | 0.00017 | 0.92413 | 0.00050 | 0.99964 | 0.00171 | 0.33 |

The ablation supports the topology/electrical part of the claim strongly:
removing topology and neighbor electrical features increases the mean missed
bus-level violations from 0.33 to 3.33 and widens intervals from 0.00050 to
0.00207 p.u. The residual formulation should be read more narrowly. Relative
to a direct full ExtraTrees predictor, the residual full model lowers RMSE
(0.00017 versus 0.00029), interval width (0.00050 versus 0.00073), and
false-alarm rate (0.00171 versus 0.00298), while both the full residual and
local+topology residual have statistically comparable missed-violation counts.
This is why the paper emphasizes physics-informed topology-aware residual
screening rather than claiming that residualization alone dominates every
operating metric.

### 6.5 Comparison with Competing Screening Methods

The reviewer-requested comparison table brings together the representative
random-split results for physical, tree-based, conformal, statistical-UQ, and
graph-residual screens. The quantile-regression and Gaussian-process rows are
additional baselines run on the same seed-7 random split. The Gaussian-process
baseline uses a 900-row training subsample for tractability and is included to
test whether generic probabilistic regression gives useful screening intervals
without feeder-specific residual structure.

| Method | Interval source | RMSE | Coverage | Width | Recall | False alarm | Missed |
|---|---|---:|---:|---:|---:|---:|---:|
| LinDistFlow physical backbone | point only | 0.00140 | n/a | n/a | 0.91640 | 0.00000 | 77 |
| Random forest | point only | 0.00023 | n/a | n/a | 0.99023 | 0.00019 | 9 |
| Gradient boosting | point only | 0.00042 | n/a | n/a | 0.97286 | 0.00000 | 25 |
| Boosting + global conformal | pooled residual quantile | 0.00042 | 0.90850 | 0.00110 | 0.99674 | 0.00250 | 3 |
| Gradient-boosted quantile regression | learned 5/95% quantiles | 0.00035 | 0.83219 | 0.00444 | 0.99566 | 0.00135 | 4 |
| Gaussian-process UQ baseline | 90% Gaussian interval | 0.01165 | 0.97827 | 0.05108 | 1.00000 | 0.33353 | 0 |
| Neural graph residual ablation | topology conformal | 0.00171 | 0.91340 | 0.00540 | 0.99783 | 0.02327 | 2 |
| VoltGuard topology-aware residual | topology/PV/loading conformal | 0.00011 | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1 |

The comparison clarifies the novelty boundary. Standard tree models can give
competitive point accuracy, but their uncalibrated risk flags miss more
violations. Global conformal calibration improves recall but is less sharp
than conditioned calibration. Quantile regression gives intervals but
under-covers in this split, while generic Gaussian-process intervals become
too wide and produce many false alarms. The graph residual does not outperform
the topology-aware residual learner. VoltGuard's advantage is therefore the
combination of a physical voltage proxy, topology/electrical residual features,
and conditioned conformal calibration rather than a generic ML model alone.

### 6.6 Conformal Ablation

The representative random split directly compares calibration variants.

| Variant | Coverage | Width | Recall | False alarm | Missed |
|---|---:|---:|---:|---:|---:|
| global | 0.94984 | 0.00053 | 0.99891 | 0.00115 | 1 |
| PV-conditioned | 0.94510 | 0.00049 | 0.99891 | 0.00058 | 1 |
| topology-conditioned | 0.95523 | 0.00053 | 0.99891 | 0.00154 | 1 |
| topology+PV+loading conditioned | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1 |
| topology+PV+loading no-shrinkage | 0.91258 | 0.00042 | 0.99891 | 0.00038 | 1 |

All VoltGuard conformal variants miss only one bus-level violation in this
split. The topology+PV+loading conditioned variant is selected because it keeps
that recall while producing the sharpest shrinkage-stabilized interval; the
no-shrinkage version is marginally narrower but loses coverage, which is why
shrinkage remains in the main method.

### 6.6 Calibration-Budget Sensitivity

Conditioned conformal calibration is useful only if the calibration set covers
the operating families that will appear at test time. We therefore add a
scenario-level calibration-budget audit using the saved representative split.
The residual model is not retrained. Instead, calibration scenarios are sampled
without replacement at 10%, 25%, 50%, 75%, and 100% of the calibration split,
and conformal radii are recomputed before evaluating the same held-out test
set. Partial-budget cases are repeated 20 times. Sampling is done at the
scenario level so buses from the same scenario are not treated as independent
calibration draws.

| Method | Calib. fraction | Calib. scenarios | Observed families | Empty test families | Coverage | Width | Recall | False alarm | Missed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Boosting + global | 0.10 | 12 | 1.00 | 0.00 | 0.89410 | 0.00104 | 0.99457 | 0.00181 | 5.00 |
| Boosting + global | 1.00 | 120 | 1.00 | 0.00 | 0.90850 | 0.00110 | 0.99674 | 0.00250 | 3.00 |
| VoltGuard topology+PV+loading | 0.10 | 12 | 8.40 | 7.60 | 0.92903 | 0.00047 | 0.99902 | 0.00110 | 0.90 |
| VoltGuard topology+PV+loading | 0.25 | 30 | 13.35 | 2.65 | 0.93528 | 0.00044 | 0.99924 | 0.00091 | 0.70 |
| VoltGuard topology+PV+loading | 0.50 | 60 | 15.80 | 0.20 | 0.94022 | 0.00044 | 0.99919 | 0.00089 | 0.75 |
| VoltGuard topology+PV+loading | 0.75 | 90 | 16.00 | 0.00 | 0.94051 | 0.00044 | 0.99919 | 0.00078 | 0.75 |
| VoltGuard topology+PV+loading | 1.00 | 120 | 16.00 | 0.00 | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1.00 |

The budget audit supports deployment, but with a clear boundary. With only
12 calibration scenarios, the shrinkage/fallback construction prevents the
screen from collapsing: coverage remains 0.92903 and the mean missed
bus-level violations stay below one in this representative test set. However,
the calibration set observes only 8.4 of the 16 test families on average, so
many conditioned families are not actually calibrated locally. At 75% and full
budget, all 16 families are observed. We therefore describe small-budget
results as evidence for a robust fallback mechanism, not as evidence for
family-wise coverage without family-level calibration diversity.

### 6.7 Asymmetric Conformal Audit

We also audit an asymmetric one-sided conformal variant because voltage limits
are directional: undervoltage risk depends on the lower tail and overvoltage
risk depends on the upper tail. This audit uses the same saved calibration and
test predictions and replaces the symmetric absolute-residual radius with
separate lower and upper one-sided conformal radii. It is not a new
distribution-shift guarantee; it is a tail-aware calibration ablation under the
same split and exchangeability assumptions as the main conformal analysis.

| Method | Calibration | Coverage | Width | Recall | False alarm | Missed |
|---|---|---:|---:|---:|---:|---:|
| Boosting + global conformal | symmetric | 0.90850 | 0.001096 | 0.99674 | 0.00250 | 3 |
| Boosting + global conformal | asymmetric | 0.90539 | 0.001162 | 0.99891 | 0.00327 | 1 |
| VoltGuard global | symmetric | 0.94984 | 0.000527 | 0.99891 | 0.00115 | 1 |
| VoltGuard global | asymmetric | 0.94624 | 0.000497 | 0.99891 | 0.00058 | 1 |
| VoltGuard topology+PV+loading | symmetric | 0.93660 | 0.000433 | 0.99891 | 0.00058 | 1 |
| VoltGuard topology+PV+loading | asymmetric | 0.91977 | 0.000411 | 1.00000 | 0.00058 | 0 |

For the main topology+PV+loading variant, the asymmetric audit narrows the
mean interval by 0.000022 p.u. and removes the remaining missed bus-level
violation while retaining scenario-level recall of 1.0. The cost is lower
empirical coverage, 0.91977 rather than 0.93660, although still above the
nominal 90% target in this representative split. We therefore keep symmetric
conditioned conformal calibration as the main method and report the asymmetric
variant as an optional tail-aware extension that may be useful when missed
voltage violations are costlier than modest interval-efficiency loss.

### 6.8 EV-Conditioning Ablation

Because the scenarios also include EV charging perturbations, we add an
EV-conditioned ablation to test whether EV scale should be added to the
conformal family key. The result is negative for the current sample size.
Adding EV to the topology+PV+loading family increases the number of families
from 16 to 55, reduces the minimum calibration count from 198 to 33, and leaves
seven empty test families. It does not reduce missed violations or improve
recall; it increases interval width and false alarms. Thus EV demand remains a
pre-dispatch feature for residual learning, but the conformal calibration key
is kept at feeder/PV/loading granularity unless a larger EV-calibration set is
available.

| Conditioning key | Families | Min calib. | Empty test families | Coverage | Width | Recall | False alarm | Missed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| topology+PV+loading | 16 | 198 | 0 | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1 |
| topology+PV+loading+EV | 55 | 33 | 7 | 0.94918 | 0.00048 | 0.99891 | 0.00154 | 1 |
| topology+PV+EV | 31 | 33 | 1 | 0.94853 | 0.00050 | 0.99891 | 0.00173 | 1 |
| PV+loading+EV | 32 | 33 | 0 | 0.94003 | 0.00045 | 0.99891 | 0.00077 | 1 |
| EV-only | 4 | 1359 | 0 | 0.94444 | 0.00053 | 0.99891 | 0.00115 | 1 |

This ablation is therefore a sample-size outlook rather than a claim that EV
information has no value. At the current calibration scale, EV bins fragment
the calibration set: the most detailed EV-conditioned key has only 33 samples
in its smallest calibration family, compared with 198 for the primary
topology+PV+loading key. If the same scenario design were expanded while
keeping the EV family definition fixed, the EV-conditioned split would need
roughly six times more calibration support before its weakest family matches
the primary grouping. The supplementary sensitivity curve below records this
threshold logic and should be used to decide when EV-conditioned calibration is
worth retesting.

| Calibration scale relative to current EV-conditioned split | Approx. minimum EV-family calibration samples | Expected EV-conditioning status |
|---:|---:|---|
| 1x | 33 | Fragmented; no recall gain observed and intervals are wider |
| 2x | 66 | Still below primary-family support; diagnostic use only |
| 4x | 132 | Candidate regime for retesting EV-conditioned intervals |
| 6x | 198 | Comparable weakest-family support to topology+PV+loading |
| 8x | 264 | Plausible regime if width and false alarms begin to fall |

### 6.9 Per-Family Calibration Analysis

Per-family analysis exposes where conditioned calibration works and where it
remains weak.

| Family | Calib. samples | Test samples | Coverage | Width | Recall | False alarm | Missed |
|---|---:|---:|---:|---:|---:|---:|---:|
| 33, PV 0.2, high load | 198 | 330 | 0.97576 | 0.00069 | 1.00000 | 0.00000 | 0 |
| 33, PV 0.4, high load | 231 | 264 | 0.99621 | 0.00076 | 1.00000 | 0.00000 | 0 |
| 33, PV 0.6, high load | 396 | 165 | 0.84242 | 0.00070 | 0.98305 | 0.01887 | 1 |
| 33, PV 0.8, low load | 198 | 99 | 0.76768 | 0.00060 | -- | 0.00000 | 0 |
| 69, PV 0.2, high load | 1104 | 759 | 0.91173 | 0.00029 | 1.00000 | 0.00000 | 0 |
| 69, PV 0.4, low load | 414 | 483 | 0.82402 | 0.00022 | 1.00000 | 0.00000 | 0 |

The low-coverage 33-bus PV 0.8 low-load family has no actual violating buses,
so it is a calibration-efficiency warning rather than a missed-risk warning.
The 33-bus PV 0.6 high-load family is the main risk-relevant weak family: it
contains 59 violating buses and one missed violation. These rows motivate the
discussion: conditioned calibration is useful, but it does not remove the need
for sufficient family-level calibration samples and explicit per-family
reporting.

We therefore add a post-hoc recalibration audit rather than hiding this weak
family. The audit uses test AC labels only for diagnosis and asks how much an
inflate-only family radius update would be needed to restore the 90% empirical
target. Across 16 topology/PV/loading families, five are below nominal
coverage. Inflating only those undercovered family radii increases weighted
interval width from 0.000433 to 0.000451 p.u. and leaves false alarms and
missed violations unchanged in this representative split. For the weakest
coverage family, 33-bus PV 0.8 low-load, coverage improves from 0.76768 to
0.90909 without affecting violations because the family has no violating buses.
For the risk-relevant 33-bus PV 0.6 high-load family, coverage improves from
0.84242 to 0.90909 while the single missed violation remains. This is the
proper operational reading of conditioned conformal calibration: family
reporting identifies where explicit recalibration changes coverage and
sharpness, and whether the undercovered family is operationally risky or merely
interval-inefficient.

| Recalibration audit | Families | Undercovered | Missed current | Missed audited | Width current | Width audited | False alarm current | False alarm audited |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Inflate undercovered families only | 16 | 5 | 1 | 1 | 0.000433 | 0.000451 | 0.00058 | 0.00058 |

### 6.10 Risk-Stratified Calibration and Screening

Aggregate coverage can hide the voltage-boundary behavior that matters for
operation. We therefore add a risk-stratified audit on the representative
random split. Bus samples and scenarios are grouped into true violations,
boundary-safe cases within 0.002 p.u. of either voltage limit, near-safe cases
within 0.010 p.u., and interior-safe cases. This audit is derived from saved
raw interval predictions and does not retrain any estimator.

| Method | Stratum | Bus samples | Coverage | Width | Risk-flag rate | Recall / false-alarm | Missed / false alarms |
|---|---|---:|---:|---:|---:|---:|---:|
| Boosting + global conformal | violating | 921 | 0.59501 | 0.00110 | 0.99674 | 0.99674 recall | 3 missed |
| VoltGuard | violating | 921 | 0.87188 | 0.00052 | 0.99891 | 0.99891 recall | 1 missed |
| Neural graph ablation | violating | 921 | 0.74159 | 0.00611 | 0.99783 | 0.99783 recall | 2 missed |
| Boosting + global conformal | boundary-safe | 55 | 0.78182 | 0.00110 | 0.23636 | 0.23636 false alarm | 13 false alarms |
| VoltGuard | boundary-safe | 55 | 0.92727 | 0.00044 | 0.05455 | 0.05455 false alarm | 3 false alarms |
| Neural graph ablation | boundary-safe | 55 | 0.90909 | 0.00664 | 0.81818 | 0.81818 false alarm | 45 false alarms |

The boundary-safe rows are important for operating value. A conservative
interval can achieve high recall by flagging many near-limit but safe buses,
which increases unnecessary downstream AC calls or corrective actions.
VoltGuard reduces boundary-safe false-alarm buses from 13 under boosting plus
global conformal and 45 under the neural graph ablation to three, while still
missing only one of 921 truly violating buses. At scenario level, VoltGuard
recalls all 93 truly risky scenarios and produces zero false-alarm scenarios
across the boundary-safe, near-safe, and interior-safe strata. This is a more
direct voltage-risk-screening test than aggregate RMSE alone.

### 6.11 Shift and Scenario-Level Results

Under PV-penetration shift, VoltGuard keeps bus-level violation recall at
99.81%, but empirical coverage drops below nominal because the test
distribution is intentionally shifted. This is exactly why the paper does not
claim unconditional distribution-free safety. Under topology-held-out transfer
from 33-bus training to 69-bus calibration/testing, the topology+PV+loading
variant has zero missed bus-level violations across the three seeds and lower
false alarms than boosting plus global conformal. This is encouraging, but it
is still a controlled 33-to-69 transfer with calibration on the target feeder,
not a proof of arbitrary topology-shift safety.

We also audit an explicit PV-shift recalibration protocol. The point estimator
is still trained only on the low/medium-PV split. A small, disjoint subset of
early high-PV scenarios is then treated as target calibration, and the
remaining high-PV scenarios are evaluated. This simulates periodic
AC-audited recalibration after a feeder enters a higher renewable-hosting
regime; the target calibration labels are not reused for testing.

| PV-shift calibration protocol | Target high-PV calibration scenarios | High-PV test scenarios | Coverage | Width | Recall | False alarm | Missed |
|---|---:|---:|---:|---:|---:|---:|---:|
| Source PV 0.6 calibration only | 0 | 132 | 0.76915 | 0.00081 | 0.99807 | 0.00147 | 1.00 |
| Source + 10% target high-PV calibration | 16 | 116 | 0.89527 | 0.00189 | 1.00000 | 0.00398 | 0.00 |
| Source + 20% target high-PV calibration | 29 | 103 | 0.88790 | 0.00176 | 1.00000 | 0.00322 | 0.00 |

Thus target recalibration repairs much of the coverage loss and removes the
remaining missed bus-level violation, but it does so by widening intervals and
raising false alarms. This is not an unconditional conformal guarantee under
PV shift; it is evidence that the screening layer can be re-calibrated when a
new high-PV operating regime supplies AC-audited calibration cases.

The same PV-shift adaptation is also translated into operating screening
quantities on the remaining high-PV scenarios. With source-only calibration,
VoltGuard releases 57.00 high-PV scenarios from downstream AC optimization on
average, but still has one missed bus-level violation. Adding the 10% target
high-PV calibration set removes the bus-level missed violation while keeping
scenario-level risky recall at 1.00000. The cost is operationally visible:
screened-safe releases fall to 49.67 scenarios and the mean interval width
increases from 0.00081 to 0.00209 p.u. This is the desired interpretation for
energy management: target recalibration improves high-PV risk conservatism,
but it consumes calibration data and reduces the number of scenarios that can
be safely bypassed.

| PV-shift screening protocol | Target high-PV calibration scenarios | AC calls avoided mean | Risky recall mean | Post-screen miss mean | Missed buses mean | Width mean |
|---|---:|---:|---:|---:|---:|---:|
| Source PV 0.6 calibration only | 0 | 57.00 | 1.00000 | 0.00000 | 1.00 | 0.00081 |
| Source + 10% target high-PV calibration | 16 | 49.67 | 1.00000 | 0.00000 | 0.00 | 0.00209 |

At scenario level, the representative random split has 120 test scenarios and
93 risky scenarios. VoltGuard topology+PV+loading conditioned calibration has
scenario recall 1.000, zero missed risky scenarios, and zero scenario false
alarms. The neural graph ablation also avoids missed risky scenarios but
triggers many more scenario false alarms and has worse bus-level sharpness.

### 6.12 Expanded IEEE 118-Bus Stress Audit

The IEEE 118-bus case is not used as the main distribution-network evidence,
but the review requested either a realistic feeder case or a more complete
analysis of this supplementary system. We therefore report the same
representative random-split metrics on the 118-bus stress case. The result is
intentionally interpreted as a stress audit because the LinDistFlow assumptions
and radial distribution-feeder interpretation are not native to this system.

| Method | Variant | RMSE | Coverage | Width | Recall | False alarm | Missed |
|---|---|---:|---:|---:|---:|---:|---:|
| LinDistFlow physical backbone | none | 0.88711 | n/a | n/a | 0.80723 | 0.87352 | 48 |
| Random forest | none | 0.00445 | n/a | n/a | 0.58635 | 0.00425 | 103 |
| Gradient boosting | none | 0.00466 | n/a | n/a | 0.57831 | 0.00586 | 105 |
| Boosting point + global conformal | global | 0.00466 | 0.89237 | 0.01005 | 0.82731 | 0.06236 | 43 |
| VoltGuard topology-aware residual | global | 0.00572 | 0.90254 | 0.01054 | 0.81526 | 0.06851 | 46 |
| VoltGuard topology-aware residual | PV conditioned | 0.00572 | 0.91243 | 0.01211 | 0.88755 | 0.07159 | 28 |
| VoltGuard topology-aware residual | topology/PV/loading | 0.00572 | 0.91328 | 0.01211 | 0.88353 | 0.07100 | 29 |

The 118-bus audit does not strengthen the distribution-feeder claim; it
exposes where the present physical backbone is inappropriate. The stress case
requires much wider intervals and still misses more bus-level violations than
the 33/69 distribution-feeder experiments. This is why the main evidence is
kept on IEEE 33-bus and 69-bus feeders, while realistic unbalanced
OpenDSS/SMART-DS feeders remain a required next validation step rather than a
claim made by the current manuscript.

### 6.13 Failure Mode Analysis

The representative 33/69 random split contains one missed bus-level violation
for the selected topology/PV/loading conditioned VoltGuard interval. The miss
occurs on IEEE 33-bus scenario 153, bus 7, under PV bin 0.6 and high loading.
The true voltage is 0.949940 p.u., only 0.000060 p.u. below the 0.95 p.u.
limit. The predicted voltage is 0.950518 p.u.; with a conformal radius of
0.000351 p.u., the lower interval endpoint is 0.950167 p.u. and therefore just
misses the undervoltage boundary.

This is not a missed risky scenario. The same scenario contains many deeper
undervoltage buses, including bus 17 at 0.916314 p.u. and bus 16 at 0.917032
p.u., all of which are flagged by the interval screen. The failure mode is
therefore a boundary-bus miss inside an already risky scenario, not a release
of a dangerous scenario. Operationally, the scenario would still enter the
corrective-audit queue because other buses are flagged.

The early-warning indicators are visible in the inputs: high loading, PV bin
0.6, multiple downstream buses near the undervoltage band, and a scenario whose
minimum interval lower bound is already far below 0.95 p.u. The DMS
integration paper turns these indicators into fallback rules: stale telemetry,
unseen topology, out-of-envelope forecast features, and rolling residual alarms
force watch or corrective-audit routing even when an individual boundary bus is
not flagged.

### 6.14 Computational Cost and Breakeven Analysis

The reviewer-requested timing audit separates training, online screening, and
downstream AC-audited grid search. On the representative random split, fitting
the residual learner uses 18,360 training rows and takes 1.858 s; the full
train/calibration/test evaluation takes 4.468 s. The supplementary 118-bus
stress run takes 2.426 s for model fitting and 2.508 s end-to-end.

| Workflow | Scenarios sent to AC | Seconds | ms/scenario | Speedup vs full AC |
|---|---:|---:|---:|---:|
| VoltGuard online screening only | 120 | 0.03046 | 0.25380 | 6796.17 |
| Full AC grid search on every scenario | 120 | 206.98291 | 1724.86 | 1.00 |
| VoltGuard-flagged scenarios then AC grid search | 93 | 160.44221 | 1725.19 | 1.29 |
| VoltGuard top-20% budget then AC grid search | 24 | 41.42704 | 1726.13 | 5.00 |

A rough breakeven calculation is favorable because online screening is cheap.
Using the 1.858 s fit time and the per-scenario difference between full AC grid
search and screening-only evaluation, the fit cost is recovered after roughly
1.1 screened scenarios. The more important operational question is not
training amortization but triage policy: conservative intervals may still send
many scenarios to AC analysis, while risk-budgeted queues can reduce wall-clock
time when the operator has a limited AC-study budget.

### 6.15 Forecast-Noise Robustness

The screening layer runs before dispatch, so the load, PV, and
EV inputs should be interpreted as forecasts or pseudo-measurements rather
than perfect realized injections. We therefore add a forecast-noise robustness
audit. Only pre-dispatch input features are perturbed: load, reactive load, PV,
net injection, EV/load/PV scale features, neighbor aggregates, and the
LinDistFlow backbone recomputed from those noisy injections. The AC voltage
labels remain unchanged. This asks how much the screening layer degrades when
the operating input is imperfect.

| Forecast-noise std. | RMSE | Coverage | Width | Bus recall | False alarm | Missed buses | Scenario recall | Missed risky scenarios |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0% | 0.00011 | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1 | 1.00000 | 0 |
| 5% | 0.00112 | 0.90359 | 0.00309 | 0.99783 | 0.01019 | 2 | 1.00000 | 0 |
| 10% | 0.00208 | 0.89330 | 0.00640 | 0.98480 | 0.02770 | 14 | 1.00000 | 0 |
| 20% | 0.00392 | 0.87402 | 0.01098 | 0.97937 | 0.04155 | 19 | 0.98925 | 1 |

The result is deliberately not presented as a new guarantee. It shows that the
scenario-level screening task remains stable through 10% forecast noise, while
bus-level misses and false alarms increase as forecasts degrade. At 20% noise,
one risky scenario is missed. This motivates noise-aware calibration or
operator-chosen conservative margins when forecast uncertainty is large.

### 6.13 Two-Stage Operating Value

The AC-audited corrective grid-search benchmark is evaluated on the same
representative IEEE 33/69 random split. It searches load relief and PV
curtailment in `{0%, 10%, 20%}` and selects the action with the fewest voltage
violating buses, then the lowest action cost.

| Method | Test scenarios | Post-action violating scenarios | Violating buses | Violation rate | Curtailed PV | Relieved load |
|---|---:|---:|---:|---:|---:|---:|
| AC corrective grid-search benchmark | 120 | 51 | 398 | 0.42500 | 0.00000 | 59.14266 |

This benchmark is stronger than a simple risk-triggered rule, but it is a
downstream optimizer. VoltGuard should be read as the calibrated front-end that
decides which scenarios deserve this AC-audited corrective treatment.

The representative learned benchmark is dominated by undervoltage events in
the main 33/69 feeders. To avoid overstating renewable-hosting coverage, we add
a separate high-PV AC stress audit with light-load scenarios, PV penetration
from 100% to 400% of base load, and slack/tap setpoints from 1.00 to 1.04 p.u.
This supplementary audit is not used for model training; it tests whether the
same downstream interface can represent overvoltage/PV-curtailment operation.
Across 270 AC-converged stress scenarios, 132 have pre-action overvoltage.
Grid-search PV curtailment in 0%-50% steps reduces post-action overvoltage
scenarios to 43 and overvoltage buses from 2262 to 552 while accepting 468.05
MW of PV and curtailing 316.74 MW across initially overvoltage cases. The
remaining overvoltage cases show the limitation of a coarse curtailment grid
and motivate stronger OPF/MPC backends for final dispatch.

| Hosting stress case | Scenarios | Pre-over scenarios | Post-over scenarios | Pre-over buses | Post-over buses | Max pre V | Max post V | Accepted PV | Curtailed PV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| High-PV AC stress, 33/69 | 270 | 132 | 43 | 2262 | 552 | 1.24552 | 1.13734 | 468.05 | 316.74 |

The same AC stress set is then expanded into a High-PV hosting frontier rather
than a single selected action. For each stress scenario, every PV-curtailment
level in the 0%-50% grid is AC-audited and aggregated as accepted PV,
curtailed PV, remaining overvoltage scenarios, remaining overvoltage buses, and
maximum voltage. On the initially overvoltage subset, 20% curtailment still
accepts 627.83 MW of PV and removes 31 of 132 overvoltage scenarios; 50%
curtailment accepts 392.39 MW of PV and removes 89 overvoltage scenarios and
1710 overvoltage buses. This curve makes the hosting tradeoff explicit: the
screening layer can prioritize which scenarios enter the downstream search, but
the final PV acceptance/curtailment decision remains an AC-audited operational
optimization problem.

| High-PV hosting frontier | PV curtailment | Accepted PV | Curtailed PV | Overvoltage scenarios | Overvoltage buses | Scenario reduction | Bus reduction | Max V |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Initially overvoltage 33/69 | 0.00 | 784.79 | 0.00 | 132 | 2262 | 0.00000 | 0.00000 | 1.24552 |
| Initially overvoltage 33/69 | 0.20 | 627.83 | 156.96 | 101 | 1545 | 0.23485 | 0.31698 | 1.20183 |
| Initially overvoltage 33/69 | 0.30 | 549.35 | 235.44 | 82 | 1177 | 0.37879 | 0.47966 | 1.17875 |
| Initially overvoltage 33/69 | 0.50 | 392.39 | 392.39 | 43 | 552 | 0.67424 | 0.75597 | 1.12970 |

### 6.14 Energy Management Value of Screening

For an energy-management journal, the key operating question is not only
whether the voltage interval is accurate. It is whether the interval helps
decide which DER scenarios should be passed to expensive AC-audited corrective
optimization. The following tables report screening-layer metrics over nominal
coverage levels and the corresponding proxy PV/load action quantities. The
PV/load quantities are induced by the screening flag and are not claimed to be
globally optimal dispatch.

| Method | Nominal coverage | Screened-safe ratio | AC calls avoided | Risky scenario recall | Post-screen miss rate | Bus recall | Missed buses | Width |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Boosting + global conformal | 0.95 | 0.21667 | 26 | 1.00000 | 0.00000 | 0.99891 | 1 | 0.00161 |
| VoltGuard | 0.95 | 0.21667 | 26 | 1.00000 | 0.00000 | 1.00000 | 0 | 0.00061 |
| Boosting + global conformal | 0.90 | 0.21667 | 26 | 1.00000 | 0.00000 | 0.99674 | 3 | 0.00110 |
| VoltGuard | 0.90 | 0.22500 | 27 | 1.00000 | 0.00000 | 0.99891 | 1 | 0.00046 |
| Boosting + global conformal | 0.80 | 0.22500 | 27 | 1.00000 | 0.00000 | 0.98806 | 11 | 0.00075 |
| VoltGuard | 0.80 | 0.22500 | 27 | 1.00000 | 0.00000 | 0.99891 | 1 | 0.00029 |

| Method | Nominal coverage | Available PV | Accepted PV proxy | Curtailed PV proxy | Relieved load proxy | Proxy action cost |
|---|---:|---:|---:|---:|---:|---:|
| Boosting + global conformal | 0.95 | 191.231 | 191.231 | 0.000 | 35.6416 | 35.6416 |
| VoltGuard | 0.95 | 191.231 | 191.231 | 0.000 | 35.6416 | 35.6416 |
| Boosting + global conformal | 0.90 | 191.231 | 191.231 | 0.000 | 35.6416 | 35.6416 |
| VoltGuard | 0.90 | 191.231 | 191.231 | 0.000 | 35.3345 | 35.3345 |
| Boosting + global conformal | 0.80 | 191.231 | 191.231 | 0.000 | 35.3345 | 35.3345 |
| VoltGuard | 0.80 | 191.231 | 191.231 | 0.000 | 35.3345 | 35.3345 |

At 90% nominal coverage, VoltGuard avoids one additional downstream AC call,
keeps perfect risky-scenario recall, narrows the mean interval by more than
half, and reduces missed bus-level violations from three to one. At 80%
nominal coverage, VoltGuard keeps the same screened-safe ratio as boosting
plus global conformal but misses ten fewer bus-level violations. In this
representative case, the selected risk flags trigger flexible-load relief
rather than PV curtailment, so accepted-PV proxy values remain unchanged while
the interval-width/missed-violation tradeoff changes. These results support the
paper's energy-management interpretation: VoltGuard is a tunable
pre-optimization screening layer for DER operating scenarios, not a substitute
for the corrective optimization itself.

The same screening-value audit is repeated over the three random seeds used in
the main statistical evaluation. This multi-seed view keeps the operating
interpretation intact: at 90% nominal coverage, VoltGuard avoids 27.33 AC
optimization calls on average, keeps scenario-level risky recall at 1.00000,
and has zero post-screening risky-scenario misses. Its mean bus-level missed
violations fall to 0.33, compared with 1.67 for boosting plus global conformal,
while the mean interval width is less than half as large.

| Method | Nominal coverage | Safe scenarios mean | AC calls avoided mean | Risky recall mean | Post-screen miss mean | Missed buses mean | Width mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| Boosting + global conformal | 0.90 | 27.00 | 27.00 | 1.00000 | 0.00000 | 1.67 | 0.00127 |
| VoltGuard | 0.90 | 27.33 | 27.33 | 1.00000 | 0.00000 | 0.33 | 0.00051 |

We also repeat the same primary-level screening audit across the four split
families used in the generalization study. The result should be read as
empirical operating evidence under the stated split protocols, not as an
unconditional conformal safety guarantee under arbitrary drift. Across random
interpolation, synthetic time-block, PV-penetration shift, and
topology-held-out transfer, VoltGuard keeps mean scenario-level risky recall at
1.00000 and mean post-screening risky-scenario miss rate at 0.00000. The number
of avoided AC calls changes with the split because the test-set composition and
risk prevalence change.

| Split | AC calls avoided mean | Risky recall mean | Post-screen miss mean | Missed buses mean | Width mean |
|---|---:|---:|---:|---:|---:|
| Random interpolation | 27.33 | 1.00000 | 0.00000 | 0.33 | 0.00051 |
| Synthetic time-block | 17.00 | 1.00000 | 0.00000 | 1.00 | 0.00055 |
| PV-penetration shift | 57.00 | 1.00000 | 0.00000 | 1.00 | 0.00081 |
| Topology-held-out 33-to-69 | 15.67 | 1.00000 | 0.00000 | 0.00 | 0.00203 |

A separate bidirectional transfer audit repeats the topology-held-out protocol
in both feeder directions. In 33-to-69 transfer, VoltGuard reduces RMSE from
0.00127 to 0.00068 p.u., narrows mean intervals from 0.00273 to 0.00203 p.u.,
and removes the remaining 0.33 mean missed bus-level violations relative to
boosting plus global conformal. In 69-to-33 transfer, both methods keep zero
missed risky scenarios; VoltGuard improves mean empirical coverage from
0.89282 to 0.90948 but has a slightly wider interval and slightly higher
false-alarm rate. The reverse direction is therefore reported as robustness
evidence and as a boundary on the sharpness claim, not as topology-invariant
certification.

| Transfer | Method | RMSE mean | Coverage mean | Width mean | Missed buses mean | Scenario recall mean | AC calls avoided mean |
|---|---|---:|---:|---:|---:|---:|---:|
| 33-to-69 | Boosting + global conformal | 0.00127 | 0.89716 | 0.00273 | 0.33 | 1.00000 | 15.67 |
| 33-to-69 | VoltGuard | 0.00068 | 0.90166 | 0.00203 | 0.00 | 1.00000 | 15.67 |
| 69-to-33 | Boosting + global conformal | 0.00076 | 0.89282 | 0.00214 | 0.00 | 1.00000 | 52.00 |
| 69-to-33 | VoltGuard | 0.00073 | 0.90948 | 0.00218 | 0.00 | 1.00000 | 52.33 |

### 6.15 Screened-Safe Release Audit

The previous table counts how many AC optimization calls can be avoided. A
stricter operating question is whether the scenarios released without AC audit
are actually safe. We therefore evaluate the released subset at the scenario
level and report the number of truly risky scenarios, released violation
severity, and released violating buses. This is a no-action audit: released
scenarios are not corrected by the downstream backend.

| Method | Protocol | Nominal coverage | Released scenarios | Safe-release precision | Released risky scenarios | Released severity share | Max released severity | Released violating buses | AC calls avoided |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LinDistFlow physical backbone | Point gate | - | 29 | 0.93103 | 2 | 0.00061 | 0.00092 | 6 | 29 |
| Boosting + global conformal | Point gate | - | 27 | 1.00000 | 0 | 0.00000 | 0.00000 | 0 | 27 |
| VoltGuard | Point gate | - | 27 | 1.00000 | 0 | 0.00000 | 0.00000 | 0 | 27 |
| Boosting + global conformal | Conformal interval | 0.90 | 26 | 1.00000 | 0 | 0.00000 | 0.00000 | 0 | 26 |
| VoltGuard | Conformal interval | 0.90 | 27 | 1.00000 | 0 | 0.00000 | 0.00000 | 0 | 27 |
| VoltGuard | Conformal interval | 0.80 | 27 | 1.00000 | 0 | 0.00000 | 0.00000 | 0 | 27 |

The same release audit is repeated over three random seeds at the primary
90% nominal conformal level:

| Method | Protocol | Released scenarios mean | Safe-release precision mean | Released risky mean | Released risky 95% CI | Released severity share mean | Released violating buses mean | Mean width |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| LinDistFlow physical backbone | Point gate | 29.33 | 0.94291 | 1.67 | 0.65333 | 0.00056 | 4.00 | 0.00000 |
| Boosting + global conformal | Conformal interval | 27.00 | 1.00000 | 0.00 | 0.00000 | 0.00000 | 0.00 | 0.00127 |
| VoltGuard | Conformal interval | 27.33 | 1.00000 | 0.00 | 0.00000 | 0.00000 | 0.00 | 0.00051 |

At 90% nominal coverage, VoltGuard releases 27 of 120 scenarios in the
representative split and 27.33 scenarios on average across seeds, while
releasing no truly risky scenario and no realized violation severity. The
LinDistFlow point-only gate releases slightly more scenarios but releases 1.67
risky scenarios on average. The audit therefore sharpens the operating claim:
VoltGuard is useful both as a high-risk prioritization layer and as a calibrated
screen for a clean low-risk subset under the stated split and calibration
protocol.

### 6.16 Screening-Budget Triage Value

This experiment adds a stricter operating-budget view. It ranks test scenarios by the
interval risk score and sends only a fixed fraction to the already audited AC
grid-search backend. Scenarios outside the budget receive no corrective action,
so the table separates prioritization value from the strength of the downstream
optimizer. With a 20% AC-call budget, VoltGuard sends 24 of 120 scenarios to
AC audit, avoids 96 calls, captures 52.59% of the realized voltage-violation
severity, and reduces total violation severity by 21.42%. A random 20% budget
captures only 19.98% of severity and reduces severity by 12.06%. The
post-policy violating-scenario count is not monotonically better for risk
ranking, because the most severe scenarios are also the hardest for the coarse
grid-search backend to fully correct; this supports the paper's claim that
VoltGuard is a prioritization front end, not a complete controller.

| Policy | Budget | AC calls | Calls avoided | Risky recall | Severity capture | Severity reduction | Post-policy violating scenarios | Post-policy violating buses | Action cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Random budget expectation | 0.20 | 24 | 96 | 0.20020 | 0.19975 | 0.12064 | 84.54 | 815.73 | 11.846 |
| Boosting + global conformal | 0.20 | 24 | 96 | 0.25806 | 0.52587 | 0.20789 | 93.00 | 848.00 | 17.465 |
| VoltGuard | 0.20 | 24 | 96 | 0.25806 | 0.52586 | 0.21416 | 93.00 | 839.00 | 18.050 |
| VoltGuard | 0.30 | 36 | 84 | 0.38710 | 0.69573 | 0.31973 | 93.00 | 791.00 | 27.182 |
| VoltGuard | 0.50 | 60 | 60 | 0.64516 | 0.90588 | 0.50842 | 84.00 | 586.00 | 44.949 |
| Oracle realized severity | 0.50 | 60 | 60 | 0.64516 | 0.90588 | 0.50842 | 84.00 | 586.00 | 45.039 |

The same budgeted triage calculation is then repeated over the three random
seeds using the saved seed-specific AC candidate grids. At the 20% AC-call
budget, VoltGuard avoids 96 scenario-level AC grid searches on average,
captures 0.34048 of realized pre-action severity, and reduces total severity
by 0.19708. This is a 0.13982 absolute severity-capture gain over random
budgeting, while keeping fewer post-policy violating scenarios and buses than
the LinDistFlow point-risk ranking. The comparison is intentionally nuanced:
LinDistFlow and oracle severity rankings capture more raw pre-action severity
at the same budget, but those severe cases are not always the cases for which
the coarse corrective grid produces the largest post-policy reduction. This is
why we report both severity capture and post-policy operating outcomes.

| Multi-seed policy | Budget | AC calls mean | Calls avoided mean | Risky recall mean | Severity capture mean | Severity reduction mean | Post-policy scenarios mean | Post-policy buses mean | Action cost mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Random budget expectation | 0.20 | 24.00 | 96.00 | 0.20043 | 0.20067 | 0.11613 | 83.80 | 766.91 | 11.838 |
| LinDistFlow point-risk | 0.20 | 24.00 | 96.00 | 0.25996 | 0.53084 | 0.18767 | 92.33 | 804.67 | 16.114 |
| VoltGuard interval-risk | 0.20 | 24.00 | 96.00 | 0.25996 | 0.34048 | 0.19708 | 86.33 | 651.67 | 18.577 |
| Oracle realized severity | 0.20 | 24.00 | 96.00 | 0.25996 | 0.53085 | 0.18558 | 92.33 | 807.67 | 15.919 |

### 6.17 Paired Statistical Evidence Audit

Because the main evidence combines split-level prediction metrics and
budgeted operating metrics, we add a paired statistical audit rather than a
single aggregate significance claim. For the prediction/screening table, each
paired unit is one split-seed combination from the four main 33/69 protocols
and seeds 7, 17, and 42. For each unit, VoltGuard with
topology+PV+loading-conditioned conformal calibration is compared against
boosting plus global conformal. For the operating table, each paired unit is a
seed at the 20% AC-call budget. We report mean paired deltas, bootstrap
confidence intervals, and the fraction of paired units with the preferred
direction; this is an empirical stability audit, not a distribution-free
hypothesis test under arbitrary nonstationarity.

| Experiment | Comparison | Metric | Preferred direction | Paired units | Delta mean | 95% CI low | 95% CI high | Better-unit fraction |
|---|---|---|---|---:|---:|---:|---:|---:|
| Main prediction/screening | VoltGuard minus boosting+global | RMSE | lower | 12 | -0.000848 | -0.001069 | -0.000654 | 1.00000 |
| Main prediction/screening | VoltGuard minus boosting+global | Average width | lower | 12 | -0.000645 | -0.000734 | -0.000561 | 1.00000 |
| Main prediction/screening | VoltGuard minus boosting+global | Violation recall | higher | 12 | 0.000892 | 0.000444 | 0.001363 | 0.58333 |
| Main prediction/screening | VoltGuard minus boosting+global | False-alarm rate | lower | 12 | -0.000809 | -0.001252 | -0.000291 | 0.83333 |
| Main prediction/screening | VoltGuard minus boosting+global | Missed violations | lower | 12 | -0.750000 | -1.166670 | -0.333333 | 0.58333 |
| Budgeted AC triage | VoltGuard minus random | Severity capture | higher | 3 | 0.139817 | 0.110381 | 0.169674 | 1.00000 |
| Budgeted AC triage | VoltGuard minus LinDistFlow | Post-policy violating buses | lower | 3 | -153.000000 | -157.000000 | -147.000000 | 1.00000 |

The paired audit supports two bounded claims. First, VoltGuard's topology-aware
residual plus conditioned conformal calibration consistently improves RMSE and
interval sharpness over the boosting+global baseline across all 12 split-seed
prediction units, while recall and missed-violation gains are positive on
average but not uniform in every unit. Second, under a 20% AC-call budget,
VoltGuard captures more realized severity than random budgeting in every seed
and leaves fewer post-policy violating buses than LinDistFlow point-risk in
every seed, despite LinDistFlow and oracle rankings capturing more raw
pre-action severity. This is the operating boundary: VoltGuard
is a calibrated front end whose value is measured by downstream triage and
post-policy audit outcomes, not by claiming universal optimal control.

### 6.18 Candidate-Action Screening Audit

Sections 6.18--6.20 are application extensions. They illustrate downstream use
of the calibrated risk score after the main method has already screened and
ranked scenarios. They should be read as supplementary operating evidence, not
as additional method claims.

The previous triage experiment decides which scenarios should be sent to the
downstream corrective backend. We also audit a finer operating question:
within a flagged scenario, can VoltGuard reduce the number of candidate
corrective actions that require AC power-flow evaluation? Each test scenario
has a nine-point action grid formed by load relief and PV curtailment in
0%, 10%, and 20% steps. Full AC grid search therefore audits 1080 candidate
actions over the 120 test scenarios. The candidate-action audit ranks these
actions using VoltGuard's predicted conformal interval risk before AC power
flow is run, sends only the top-k actions to AC audit, and then lets the AC
audit choose the best action within that reduced set. This is an AC-audit
pruning experiment, not a post-action conformal feasibility guarantee.

| Policy | Top-k actions | Candidate AC audits | Audits avoided | Full-best retained | Same action as full | Post-action violating scenarios | Extra violating scenarios | Post-action violating buses | Extra violating buses | Cost delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full AC grid search | 9 | 1080 | 0 | 1.00000 | 1.00000 | 51 | 0 | 398 | 0 | 0.000 |
| VoltGuard interval-risk | 1 | 120 | 960 | 0.74167 | 0.74167 | 51 | 0 | 398 | 0 | 14.551 |
| VoltGuard interval-risk | 3 | 360 | 720 | 0.90000 | 0.90000 | 51 | 0 | 398 | 0 | 7.237 |
| VoltGuard interval-risk | 5 | 600 | 480 | 0.93333 | 0.93333 | 51 | 0 | 398 | 0 | 3.172 |
| LinDistFlow point-risk | 3 | 360 | 720 | 0.94167 | 0.94167 | 52 | 1 | 400 | 2 | 4.662 |
| Cheapest-first | 3 | 360 | 720 | 0.36667 | 0.36667 | 81 | 30 | 826 | 428 | -49.142 |

The top-three VoltGuard candidate screen avoids 720 of 1080 candidate AC
audits, a 66.7% reduction, while matching full grid search on the number of
post-action violating scenarios and buses in this split. It pays a 7.237 MW
proxy action-cost increase because the reduced candidate set is more
conservative than the full-grid optimum. The contrast with cheapest-first
pruning is important for the energy-management claim: simply evaluating the
least intrusive actions first is computationally cheap but leaves 30 extra
violating scenarios and 428 extra violating buses. LinDistFlow point-risk
pruning is much stronger than cheapest-first but still leaves one extra
violating scenario and two extra violating buses at top-three. VoltGuard
therefore contributes a calibrated, data-corrected action-pruning signal for
the AC-audited backend; it still does not replace that backend.

We repeat the top-three candidate-pruning audit across the three random seeds.
For each seed, the full backend evaluates 1080 candidate AC power flows, while
top-three pruning evaluates 360 and avoids 720. VoltGuard matches the full
grid-search post-action violation count in all three seeds on average: mean
extra post-action violating scenarios and buses are both zero. The physics-only
LinDistFlow point-risk screen is close but leaves 0.67 extra violating
scenarios and 1.33 extra violating buses on average, while cheapest-first
leaves 29.33 extra violating scenarios and 364.33 extra violating buses. The
cost boundary is explicit: VoltGuard's top-three subset is more conservative,
with an 11.589 MW mean proxy action-cost increase relative to full grid search.

| Policy | Top-k actions | Candidate AC audits mean | Audits avoided mean | Full-best retained mean | Same action mean | Post-action violating scenarios mean | Extra violating scenarios mean | Extra violating buses mean | Cost delta mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full AC grid search | 9 | 1080 | 0 | 1.00000 | 1.00000 | 49.67 | 0.00 | 0.00 | 0.000 |
| VoltGuard interval-risk | 3 | 360 | 720 | 0.84167 | 0.84167 | 49.67 | 0.00 | 0.00 | 11.589 |
| LinDistFlow point-risk | 3 | 360 | 720 | 0.92500 | 0.92500 | 50.33 | 0.67 | 1.33 | 6.698 |
| Cheapest-first | 3 | 360 | 720 | 0.40000 | 0.40000 | 79.00 | 29.33 | 364.33 | -45.585 |

### 6.19 Risk-Cost Candidate-Action Tradeoff

The risk-first candidate screen above is intentionally conservative. For
energy management, however, the operator may also care about flexible-load
relief and PV-curtailment cost. We therefore add a post-hoc risk-cost
sensitivity audit. For each candidate action, a normalized VoltGuard risk score
is combined with a normalized proxy action cost,
$s^{act}=s^{risk}+\lambda c^{act}$, and the top-k candidates are AC-audited as
before. AC outcomes are used only for evaluation after the reduced candidate
set has been selected.

| Cost weight | Top-k actions | Candidate AC audits | Audits avoided | Full-best retained | Same action as full | Extra violating scenarios | Extra violating buses | Cost delta |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 3 | 360 | 720 | 0.90000 | 0.90000 | 0 | 0 | 6.884 |
| 0.10 | 3 | 360 | 720 | 0.95000 | 0.95000 | 0 | 0 | 4.913 |
| 0.20 | 3 | 360 | 720 | 0.95833 | 0.95833 | 0 | 0 | 2.429 |
| 0.30 | 3 | 360 | 720 | 0.99167 | 0.99167 | 0 | 0 | 0.467 |
| 0.50 | 3 | 360 | 720 | 1.00000 | 1.00000 | 0 | 0 | 0.000 |
| 1.00 | 3 | 360 | 720 | 0.99167 | 0.99167 | 1 | 2 | -0.251 |
| 1.50 | 3 | 360 | 720 | 0.71667 | 0.71667 | 9 | 124 | -16.904 |

The sensitivity curve shows why the paper should not claim a complete
controller. Cost weighting is useful up to a point: in this split,
$\lambda=0.5$ keeps the top-three audit budget, avoids 720 candidate AC
evaluations, matches the full-grid post-action violation count, and recovers
the full-grid action cost. Pushing the cost term too far starts to exchange
voltage security for lower action cost; at $\lambda=1.0$ the top-three screen
has one extra violating scenario and two extra violating buses. This is the
appropriate operating interpretation: VoltGuard provides a tunable risk signal
for corrective-search pruning, while AC audit remains responsible for final
action acceptance.

The risk-cost audit is also repeated over the same three random seeds used for
the multi-seed action-pruning table. For top-three pruning, the risk-first
setting already preserves the full-grid post-action violation outcome in every
seed, but it adds 10.746 MW of proxy action cost on average. A moderate
$\lambda=0.5$ keeps the 360-candidate AC audit budget and the same zero-extra
violation outcome across all seeds, while reducing the mean cost delta to
0.145 MW and matching the full-grid action in 99.72% of scenarios. Excessive
cost emphasis is again unsafe: at $\lambda=1.0$, the top-three screen adds
1.00 violating scenario and 2.67 violating buses on average.

| Cost weight | Top-k actions | Candidate AC audits mean | Audits avoided mean | Same action mean | Extra violating scenarios mean | Extra violating scenarios max | Extra violating buses mean | Cost delta mean |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 3 | 360 | 720 | 0.84167 | 0.00 | 0 | 0.00 | 10.746 |
| 0.20 | 3 | 360 | 720 | 0.91667 | 0.00 | 0 | 0.00 | 5.791 |
| 0.30 | 3 | 360 | 720 | 0.93611 | 0.00 | 0 | 0.00 | 3.978 |
| 0.50 | 3 | 360 | 720 | 0.99722 | 0.00 | 0 | 0.00 | 0.145 |
| 0.80 | 3 | 360 | 720 | 0.99444 | 0.33 | 1 | 1.33 | -0.195 |
| 1.00 | 3 | 360 | 720 | 0.98333 | 1.00 | 2 | 2.67 | -0.691 |

### 6.20 Consolidated Energy-Management Frontier

The previous sections report several operating views separately. To make the
energy-management consequence explicit, we assemble a consolidated frontier
from the completed audits. The table does not introduce new labels or a new
controller; it summarizes how risk tolerance, AC-audit budget, action-pruning
cost weight, and PV curtailment map to avoided AC work, post-policy risk, and
renewable-hosting proxies.

| Frontier | Operating setting | AC calls/audits avoided | Post-policy violating scenarios | Post-policy violating buses | Accepted PV | Action/load cost | Main tradeoff |
|---|---|---:|---:|---:|---:|---:|---|
| Conformal release | 90% nominal coverage | 27.33 AC calls | - | - | 222.52 MW | 36.26 MW | Releases a low-risk subset with zero missed risky scenarios; mean interval width is 0.000512 p.u. |
| Budgeted AC triage | 20% scenario budget | 96 AC calls | 86.33 | 651.67 | 222.52 MW | 18.58 MW | Gains 0.13982 severity capture over random budgeting while leaving fewer post-policy buses than LinDistFlow point-risk. |
| Candidate-action pruning | Top-3, $\lambda=0.5$ | 720 candidate AC audits | 49.67 | 381.33 | 222.52 MW | +0.15 MW vs full grid | Keeps zero extra violating buses while nearly recovering full-grid action cost. |
| High-PV hosting stress | 50% PV curtailment | - | 44 | 557 | 392.39 MW | 392.39 MW curtailed | Reduces overvoltage scenarios by 67.42% and overvoltage buses by 75.60% on initially overvoltage stress cases. |

This frontier is a compact application summary, not the main contribution. It
separates four decisions that a distribution operator might tune after receiving
VoltGuard's risk scores: low-risk release, budgeted AC triage, candidate-action
pruning, and PV-curtailment stress response. The paper's core remains
physics-informed residual learning plus calibrated voltage-risk screening for
AC-call reduction; AC audit or a replaceable OPF/MPC backend remains
responsible for corrective feasibility.

### 6.21 Operational Runtime Benchmark

The operational runtime benchmark separates offline fitting, online screening,
and downstream AC-audited grid search. The numbers are wall-clock measurements
from the local Python prototype and should be interpreted as relative evidence
for the two-stage workflow, not as optimized industrial implementation times.

| Workflow | Scenarios sent to AC | Seconds | ms/scenario | Speedup vs full AC |
|---|---:|---:|---:|---:|
| VoltGuard online screening only | 120 | 0.03046 | 0.25380 | 6796.17 |
| Full AC grid search on every scenario | 120 | 206.98291 | 1724.86 | 1.00 |
| VoltGuard-flagged scenarios then AC grid search | 93 | 160.44221 | 1725.19 | 1.29 |
| VoltGuard top-20% budget then AC grid search | 24 | 41.42704 | 1726.13 | 5.00 |

These results sharpen the computational claim. VoltGuard's online screening
cost is negligible relative to AC grid search, but high-recall calibrated
screening can still flag most scenarios under conservative nominal coverage.
The larger runtime value appears when the operator uses the interval risk score
for budgeted prioritization, where a 20% AC-call budget yields about 5x
wall-clock reduction while retaining the severity-capture behavior reported
above.

### 6.22 Scenario Risk-Ranking Quality

The two-stage operating interface also requires prioritization when the
operator cannot run AC-audited optimization on every forecasted scenario at
once. The ranking audit evaluates scenario-level ranking using the interval risk score
$\eta_t$. Ranking quality is measured by ROC-AUC, average precision (AP),
Spearman correlation between $\eta_t$ and realized voltage-violation severity,
top-20 severity capture, and bottom-10 safe-screen precision.

| Method | Variant | ROC-AUC | AP | Spearman severity | Top-20 severity capture | Bottom-10 safe precision |
|---|---|---:|---:|---:|---:|---:|
| VoltGuard topology-aware residual | global | 1.00000 | 1.00000 | 0.99992 | 0.45594 | 1.00000 |
| Boosting + global conformal | global | 1.00000 | 1.00000 | 0.99901 | 0.45581 | 1.00000 |
| VoltGuard topology-aware residual | topology+PV+loading | 1.00000 | 1.00000 | 0.99985 | 0.45594 | 1.00000 |
| Neural graph residual ablation | topology | 0.99084 | 0.99726 | 0.98573 | 0.45539 | 1.00000 |

This experiment supports the screening-layer interpretation but adds an
important nuance. The topology+PV+loading conditioned variant remains the main
screening model because it keeps the lowest missed bus-level violations while
using sharper intervals than global VoltGuard. For scenario ranking, the
global and conditioned VoltGuard scores are essentially tied; both dominate the
neural ablation on Spearman severity correlation and false-alarm behavior.

## 7. Discussion

The central result is a corrected claim, not a broader one. The best executed
model is not a neural graph residual. It is a physics-informed,
topology-aware residual learner with conditioned conformal calibration. This
makes the paper more defensible: the method's value comes from aligning the
residual features and calibration families with feeder and operating regime,
not from claiming that message passing alone solves voltage security.

The conformal guarantee is bounded. Split conformal prediction provides
finite-sample coverage under exchangeability of calibration and test samples.
Grid data can violate this assumption when topology, load regimes, PV
penetration, or time periods shift. The PV-shift and topology-held-out
experiments make that limitation visible rather than hiding it. VoltGuard
should therefore be used as a calibrated screening estimator under a stated
scenario family and recalibration protocol, not as a universal safety
certificate.

The screening interpretation is also bounded. The intervals can prioritize
scenarios and buses for downstream AC analysis, but they do not certify AC
feasibility, replace state estimation, or select final dispatch. OPF, MPC, and
AC power flow remain the authority for corrective action. This distinction is
important for reviewer interpretation: the paper's claim is sharper intervals
and fewer missed voltage-risk events than baseline screening methods, not a new
distribution-grid controller.

Model maintenance is part of the operating design. A deployed screen should
store every model version, feeder model, calibration family, and release/watch
decision, then sample released scenarios for periodic AC audit. Recalibration
should be triggered when rolling residuals exceed the calibration-family
threshold, when topology identifiers are unseen, when DER capacity or siting
changes materially, when reconductoring/regulator/capacitor settings change,
or when forecast distributions move outside the training envelope. In those
cases the DMS should disable release or fall back to a global conservative
radius until a fresh AC-audited calibration set is available.

Real-world validation remains the most important external gap. The present
evidence uses public IEEE-style test systems and synthetic operating scenarios;
it does not include an anonymized utility feeder, real SCADA/AMI streams, or an
OpenDSS/SMART-DS unbalanced feeder with regulator, capacitor, and phase
connectivity details. On real feeders, missing telemetry, phase imbalance,
equipment controls, and data-governance rules may dominate the residual
structure. The current results should therefore be read as a reproducible
method demonstration and screening benchmark, while utility-pilot validation is
required before operational deployment claims.

The present feeder models are balanced single-phase equivalents, so extension
to highly unbalanced three-phase distribution systems is not automatic. On
IEEE 123-bus or OpenDSS feeders, the LinDistFlow backbone would need a
phase-resolved branch-flow approximation with phase-specific voltage limits,
mutual coupling terms, regulator and capacitor states, and missing-phase
connectivity. The residual learner can still use the same philosophy, but its
features would become phase-indexed and equipment-aware, and the conformal
families would likely need to include regulator configuration, phase loading,
and feeder section. This is a limitation of the current 33/69 evidence.

## 8. Conclusion

This paper presents VoltGuard, a physics-informed topology-aware residual
learning framework with conformal calibration for voltage-risk screening in
active distribution networks. On IEEE 33-bus and IEEE 69-bus feeder scenarios,
the topology+PV+loading conditioned conformal variant improves missed-violation
and interval-sharpness behavior relative to global conformal calibration. The
work deliberately keeps neural graph residual learning as an ablation because
the executed neural model does not justify being the central claim. Future work
will extend the same residual-plus-conditioned-calibration framework to
unbalanced IEEE 123-bus/OpenDSS or SMART-DS feeders and evaluate recalibration
under larger topology and DER regime shifts.
