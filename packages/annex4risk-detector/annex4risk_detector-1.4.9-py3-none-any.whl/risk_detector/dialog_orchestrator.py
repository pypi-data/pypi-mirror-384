"""Simple dialog orchestrator for CLI demo with AI-generated questionnaires."""
from __future__ import annotations

import uuid
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import json

from . import models
from .evaluators.jsonlogic_eval import evaluate_rule
from .auto_rules import build_annex3_index
from sqlalchemy import text as sql_text


# Dynamic risk classification based on database features
def classify_from_answers(answers: dict) -> dict:
    """Classify risk dynamically based on database features and answers."""
    if not answers:
        return {"category": "not_high_risk", "score": 0.0, "legal_refs": [], "exception_applied": False, "obligations": []}
    
    # если пользователь выбрал "вне Annex III", считаем, что подпункт не выбран
    if answers.get("annex3_area") == "AnnexIII.none":
        answers = dict(answers)          # не мутируем исходный объект в БД
        answers.pop("annex3_item", None)
    
    # If no database URL provided, use default
    db_url = os.getenv('ANNEX4AC_DB_URL') or os.getenv('DB_URL') or "sqlite:///risk.db"
    
    # Create database connection
    if db_url.startswith("sqlite"):
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(db_url, pool_recycle=3600, pool_size=5)
    
    Session = sessionmaker(bind=engine)
    
    try:
        with Session() as db:
            # ——— Legally correct, data-driven classifier (AI Act) ———
            features = {f.key: f for f in db.execute(select(models.RiskFeature)).scalars()}
            questions = {q.feature_key: q for q in db.execute(select(models.RiskQuestion)).scalars()}
            constraints = list(db.execute(select(models.PolicyConstraint)).scalars())
            annex3 = build_annex3_index(db, table_name=os.environ.get("ANNEX_TABLE","rules"))
            all_items = {code for items in annex3["items"].values() for code,_ in items}
            # (Annex I ссылки можем тянуть при необходимости, сейчас не используем)

            legal_refs: list[str] = []
            exception_applied = False
            risk_factors: list[str] = []
            obligations: set[str] = set()

            def _truthy(v):
                if isinstance(v, bool): return v
                if v is None: return False
                if isinstance(v, (list, dict, tuple, set)): return len(v) > 0
                if isinstance(v, str): return v.strip() != ""
                return True

            # Dynamic obligations: evaluate obligation_rules table against answers + outcome context
            def _compute_obligations_dynamic(outcome: dict) -> list[str]:
                """
                Evaluate obligation_rules (LLM-generated) against current answers + derived vars.
                Returns compact 'code: label — role [anchor]' strings for UI; role optional; keep data-driven only.
                """
                ctx = dict(answers)
                ctx["outcome_category"] = outcome.get("category")
                ctx["exception_applied"] = bool(outcome.get("exception_applied"))
                items = []
                try:
                    rows = db.execute(sql_text("SELECT name, trigger_dsl, legal_bases, actions, actors FROM obligation_rules")).fetchall()
                    for name, trig_json, bases_json, acts_json, actors_json in rows:
                        try:
                            trig = json.loads(trig_json or "{}") if isinstance(trig_json, str) else (trig_json or {})
                        except Exception:
                            trig = {}
                        if evaluate_rule(trig, ctx):
                            try:
                                bases = json.loads(bases_json or "[]") if isinstance(bases_json, str) else (bases_json or [])
                            except Exception:
                                bases = []
                            try:
                                acts = json.loads(acts_json or "[]") if isinstance(acts_json, str) else (acts_json or [])
                            except Exception:
                                acts = []
                            actors = []
                            try:
                                actors = json.loads(actors_json or "[]") if isinstance(actors_json, str) else (actors_json or [])
                            except Exception:
                                actors = []
                            role = (actors[0] if actors else "").strip()
                            for a in acts:
                                code = str((a or {}).get("code", "")).strip()
                                label = str((a or {}).get("label", "")).strip()
                                anchor = (bases[0] if bases else "").strip()
                                if code and label:
                                    text = f"{code}: {label}"
                                    if role:
                                        text += f" — {role}"
                                    if anchor:
                                        text += f" [{anchor}]"
                                    items.append(text)
                except Exception:
                    pass
                # de-dup while preserving order
                seen, uniq = set(), []
                for it in items:
                    if it not in seen:
                        uniq.append(it)
                        seen.add(it)
                return uniq

            # map DB option ids for scope exclusions
            RND_PRE_MARKET_KEYS = {"RnD_activity", "research_testing_pre_market_RnD_activity"}

            # ——— Article 2 early scope exclusions (before Art.5/6/50) ———
            sx_raw = answers.get("scope_exclusion")
            if _truthy(sx_raw):
                sx_values = sx_raw if isinstance(sx_raw, (list, tuple, set)) else [sx_raw]
                sx_set = {str(v) for v in sx_values if v is not None}

                if "national_security_defence" in sx_set:
                    return {
                        "category": "out_of_scope",
                        "score": 0.0,
                        "legal_refs": ["Article 2(3)"],
                        "exception_applied": False,
                        "risk_factors": ["scope_exclusion"],
                        "obligations": [],
                    }

                if any(s.startswith("intl_coop_law_judici") for s in sx_set) and _truthy(answers.get("intl_coop_adequate_safeguards")):
                    return {
                        "category": "out_of_scope",
                        "score": 0.0,
                        "legal_refs": ["Article 2(4)"],
                        "exception_applied": False,
                        "risk_factors": ["scope_exclusion"],
                        "obligations": [],
                    }

                if (sx_set & RND_PRE_MARKET_KEYS):
                    rwt = _truthy(answers.get("real_world_testing_planned") or answers.get("real_world_testing"))
                    if not rwt:
                        return {
                            "category": "out_of_scope",
                            "score": 0.0,
                            "legal_refs": ["Article 2(8)"],
                            "exception_applied": False,
                            "risk_factors": ["scope_exclusion"],
                            "obligations": [],
                        }

                if "personal_non_professional" in sx_set:
                    return {
                        "category": "out_of_scope",
                        "score": 0.0,
                        "legal_refs": ["Article 2(10)"],
                        "exception_applied": False,
                        "risk_factors": ["scope_exclusion"],
                        "obligations": [],
                    }

                if "research_only_use" in sx_set:
                    return {
                        "category": "out_of_scope",
                        "score": 0.0,
                        "legal_refs": ["Article 2(6)"],
                        "exception_applied": False,
                        "risk_factors": ["scope_exclusion"],
                        "obligations": [],
                    }

            # 0) Разделяем constraints по правовым основаниям:
            def _is_a63(c):
                lbs = (c.legal_bases or [])
                return any(isinstance(lb, str) and "Article 6(3)" in lb for lb in lbs)
            pre_constraints  = [c for c in constraints if not _is_a63(c)]
            a63_constraints  = [c for c in constraints if _is_a63(c)]

            # 0a) Применяем "ранние" ограничения (ст.5, ст.6(1)/Annex I и др., но не ст.6(3))
            pre_fired = []
            for c in pre_constraints:
                try:
                    if evaluate_rule(c.trigger, answers):
                        pre_fired.append(c)
                except Exception:
                    pass
            if any(c.effect == "force_prohibited" for c in pre_fired):
                res = {
                    "category": "prohibited",
                    "score": 1.0,
                    "legal_refs": sorted(set(["Article 5"] + sum([c.legal_bases or [] for c in pre_fired], []))),
                    "exception_applied": False,
                    "risk_factors": ["constraint:force_prohibited"],
                    "obligations": [],
                }
                return res

            if any(c.effect == "force_high_risk" for c in pre_fired):
                res = {
                    "category": "high_risk",
                    "score": 1.0,
                    "legal_refs": sorted(set(sum([c.legal_bases or [] for c in pre_fired], []))),
                    "exception_applied": False,
                    "risk_factors": ["constraint:force_high_risk"],
                    "obligations": [],
                }
                res["obligations"] = _compute_obligations_dynamic(res)
                return res

            # Art. 6(1) path: safety component / product in Annex I + third-party conformity assessment
            annex1_covered = _truthy(answers.get("annex1_safety_component") or answers.get("annex1_product"))
            annex1_b = _truthy(answers.get("third_party_assessment"))
            if annex1_covered and annex1_b:
                refs = ["Article 6(1)", "Annex I"]
                if _truthy(answers.get("annex1_act_ref")):
                    refs.append(str(answers.get("annex1_act_ref")))
                res = {
                    "category": "high_risk",
                    "score": 1.0,
                    "legal_refs": sorted(set(refs)),
                    "exception_applied": False,
                    "risk_factors": ["annex1_path"],
                    "obligations": [],
                }
                res["obligations"] = _compute_obligations_dynamic(res)
                return res

            # Annex III item selected → high-risk (Art. 6(2)), если нет снижения по 6(3)
            annex3_item = answers.get("annex3_item")
            if isinstance(annex3_item, str) and annex3_item in all_items:
                category = "high_risk"
                legal_refs.append(annex3_item)
                risk_factors.append(f"annex3:{annex3_item}")

                # 1) Применяем ТОЛЬКО здесь ограничения по ст.6(3) (включая "always_high_risk_profiling")
                a63_fired = []
                for c in a63_constraints:
                    try:
                        if evaluate_rule(c.trigger, answers):
                            a63_fired.append(c)
                    except Exception:
                        pass
                # Сначала жёсткие эффекты:
                if any(c.effect == "force_prohibited" for c in a63_fired):
                    return {
                        "category": "prohibited",
                        "score": 1.0,
                        "legal_refs": sorted(set(["Article 6(3)"] + sum([c.legal_bases or [] for c in a63_fired], []))),
                        "exception_applied": False,
                        "risk_factors": ["constraint:force_prohibited","annex3"],
                        "obligations": [],
                    }
                if any(c.effect == "force_high_risk" for c in a63_fired):
                    out = {
                        "category": "high_risk",
                        "score": 1.0,
                        "legal_refs": sorted(set(sum([c.legal_bases or [] for c in a63_fired], []))),
                        "exception_applied": False,
                        "risk_factors": ["constraint:force_high_risk","annex3"],
                        "obligations": [],
                    }
                    out["obligations"] = _compute_obligations_dynamic(out)
                    return out

                a63 = answers.get("a6_conditions") or []
                if isinstance(a63, list) and len(a63) > 0:
                    # при попытке «снизить» учитываем ТОЛЬКО а63-ограничения
                    blocks_downgrade = any(
                        c.effect in ("force_high_risk","force_prohibited","disallow_a6_relief")
                        for c in a63_fired
                    )
                    if not blocks_downgrade:
                        category = "not_high_risk"
                        exception_applied = True
                        legal_refs.append("Article 6(3)")
                res = {
                    "category": category,
                    "score": 1.0 if category == "high_risk" else 0.0,
                    "legal_refs": sorted(set(legal_refs)),
                    "exception_applied": exception_applied,
                    "risk_factors": risk_factors,
                    "obligations": [],
                }
                res["obligations"] = _compute_obligations_dynamic(res)
                # No hard-coded obligations here; rely solely on obligation_rules
                return res

            # Removed area-only high-risk classification: without a specific Annex III item,
            # classification falls through to the default not_high_risk unless other constraints fire.

            # Art. 2(12) (open-source) contains an explicit caveat: the Regulation still applies when
            # the system triggers high-risk, Article 5 prohibitions, or Article 50 transparency duties.
            foss = "open_source_release"
            rnd = "RnD_activity"
            personal = "personal_non_professional"

            sx_raw = answers.get("scope_exclusion")
            foss_triggered = False
            if _truthy(sx_raw):
                sx_values = sx_raw if isinstance(sx_raw, (list, tuple, set)) else [sx_raw]
                sx_set = {str(v) for v in sx_values if v is not None}
                foss_triggered = foss in sx_set

            if foss_triggered:
                art50 = (
                    _truthy(answers.get("generates_synthetic_content")) or
                    _truthy(answers.get("ai_interacts_with_persons")) or
                    _truthy(answers.get("uses_emotion_or_biometric"))
                )
                high_risk_flag = (
                    (annex1_covered and annex1_b) or
                    (isinstance(answers.get("annex3_item"), str) and answers.get("annex3_item") in all_items)
                )
                banned_flag = any(c.effect == "force_prohibited" for c in pre_fired)

                if not (high_risk_flag or banned_flag or art50):
                    return {
                        "category": "out_of_scope",
                        "score": 0.0,
                        "legal_refs": ["Article 2(12)"],
                        "exception_applied": False,
                        "risk_factors": ["scope_exclusion"],
                        "obligations": [],
                    }

            # No Annex III / Article 5 / Annex I triggers → not_high_risk (no legal risk type in AI Act for "minimal")
            out = {
                "category": "not_high_risk",
                "score": 0.0,
                "legal_refs": [],
                "exception_applied": False,
                "risk_factors": [],
                "obligations": [],
            }
            out["obligations"] = _compute_obligations_dynamic(out)
            return out
            
    except Exception as e:
        # Fallback to not_high_risk if database access fails
        return {
            "category": "not_high_risk", 
            "score": 0.0, 
            "legal_refs": [], 
            "exception_applied": False,
            "obligations": [],
            "error": f"Database error: {str(e)}"
        }


class DialogOrchestrator:
    def __init__(self, db_url: str):
        if db_url.startswith("sqlite"):
            self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        else:
            self.engine = create_engine(db_url, pool_recycle=3600, pool_size=5)
        self.Session = sessionmaker(bind=self.engine)

    def start_session(self, customer_id: str = None) -> str:
        with self.Session() as db:
            # Get current questionnaire version from meta_kv
            a_hash = db.execute(sql_text("SELECT value FROM meta_kv WHERE key='annex3_hash'")).scalar() or "unknown"
            l_hash = db.execute(sql_text("SELECT value FROM meta_kv WHERE key='legal_hash'")).scalar() or "unknown"
            version = f"{a_hash[:12]}+{l_hash[:12]}"
            
            session_id = str(uuid.uuid4())
            chat = models.ChatSession(
                id=session_id, customer_id=customer_id, rule_snapshot_version=version
            )
            db.add(chat)
            db.commit()
            return session_id

    def _get_missing_required_features(self, features, questions, answers):
        """
        Return required features that are currently *visible* under gating and still unanswered.
        This prevents blocking on required fields that are not yet gated-in.
        """
        NONE_CODE = "AnnexIII.none"
        missing: list[str] = []
        for q in sorted(questions, key=lambda q: getattr(q, "priority", 0)):
            f = features.get(q.feature_key)
            if not f:
                continue
            if q.feature_key in answers:
                continue
            if q.gating and not evaluate_rule(q.gating, answers):
                continue
            # новое правило: если вне Annex III, annex3_item не обязателен
            if q.feature_key == "annex3_item":
                area = answers.get("annex3_area")
                if area == NONE_CODE:
                    continue
                # Если у выбранной области нет подпунктов (после фильтра по префиксу) — не блокируем required
                if isinstance(area, str) and f and isinstance(f.options, list):
                    filtered = [opt for opt in f.options if isinstance(opt, str) and opt.startswith(area + ".")]
                    if len(filtered) == 0:
                        continue
            if getattr(f, "required", False):
                missing.append(q.feature_key)
        return missing

    def _visible_unanswered(self, questions, answers):
        """List feature_keys for questions that are currently visible (gating passes) and unanswered."""
        out = []
        for q in questions:
            if q.feature_key in answers:
                continue
            if q.gating and not evaluate_rule(q.gating, answers):
                continue
            out.append(q.feature_key)
        return out

    def _get_next_question(self, questions, features, answers):
        """Get the next question to ask based on priority and gating."""
        NONE_CODE = "AnnexIII.none"
        for q in sorted(questions, key=lambda q: getattr(q, "priority", 0)):
            if q.feature_key in answers:
                continue
            if q.gating and not evaluate_rule(q.gating, answers):
                continue

            f = features.get(q.feature_key)
            if not f:
                continue

            # СКРЫВАЕМ второй вопрос если выбран "вне Annex III"
            if q.feature_key == "annex3_item":
                area = answers.get("annex3_area")
                if area == NONE_CODE:
                    continue  # пропускаем этот вопрос полностью

            result = {
                "feature_key": q.feature_key,
                "prompt": q.prompt_en or f.prompt_en,
                "type": f.type,
                "options": (f.options or []),
            }

            labels = getattr(f, "option_labels", None)
            if labels:
                result["option_labels"] = labels

            if q.feature_key == "annex3_item":
                area = answers.get("annex3_area")
                if area:
                    filtered = [opt for opt in f.options if opt.startswith(area + ".")]
                    if filtered:
                        result["options"] = filtered
                    else:
                        # Если у выбранной области нет подпунктов — прячем карточку полностью
                        continue

            return result
        return None

    def next_question(self, session_id: str):
        with self.Session() as db:
            chat = db.get(models.ChatSession, session_id)
            if not chat:
                raise RuntimeError(f"Chat session not found: {session_id}")
            
            # Load AI-generated features and questions
            features = {f.key: f for f in db.execute(select(models.RiskFeature)).scalars()}
            questions = list(db.execute(select(models.RiskQuestion).order_by(models.RiskQuestion.priority)).scalars())
            answers = {a.feature_key: a.value for a in chat.answers}
            
            # Get current questionnaire version (consistent with start_session)
            a_hash = db.execute(sql_text("SELECT value FROM meta_kv WHERE key='annex3_hash'")).scalar() or "unknown"
            l_hash = db.execute(sql_text("SELECT value FROM meta_kv WHERE key='legal_hash'")).scalar() or "unknown"
            version = f"{a_hash[:12]}+{l_hash[:12]}"

            def finalize():
                """Finalize the session with risk classification."""
                outcome = classify_from_answers(answers)
                # Нормализация на всякий случай: legacy "limited_risk" → "not_high_risk"
                if outcome.get("category") == "limited_risk":
                    outcome["category"] = "not_high_risk"
                reasoning = {"outcome": outcome, "answers": answers}
                res = models.RiskOutcome(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    rule_snapshot_version=version,
                    category=outcome["category"],
                    score=outcome["score"],
                    reasoning=reasoning,
                    legal_refs=outcome["legal_refs"],
                    exception_applied=outcome["exception_applied"],
                    obligations=outcome.get("obligations", []),
                )
                db.add(res)
                db.commit()
                return {"outcome": outcome, "answers": answers}

            # Generic early-finish rule:
            # if no gated question remains visible (i.e., nothing to ask now), finalize.
            visible_still_unanswered = self._visible_unanswered(questions, answers)
            if not visible_still_unanswered:
                return finalize()

            # Find next question to ask
            next_q = self._get_next_question(questions, features, answers)
            if next_q:
                return next_q

            # If no next question, check if any required (and *visible*) features remain; otherwise finalize
            missing = self._get_missing_required_features(features, questions, answers)
            if missing:
                raise RuntimeError(f"Missing required answers for: {', '.join(missing)}")

            return finalize()

    def submit_answer(self, session_id: str, feature_key: str, value):
        with self.Session() as db:
            if not db.get(models.ChatSession, session_id):
                raise RuntimeError(f"Chat session not found: {session_id}")
            ans = models.ChatAnswer(
                id=str(uuid.uuid4()),
                session_id=session_id,
                feature_key=feature_key,
                value=value,
            )
            db.add(ans)
            db.commit()
