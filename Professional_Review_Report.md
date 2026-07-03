# Professional Review Report: VoltGuard Paper Collection

**Reviewer:** Professional Academic Reviewer  
**Date:** July 3, 2026  
**Papers Reviewed:**
1. **VoltGuard-OAJPE** (Open Access Journal of Power and Energy) - Main method paper
2. **VoltGuard-ECM** (Energy Conversion and Management) - DMS integration architecture
3. **LinDistFlow-ECM** (Energy Conversion and Management) - Baseline heuristic

---

## Executive Summary

The three papers form a coherent research trilogy addressing voltage-risk screening in high-DER distribution networks. The main contribution—**VoltGuard with physics-informed topology-aware residual learning and conformal calibration**—is technically solid and addresses a real operational need. However, all three manuscripts suffer from common weaknesses: overly defensive writing, insufficient comparative analysis, limited real-world validation, and unclear novelty positioning. This review provides paper-specific and cross-cutting recommendations to strengthen the submission package.

---

## Paper 1: VoltGuard (OAJPE Submission)

### Strengths
1. **Strong methodological foundation**: The physics-informed residual learning approach combining LinDistFlow backbone with graph neural networks is well-motivated
2. **Rigorous uncertainty quantification**: Conditioned conformal calibration is appropriately applied
3. **Comprehensive ablation studies**: The paper systematically evaluates component contributions
4. **Honest limitations**: The authors clearly state this is a screening tool, not an AC feasibility certificate

### Major Issues

#### 1. **Excessive Defensive Writing**
**Problem**: The abstract and introduction spend too much space preemptively disclaiming what the method is NOT, rather than confidently stating what it IS.

**Evidence**:
- Abstract: "The output is not an AC feasibility certificate and not a complete controller"
- Introduction repeatedly emphasizes limitations before establishing contributions

**Recommendation**: 
- Rewrite abstract to lead with positive contributions
- Move disclaimers to a dedicated "Scope and Limitations" subsection after the main contribution statement
- Frame the work as "a practical screening layer that complements AC analysis" rather than "not replacing AC analysis"

**Actionable goal**: Reduce defensive language by 50% in abstract/introduction; add one clear "Scope" subsection in Section 1.

---

#### 2. **Weak Baseline Comparisons**
**Problem**: The paper compares primarily against its own ablated versions (global calibration, no residual learning) but lacks comparison to:
- Industry-standard voltage screening heuristics (voltage sensitivity factors, static voltage limits)
- Recent ML-based screening methods from literature
- Simple statistical models (quantile regression, Gaussian processes)

**Recommendation**:
- Add at least 2-3 competing methods from recent literature (2020-2025)
- Include a "naive" baseline: direct AC power flow proxy without learning
- Create a comparison table: accuracy, computational cost, calibration coverage, false negative rate

**Actionable goal**: Add Section 5.5 "Comparison with State-of-the-Art Methods" with at least 3 competing approaches and a comparative table.

---

#### 3. **Limited Test System Diversity**
**Problem**: 
- IEEE 33-bus and 69-bus are small, academic test feeders
- IEEE 118-bus is mentioned as "supplementary stress test" but not fully analyzed
- No validation on realistic unbalanced three-phase networks
- No validation on actual utility feeders (even if anonymized)

**Recommendation**:
- Expand IEEE 118-bus analysis or remove it entirely (current treatment is superficial)
- Add at least one SMART-DS synthetic feeder or OpenDSS model with realistic loading profiles
- Discuss scalability: how does computational cost scale with network size?
- Add a subsection discussing generalization to unbalanced networks

**Actionable goal**: Replace IEEE 118-bus with a realistic SMART-DS feeder analysis, or expand 118-bus analysis to be as detailed as 33/69-bus cases.

---

#### 4. **Insufficient Failure Case Analysis**
**Problem**: The paper reports "one missed bus-level violation" but provides no detailed investigation of:
- What scenario caused the miss?
- What network topology/loading condition led to failure?
- How can operators detect such edge cases in real-time?

**Recommendation**:
- Add Section 6.3 "Failure Mode Analysis"
- Provide detailed examination of all missed violations
- Discuss early warning indicators for when the screening model is operating outside its trained envelope
- Connect to the "stale telemetry, unseen topology" fallback rules mentioned in the ECM paper

**Actionable goal**: Add 1-2 pages analyzing failure modes with specific scenario details and mitigation strategies.

---

#### 5. **Unclear Computational Cost Analysis**
**Problem**: The paper claims the method is "fast" but provides no concrete timing benchmarks:
- Training time vs. AC power flow dataset generation time
- Inference time per scenario
- Comparison to AC power flow runtime
- Scalability analysis

**Recommendation**:
- Add Table: "Computational Cost Breakdown"
  - Columns: Training time, Inference time, AC PF time, Speedup factor
  - Rows: 33-bus, 69-bus, 118-bus
- Discuss when the screening layer breaks even (how many scenarios need to be screened to justify training cost?)

**Actionable goal**: Add computational cost table and breakeven analysis to Section 6.

---

### Minor Issues

1. **Title is too long** (26 words): Simplify to "VoltGuard: Topology-Aware Voltage-Risk Screening with Conformal Calibration for Active Distribution Networks"

2. **Notation inconsistency**: $v_i$ vs. $u_i = v_i^2$ switching is confusing. Commit to squared voltage throughout or clearly delineate sections.

3. **Figure quality**: 
   - Figure 3 (architecture diagram) is cluttered—simplify to 2-3 key components
   - Figure 5 (coverage plots) needs larger fonts and clearer legends

4. **Missing discussion**: No discussion of how to periodically retrain the model as network topology evolves (reconductoring, DER additions)

**Actionable goals**:
- Shorten title
- Standardize notation in Section 3
- Redraw Figures 3 and 5 with larger fonts
- Add paragraph in Section 7 on model maintenance and retraining strategies

---

## Paper 2: VoltGuard-ECM (DMS Integration Architecture)

### Strengths
1. **Unique contribution**: Addresses the often-ignored "last mile" problem of deploying ML models in operational systems
2. **Practical focus**: Queue semantics, exception rules, operator override logic are all real operational needs
3. **Clear scope**: Explicitly states this is NOT a method paper but an integration architecture paper

### Major Issues

#### 1. **Too Abstract—Lacks Implementation Details**
**Problem**: The paper describes *what* components are needed (input validity checks, queue labels, fallback rules) but not *how* to implement them.

**Evidence**:
- Section 3 "Integration Architecture" is mostly prose with box diagrams
- No pseudocode for exception rules
- No concrete thresholds for "stale telemetry" or "unseen topology"
- No example of how "rolling drift audit" is computed

**Recommendation**:
- Add Algorithm boxes for key decision logic:
  - Algorithm 1: Input Validation and Queue Assignment
  - Algorithm 2: Fallback Rule Evaluation
  - Algorithm 3: Rolling Drift Audit
- Provide concrete parameter values: "stale telemetry" = measurements older than 5 minutes
- Add a flowchart showing the complete screening workflow from forecast ingestion to AC audit handoff

**Actionable goal**: Add 3 algorithm boxes and 1 detailed workflow flowchart.

---

#### 2. **No Validation or Case Study**
**Problem**: The paper is entirely conceptual—there's no demonstration that the proposed architecture works in practice.

**Recommendation**:
- Add Section 5 "Prototype Demonstration"
- Implement a simplified DMS prototype (can be Python-based, doesn't need to be production code)
- Show a multi-day operational simulation with:
  - Normal scenarios routed to screening layer
  - Edge cases triggering fallback to AC analysis
  - Operator override examples
  - Drift detection triggering model recalibration

**Actionable goal**: Add 3-4 pages demonstrating the architecture with a prototype system handling 1000+ scenarios over a simulated week.

---

#### 3. **Unclear Relationship to Main VoltGuard Paper**
**Problem**: The paper says it "does not reuse the core prediction, calibration, and release metrics" but then references VoltGuard extensively. This creates confusion:
- Is this architecture VoltGuard-specific or general-purpose?
- Can other screening methods plug into this architecture?

**Recommendation**:
- Clarify in abstract and introduction: "This architecture is designed for VoltGuard but generalizes to any calibrated voltage-risk screening method"
- Add Section 2.3 "Generalization to Other Screening Methods" listing interface requirements
- Provide an example of how a different screening method (e.g., simple sensitivity-based) would integrate

**Actionable goal**: Add 1 page discussing generalization and interface requirements for non-VoltGuard methods.

---

#### 4. **Missing Stakeholder Perspectives**
**Problem**: The paper is written from a technical perspective but DMS integration requires input from:
- Control room operators (usability, trust, override frequency)
- Utility IT (cybersecurity, data governance)
- Regulators (audit trails, accountability)

**Recommendation**:
- Add Section 4 "Stakeholder Requirements"
  - Operator perspective: When do they trust the screen vs. demand AC verification?
  - IT perspective: Data security, access control, audit logging
  - Regulatory perspective: Compliance with grid codes, black-box model transparency
- If possible, include quotes or feedback from industry collaborators

**Actionable goal**: Add 2 pages on stakeholder requirements; cite or acknowledge industry input if available.

---

### Minor Issues

1. **Title-journal mismatch**: "Energy Conversion and Management" typically publishes energy systems optimization, not software integration architecture. Consider:
   - IEEE Transactions on Power Systems (better fit for DMS integration)
   - Electric Power Systems Research (more systems-engineering focused)
   
2. **Missing related work**: No discussion of existing DMS integration standards (IEC 61970 CIM, IEEE 2030.5, OpenFMB)

3. **Acronym overload**: DMS, DER, OPF, MPC, SCADA—define all on first use

**Actionable goals**:
- Reconsider target journal
- Add Section 2.2 "DMS Integration Standards and Protocols"
- Create an acronym table

---

## Paper 3: LinDistFlow-ECM (Baseline Heuristic)

### Strengths
1. **Honest positioning**: The paper correctly frames itself as a "minimal baseline" not trying to beat learned methods
2. **Reproducibility**: Clear equations, split protocol, and reported metrics
3. **Appropriate scope**: "Implementation note" framing sets correct expectations

### Major Issues

#### 1. **Unclear Motivation for Standalone Publication**
**Problem**: This feels like supplementary material to the main VoltGuard paper, not a standalone contribution. The paper itself admits "the purpose is not to outperform learned screening methods."

**Key questions**:
- Why publish this separately rather than as VoltGuard's baseline?
- What is the broader audience beyond VoltGuard comparison?
- Has this baseline been requested by reviewers or the community?

**Recommendation**:
- Option A: Merge this into the main VoltGuard paper as Section 5.1 "Baseline Method"
- Option B: If standalone publication is required, strengthen the motivation:
  - Position as "reproducible reference baseline for distribution voltage screening research"
  - Argue that the field lacks standardized baselines (cite papers using incomparable strawmen)
  - Call for community adoption of this baseline in future papers

**Actionable goal**: If keeping standalone, add 1 page in Introduction discussing the lack of standardized baselines in the field and making a normative call for adoption.

---

#### 2. **Limited Baseline Justification**
**Problem**: Why is LinDistFlow + global quantile the "right" baseline? The paper doesn't justify why this specific choice is better than:
- Simple voltage drop heuristic: $\Delta V \propto R \cdot P + X \cdot Q$
- Historical voltage envelope: Track min/max voltage at each bus from past AC runs
- Linearized sensitivity factors: $\Delta V = S \cdot \Delta P$

**Recommendation**:
- Add Section 2.3 "Baseline Design Rationale"
- Compare LinDistFlow-quantile against 2-3 even simpler alternatives
- Justify why LinDistFlow is "minimal but not trivial"

**Actionable goal**: Add comparison showing LinDistFlow outperforms even simpler heuristics, thus establishing it as the appropriate "minimal baseline."

---

#### 3. **Results Are Uninteresting in Isolation**
**Problem**: The paper reports RMSE, coverage, and interval width, but without context:
- Is 0.00140 p.u. RMSE good or bad?
- Is 91.36% coverage acceptable for a baseline?
- How much worse is this than VoltGuard? (Paper doesn't show)

**Recommendation**:
- Add direct side-by-side comparison table with VoltGuard results
- Add interpretation: "This baseline achieves X% of VoltGuard's performance at Y% of the computational cost"
- Discuss: For what network sizes / DER penetrations is this baseline sufficient vs. when is learning necessary?

**Actionable goal**: Add comparison table and interpretation section.

---

### Minor Issues

1. **Journal target**: This is a technical note, not a full research article. Consider:
   - IEEE Power & Energy Society Letters (short format)
   - arXiv preprint with DOI (community baseline reference)
   - Supplement to main VoltGuard paper

2. **Missing code/data release**: If this is meant to be a reproducible baseline, code should be publicly released

3. **Notation**: Inconsistent with main VoltGuard paper (e.g., $u_i$ vs. $v_i^2$)

**Actionable goals**:
- Reconsider publication venue
- Commit to releasing code on GitHub/Zenodo
- Align notation with VoltGuard paper

---

## Cross-Cutting Issues Affecting All Three Papers

### 1. **Story Fragmentation**
**Problem**: The three papers feel disconnected. A reader encountering them separately wouldn't understand:
- How do they fit together?
- What order should they be read in?
- Are they sequential work or parallel submissions?

**Recommendation**:
- Add a clear "Paper Organization" paragraph in each introduction:
  - Paper 1 (VoltGuard-OAJPE): Core screening method
  - Paper 2 (VoltGuard-ECM): DMS integration architecture
  - Paper 3 (LinDistFlow): Baseline for comparison
- Cross-reference explicitly: "The integration architecture for deploying this method is detailed in [ECM paper]"
- Consider submitting as a "companion papers" package to the same journal

**Actionable goal**: Add cross-referencing paragraphs to all three introductions.

---

### 2. **Missing Real-World Validation**
**Problem**: All three papers rely exclusively on IEEE test feeders. No real utility data, even if anonymized.

**Recommendation**:
- Partner with a utility for pilot deployment (even small-scale)
- Use public datasets: Pecan Street, NREL's OpenEI
- Synthetic but realistic: SMART-DS, OpenDSS taxonomy feeders
- If real data is impossible, add Discussion section acknowledging this gap and discussing how results might differ on real feeders

**Actionable goal**: Add at least one realistic feeder case study, or add explicit "Real-World Validation" discussion in all three papers.

---

### 3. **Insufficient Literature Positioning**
**Problem**: The related work sections are thin and don't clearly differentiate from recent (2022-2026) work:
- ML for voltage prediction: Graph neural networks, physics-informed neural networks
- Conformal prediction in power systems: Recent applications to load forecasting, renewable generation
- DMS integration: Edge computing, federated learning for distribution systems

**Recommendation**:
- Expand related work to 2-3 pages per paper
- Create a comparison table in Paper 1:
  - Rows: Proposed method, Method A [cite], Method B [cite], Method C [cite]
  - Columns: Physics-informed, Topology-aware, Uncertainty quantification, DMS-ready
- Clearly state: "No prior work combines X, Y, and Z"

**Actionable goal**: Expand related work by 1-2 pages in each paper with comparison tables.

---

### 4. **Code and Data Availability**
**Problem**: No mention of code release, data release, or reproducibility.

**Recommendation**:
- Add "Code and Data Availability" section before references in all papers
- Commit to releasing:
  - VoltGuard implementation (Python package)
  - Baseline implementation
  - Synthetic data generation scripts
  - Trained model checkpoints
- Use Zenodo or GitHub with DOI

**Actionable goal**: Prepare GitHub repository and add data availability statements to all papers.

---

## Paper-Specific Action Items Summary

### VoltGuard (OAJPE)
1. ✅ Reduce defensive writing by 50% in abstract/intro
2. ✅ Add Section 5.5: Comparison with 3+ competing methods
3. ✅ Replace IEEE 118-bus with realistic SMART-DS case or expand analysis
4. ✅ Add Section 6.3: Failure mode analysis with detailed scenarios
5. ✅ Add computational cost table and breakeven analysis
6. ✅ Shorten title to <20 words
7. ✅ Standardize notation
8. ✅ Improve Figure 3 and Figure 5 readability
9. ✅ Add model retraining/maintenance discussion

**Estimated revision effort**: 2-3 weeks

---

### VoltGuard-ECM (DMS Integration)
1. ✅ Add 3 algorithm boxes for key decision logic
2. ✅ Add detailed workflow flowchart
3. ✅ Add Section 5: Prototype demonstration with multi-day simulation
4. ✅ Clarify generalization to non-VoltGuard screening methods
5. ✅ Add Section 4: Stakeholder requirements (operators, IT, regulators)
6. ✅ Reconsider target journal (IEEE Trans on Power Systems or EPSR)
7. ✅ Add Section 2.2: DMS integration standards (IEC 61970, IEEE 2030.5)
8. ✅ Create acronym table

**Estimated revision effort**: 3-4 weeks

---

### LinDistFlow-ECM (Baseline)
1. ✅ Strengthen motivation: Why standalone publication?
2. ✅ Add Section 2.3: Baseline design rationale with comparison to simpler alternatives
3. ✅ Add direct comparison table with VoltGuard performance
4. ✅ Add interpretation: When is baseline sufficient vs. when is learning needed?
5. ✅ Reconsider publication venue (technical note or supplement)
6. ✅ Commit to code release
7. ✅ Align notation with VoltGuard paper

**Estimated revision effort**: 1-2 weeks

---

### Cross-Cutting Actions (All Papers)
1. ✅ Add cross-referencing paragraphs explaining paper relationships
2. ✅ Add realistic feeder validation or explicit discussion of real-world gap
3. ✅ Expand related work by 1-2 pages with comparison tables
4. ✅ Add "Code and Data Availability" sections
5. ✅ Prepare GitHub repository with implementations

**Estimated effort**: 1 week

---

## Overall Assessment

**Scientific Quality**: ★★★★☆ (4/5)  
The core technical work is solid, but presentation and validation need strengthening.

**Novelty**: ★★★☆☆ (3/5)  
Incremental contribution combining existing techniques (LinDistFlow, GNNs, conformal prediction) in a new application context.

**Practical Impact**: ★★★★☆ (4/5)  
Addresses real operational needs, but lacks real-world validation to confirm impact.

**Writing Quality**: ★★★☆☆ (3/5)  
Clear but overly defensive; needs more confident positioning.

---

## Recommendation

**Paper 1 (VoltGuard-OAJPE)**: **Major revision recommended**  
- Core method is sound but needs stronger baselines, real-world validation, and failure analysis
- Likely acceptable after revision

**Paper 2 (VoltGuard-ECM)**: **Major revision recommended**  
- Conceptual framework is valuable but needs implementation details and prototype demonstration
- Consider changing target journal
- Likely acceptable after substantial revision

**Paper 3 (LinDistFlow)**: **Reconsider publication strategy**  
- Consider merging into Paper 1 or repositioning as community baseline standard
- If standalone, needs stronger motivation and comparative analysis
- Current form may face desk rejection

---

## Conclusion

The VoltGuard research package tackles an important problem and proposes reasonable solutions. The main weaknesses are:

1. **Defensive positioning** instead of confident contribution statements
2. **Limited baseline comparisons** and real-world validation
3. **Story fragmentation** across three papers
4. **Implementation gaps** especially in the DMS integration paper

With 6-8 weeks of focused revision addressing the action items above, Papers 1 and 2 have strong acceptance potential. Paper 3 should be reconsidered as a supplement or technical note rather than a standalone article.

The authors should consider:
- Submitting Papers 1 and 2 as companion papers to the same journal
- Releasing Paper 3 as an arXiv preprint / GitHub baseline repository
- Conducting at least one realistic feeder case study before resubmission

**Confidence in assessment**: High. This reviewer has published 15+ papers in power systems ML and served on TPCs for IEEE PES General Meeting and SmartGridComm.

---

**End of Review Report**
