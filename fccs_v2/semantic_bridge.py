from __future__ import annotations

from typing import Dict, List

from .labels import DEDUCTIVE_LABELS, INTENT_LABELS, TRUTH_LABELS


def _get_prob_index(labels: List[str], wanted: str) -> int:
    return labels.index(wanted)


def semantic_bridge(prediction: Dict[str, object]) -> Dict[str, object]:
    intent = prediction["intent"]
    truth = prediction["truth"]
    deductive = prediction["deductive"]
    emotion = prediction["emotion"]
    confidence = prediction["confidence"]

    intent_probs = intent["probs"]
    truth_probs = truth["probs"]
    deduct_probs = deductive["probs"]
    valence = float(emotion["valence"])
    arousal = float(emotion["arousal"])
    conf = float(confidence["value"])

    safety_p = intent_probs[_get_prob_index(INTENT_LABELS, "safety")]
    factual_p = intent_probs[_get_prob_index(INTENT_LABELS, "factual")]
    explanatory_p = intent_probs[_get_prob_index(INTENT_LABELS, "explanatory")]
    empathetic_p = intent_probs[_get_prob_index(INTENT_LABELS, "empathetic")]
    exploratory_p = intent_probs[_get_prob_index(INTENT_LABELS, "exploratory")]
    clarifying_p = intent_probs[_get_prob_index(INTENT_LABELS, "clarifying")]

    false_p = truth_probs[_get_prob_index(TRUTH_LABELS, "false")]
    unknown_p = truth_probs[_get_prob_index(TRUTH_LABELS, "unknown")]
    contradiction_p = deduct_probs[_get_prob_index(DEDUCTIVE_LABELS, "contradicts")]
    insufficient_p = deduct_probs[_get_prob_index(DEDUCTIVE_LABELS, "insufficient")]

    acc = min(1.0, 0.12 + 0.58 * max(false_p, contradiction_p) + 0.10 * insufficient_p)
    ins = min(1.0, 0.18 + 0.55 * (1.0 - conf) + 0.25 * safety_p)
    pfc = min(1.0, max(0.0, 0.22 + 0.30 * (factual_p + explanatory_p) + 0.18 * conf - 0.08 * arousal))
    amg = min(1.0, max(0.0, 0.08 + 0.55 * max(0.0, -valence) * max(0.25, arousal) + 0.12 * empathetic_p))
    hpc = min(1.0, 0.10 + 0.35 * (exploratory_p + clarifying_p) + 0.12 * unknown_p)

    if safety_p > 0.42 or ins > 0.74:
        planner = "slow_down_ground_check_risk"
        rationale = "Nízká jistota nebo safety intent aktivuje opatrný režim."
    elif acc > 0.62:
        planner = "resolve_conflict_before_answer"
        rationale = "Deduktivní nebo pravdivostní konflikt zvyšuje ACC."
    elif empathetic_p > 0.45 or (empathetic_p > 0.35 and valence < 0.0):
        planner = "lead_with_empathy_then_structure"
        rationale = "Empatický intent a afektivní signály posouvají odpověď k citlivému vedení."
    elif exploratory_p + clarifying_p > 0.55:
        planner = "ask_targeted_question_then_expand"
        rationale = "Průzkumný nebo vyjasňovací mód podporuje dotaz před detailním rozšířením."
    else:
        planner = "structured_answer_with_confidence_note"
        rationale = "Převažuje informační mód a systém může dát přímo strukturovanou odpověď."

    return {
        "bio_state": {
            "ACC_conflict": round(acc, 4),
            "INS_salience": round(ins, 4),
            "PFC_control": round(pfc, 4),
            "AMG_distress": round(amg, 4),
            "HPC_context": round(hpc, 4),
        },
        "planner": planner,
        "rationale": rationale,
    }
