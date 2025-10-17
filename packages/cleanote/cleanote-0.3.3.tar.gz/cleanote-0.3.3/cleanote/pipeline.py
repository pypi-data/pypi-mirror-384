import logging
from typing import Iterable, Callable, Dict, List, Optional, Any

from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import spacy
import pandas as pd
import numpy as np
import warnings
import json
import re


logger = logging.getLogger(__name__)


class Pipeline:

    NLI_MODEL_NAME = "pritamdeka/PubMedBERT-MNLI-MedNLI"

    def __init__(self, dataset, model_h):
        self.dataset = dataset
        self.model_h = model_h
        self.dataset_h = None

        # Cache / état
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._nlp = None  # spaCy nlp
        self._tok = None  # HF tokenizer
        self._clf = None  # HF sequence classification model
        self._id2label: Optional[Dict[int, str]] = None

        self.SCI_MODEL_NAME = "en_core_sci_lg"  # ou "en_core_sci_sm"
        self.UMLS_MIN_SCORE = 0.0
        self._sci = None
        self._umls_cache = {}
        self._umls_doc_cache = {}

    # ------------------------- Orchestration -------------------------

    def apply(self):
        print("[Pipeline] Starting pipeline...")
        self.homogenize()
        self.verify_QuickUMLS()
        self.verify_NLI()
        self.verify_UMLS_summary_vs_source()
        print("[Pipeline] Pipeline completed.")
        return self.dataset_h

    # ------------------------- Homogénéisation -------------------------

    def homogenize(self):
        print("[Pipeline] Prompt for Homogenization:")
        if self.model_h.prompt:
            print(self.model_h.prompt)
        else:
            self.model_h.prompt = self.build_prompt_h()
            print(self.model_h.prompt)

        print("[Pipeline] Start Homogenization...")
        out_h_col = f"{self.dataset.field}__h"
        self.dataset_h = self.model_h.run(self.dataset, output_col=out_h_col)
        print("[Pipeline] Homogenization completed.")

    @staticmethod
    def build_prompt_h() -> str:
        return (
            "Analyze the document below and return a single, valid JSON object with exactly these keys:\n"
            "{\n"
            '  "Symptoms": [],\n'
            '  "MedicalConclusion": [],\n'
            '  "Treatments": [],\n'
            '  "Summary": ""\n'
            "}\n"
            "- If no information exists for a given key, return an empty array for that key.\n"
            "- The Summary must only use items already extracted above (no new facts).\n"
            "- Ensure the output is syntactically valid JSON.\n"
            "Document:\n"
        )

    # ------------------------- Vérifications -------------------------

    def _ensure_scispacy(self):
        if self._sci is not None:
            return self._sci

        try:
            import scispacy  # noqa: F401
            from scispacy.umls_linking import UmlsEntityLinker  # noqa: F401
        except Exception as e:
            raise RuntimeError(
                "SciSpaCy n'est pas installé (pip install scispacy)."
            ) from e

        # charge le modèle (lg -> fallback sm)
        try:
            self._sci = spacy.load(self.SCI_MODEL_NAME)
        except OSError:
            try:
                self._sci = spacy.load("en_core_sci_sm")
                print("[UMLS] Fallback → en_core_sci_sm (lg non installé)")
            except OSError as e:
                raise RuntimeError(
                    "Aucun modèle SciSpaCy trouvé. Installe en_core_sci_lg ou en_core_sci_sm."
                ) from e

        # ajoute le linker UMLS
        if "scispacy_linker" in self._sci.pipe_names:
            self._sci.remove_pipe("scispacy_linker")
        self._sci.add_pipe(
            "scispacy_linker",
            config={
                "resolve_abbreviations": True,
                "k": 30,
                "threshold": float(self.UMLS_MIN_SCORE),
            },
            last=True,
        )
        return self._sci

    def _norm_term(self, t: str) -> str:
        return re.sub(r"\s+", " ", (t or "").strip().lower())

    def _umls_match_bulk(self, terms: List[str]) -> Dict[str, bool]:
        """Retourne {terme_original -> True/False} selon présence d'au moins un CUI (score >= seuil)."""
        self._ensure_scispacy()
        # normalise + uniques
        mapping = {t: self._norm_term(t) for t in terms}
        uniq_norm = sorted(set(v for v in mapping.values() if v))
        to_run = [u for u in uniq_norm if u not in self._umls_cache]

        if to_run:
            docs = self._sci.pipe(to_run, batch_size=64, n_process=1)
            for key, doc in zip(to_run, docs):
                ok = False
                for ent in doc.ents:
                    kb = getattr(ent._, "kb_ents", [])
                    if kb:
                        best = max(score for _, score in kb)
                        if best >= float(self.UMLS_MIN_SCORE):
                            ok = True
                            break
                self._umls_cache[key] = ok

        # re-projette sur les termes d'origine
        return {t: self._umls_cache.get(mapping[t], False) for t in terms}

    def _extract_entity_list(self, row, field_name: str, out_h_col: str) -> List[str]:
        """
        Récupère la liste d'entités pour field_name ('Symptoms'/'MedicalConclusion'/'Treatments').
        Essaie d'abord la colonne directe; sinon parse le JSON dans out_h_col.
        """
        vals = row.get(field_name)
        # déjà une liste ?
        if isinstance(vals, list):
            return [str(x).strip() for x in vals if str(x).strip()]
        # string: tente JSON, sinon split simple
        if isinstance(vals, str) and vals.strip():
            try:
                parsed = json.loads(vals)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                parts = re.split(r"[;,]\s*", vals.strip())
                return [p for p in parts if p]
        # fallback: JSON homogénéisé
        payload = row.get(out_h_col)
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            if isinstance(payload, dict):
                arr = payload.get(field_name, [])
                if isinstance(arr, list):
                    return [str(x).strip() for x in arr if str(x).strip()]
        except Exception:
            pass
        return []

    def verify_QuickUMLS(self):
        """
        Vérification via SciSpaCy + UMLS linker.
        Pour chaque colonne (Symptoms, MedicalConclusion, Treatments), ajoute:
        *_umls_total, *_umls_matched, *_umls_match_rate, *_umls_loss_rate
        """
        print("[Pipeline] Starting UMLS verification (SciSpaCy linker)...")
        self._ensure_scispacy()

        df = self.dataset_h.data
        out_h_col = f"{self.dataset.field}__h"
        triplets = [
            ("Symptoms", "symptoms"),
            ("MedicalConclusion", "medicalconclusion"),
            ("Treatments", "treatments"),
        ]

        # crée colonnes résultat si absentes
        for _, short in triplets:
            for suffix in (
                "umls_total",
                "umls_matched",
                "umls_match_rate",
                "umls_loss_rate",
            ):
                col = f"{short}_{suffix}"
                if col not in df.columns:
                    df[col] = np.nan

        for idx, row in df.iterrows():
            for field, short in triplets:
                entities = self._extract_entity_list(row, field, out_h_col)
                total = len(entities)

                if total == 0:
                    matched = 0
                    match_rate = np.nan
                    loss_rate = np.nan
                else:
                    status = self._umls_match_bulk(entities)  # {term: bool}
                    matched = sum(1 for t in entities if status.get(t, False))
                    match_rate = matched / total
                    loss_rate = 1.0 - match_rate

                df.at[idx, f"{short}_umls_total"] = total
                df.at[idx, f"{short}_umls_matched"] = matched
                df.at[idx, f"{short}_umls_match_rate"] = match_rate
                df.at[idx, f"{short}_umls_loss_rate"] = loss_rate

            if (idx + 1) % 10 == 0:
                print(f"[UMLS] processed {idx+1}/{len(df)} rows...")

        print("[Pipeline] UMLS verification completed.")

    def verify_NLI(self):
        print("[Pipeline] Starting NLI verification...")
        self._ensure_nli()

        df = self.dataset_h.data
        text_col = self.dataset.field
        out_h_col = f"{self.dataset.field}__h"

        # Colonnes résultats
        for col in ("nli_ent_mean", "nli_neu_mean", "nli_con_mean"):
            if col not in df.columns:
                df[col] = np.nan

        for idx, row in df.iterrows():
            # Texte source
            src_text = (row.get(text_col) or "").strip()

            # Résumé/hypothèses
            summ_text = (row.get("Summary") or "").strip()
            if not summ_text and out_h_col in df.columns:
                try:
                    payload = row[out_h_col]
                    payload = (
                        json.loads(payload)
                        if isinstance(payload, str)
                        else (payload or {})
                    )
                    summ_text = (payload or {}).get("Summary", "") or ""
                except Exception:
                    pass
            summ_text = summ_text.strip()

            if not src_text or not summ_text:
                print(f"[Pipeline] Row {idx}: texte ou résumé vide, skip.")
                continue

            premises = self.decouper_texte_en_phrases(src_text)  # source
            hypotheses = self.decouper_texte_en_phrases(summ_text)  # résumé

            if not premises or not hypotheses:
                print(f"[Pipeline] Row {idx}: pas de phrases, skip.")
                continue

            matrice = self.generer_table(
                hypotheses,
                premises,
                lambda h, p: self.nli(p, h, return_probs=True),
            )

            avg = self.average(hypotheses, premises, matrice)

            df.at[idx, "nli_ent_mean"] = avg["entailment"]
            df.at[idx, "nli_neu_mean"] = avg["neutral"]
            df.at[idx, "nli_con_mean"] = avg["contradiction"]

            print(
                f"[Pipeline] Row {idx} → entail={avg['entailment']}, neutral={avg['neutral']}, contra={avg['contradiction']}"
            )

        print("[Pipeline] NLI verification completed.")

    # _ensure_nlp : sans newline_boundaries
    def _ensure_nlp(self):
        if self._nlp is None:
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                self._nlp = spacy.blank("en")
            if "sentencizer" in self._nlp.pipe_names:
                self._nlp.remove_pipe("sentencizer")
            self._nlp.add_pipe(
                "sentencizer",
                config={"punct_chars": [".", "!", "?"]},
                first=True,
            )

    def nli(self, premise: str, hypothesis: str, return_probs: bool = True) -> Dict:
        self._ensure_nli()
        inputs = self._tok(
            premise,
            hypothesis,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        ).to(self.device)

        self._clf.eval()
        with torch.inference_mode():
            logits = self._clf(**inputs).logits.squeeze(0)

        probs_t = torch.softmax(logits, dim=-1).cpu()
        probs = probs_t.tolist()
        labels = [self._id2label[i] for i in range(len(probs))]
        pred_idx = int(torch.argmax(probs_t))
        pred_label = self._id2label[pred_idx]

        return {
            "premise": premise,
            "hypothesis": hypothesis,
            "prediction": pred_label,
            "probs": (
                dict(zip(labels, [round(float(p), 4) for p in probs]))
                if return_probs
                else None
            ),
        }

    # ------------------------- spaCy utils -------------------------

    def _get_summary_text(self, row, out_h_col: str) -> str:
        summ_text = (row.get("Summary") or "").strip()
        if not summ_text and out_h_col in row:
            payload = row.get(out_h_col)
            try:
                if isinstance(payload, str):
                    payload = json.loads(payload)
                if isinstance(payload, dict):
                    summ_text = (payload.get("Summary") or "").strip()
            except Exception:
                pass
        return summ_text

    def _umls_cuis_from_text(self, text: str) -> set:
        """Retourne l'ensemble des CUIs UMLS détectés dans un texte (via scispacy_linker), avec cache."""
        self._ensure_scispacy()
        key = self._norm_term(text)
        if key in self._umls_doc_cache:
            return self._umls_doc_cache[key]

        cuis = set()
        if text and text.strip():
            doc = self._sci(text)
            for ent in doc.ents:
                kb = getattr(ent._, "kb_ents", [])
                if kb:
                    # garde les CUIs dont le score passe le seuil
                    for cui, score in kb:
                        if score >= float(self.UMLS_MIN_SCORE):
                            cuis.add(cui)
                            # on peut break si on ne veut que le meilleur ; ici on garde tous >= seuil
        self._umls_doc_cache[key] = cuis
        return cuis

    def verify_UMLS_summary_vs_source(self):
        """
        Compare les entités UMLS (CUIs) du résumé vs la note complète.
        Colonnes créées :
        umls_src_total, umls_sum_total, umls_overlap_count,
        umls_match_rate, umls_loss_rate, umls_creation_rate, umls_jaccard
        """
        print("[Pipeline] Starting UMLS Summary vs Source verification...")
        self._ensure_scispacy()

        df = self.dataset_h.data
        text_col = self.dataset.field
        out_h_col = f"{self.dataset.field}__h"

        # Crée les colonnes si absentes
        new_cols = [
            "umls_src_total",
            "umls_sum_total",
            "umls_overlap_count",
            "umls_match_rate",
            "umls_loss_rate",
            "umls_creation_rate",
            "umls_jaccard",
        ]
        for c in new_cols:
            if c not in df.columns:
                df[c] = np.nan

        for idx, row in df.iterrows():
            src_text = (row.get(text_col) or "").strip()
            sum_text = self._get_summary_text(row, out_h_col)

            # CUIs
            src_cuis = self._umls_cuis_from_text(src_text)
            sum_cuis = self._umls_cuis_from_text(sum_text)

            src_total = len(src_cuis)
            sum_total = len(sum_cuis)
            overlap = len(src_cuis & sum_cuis)

            # Rates (NaN si denom == 0)
            match_rate = (overlap / sum_total) if sum_total > 0 else np.nan
            loss_rate = ((src_total - overlap) / src_total) if src_total > 0 else np.nan
            creation_rate = (
                ((sum_total - overlap) / sum_total) if sum_total > 0 else np.nan
            )

            # Jaccard (optionnel, utile pour un score global de similarité)
            denom = len(src_cuis | sum_cuis)
            jaccard = (overlap / denom) if denom > 0 else np.nan

            # Écriture
            df.at[idx, "umls_src_total"] = src_total
            df.at[idx, "umls_sum_total"] = sum_total
            df.at[idx, "umls_overlap_count"] = overlap
            df.at[idx, "umls_match_rate"] = match_rate
            df.at[idx, "umls_loss_rate"] = loss_rate
            df.at[idx, "umls_creation_rate"] = creation_rate
            df.at[idx, "umls_jaccard"] = jaccard

            if (idx + 1) % 10 == 0:
                print(f"[UMLS SxS] processed {idx+1}/{len(df)} rows...")

        print("[Pipeline] UMLS Summary vs Source verification completed.")

    def decouper_texte_en_phrases(self, texte: str) -> List[str]:
        self._ensure_nlp()
        txt = self._normalize_for_sentences(texte or "")
        doc = self._nlp(txt)
        return [s.text.strip() for s in doc.sents if s.text.strip()]

    # normalisation des sauts de ligne (remplace ta version)
    def _normalize_for_sentences(self, texte: str) -> str:
        if not texte:
            return ""
        t = texte.replace("\r\n", "\n").replace("\r", "\n").replace("\\n", "\n")
        # ponctuation + \n -> ponctuation + espace
        t = re.sub(r"([.!?])\s*\n\s*", r"\1 ", t)
        # \n sans ponctuation avant -> point + espace
        t = re.sub(r"(?<![.!?])\s*\n\s*", ". ", t)
        # espaces multiples -> 1
        t = re.sub(r"\s{2,}", " ", t).strip()
        return t

    # ------------------------- NLI model load -------------------------

    def _ensure_nli(self):
        if self._tok is None or self._clf is None:
            self._tok = AutoTokenizer.from_pretrained(self.NLI_MODEL_NAME)
            self._clf = AutoModelForSequenceClassification.from_pretrained(
                self.NLI_MODEL_NAME
            )
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._clf = self._clf.to(self.device)
            self._id2label = {
                i: lbl.lower() for i, lbl in self._clf.config.id2label.items()
            }
        return self._tok, self._clf, self._id2label

    # ------------------------- Tableaux & métriques -------------------------
    def _row_metrics_dict(self, row) -> Dict[str, Optional[float]]:
        """Récupère proprement les métriques d'une ligne, en gardant None si absentes."""

        def g(col):
            return row[col] if col in row and pd.notna(row[col]) else None

        return {
            # NLI
            "NLI – entailment": g("nli_ent_mean"),
            "NLI – neutral": g("nli_neu_mean"),
            "NLI – contradiction": g("nli_con_mean"),
            # UMLS (résumé vs source)
            "UMLS – match rate (SUM∩SRC / SUM)": g("umls_match_rate"),
            "UMLS – loss rate (SRC−SUM / SRC)": g("umls_loss_rate"),
            "UMLS – creation rate (SUM−SRC / SUM)": g("umls_creation_rate"),
            "UMLS – Jaccard": g("umls_jaccard"),
            # UMLS par colonne (facultatif ; commente si tu veux moins de barres)
            "Symptoms – match rate": g("symptoms_umls_match_rate"),
            "Symptoms – loss rate": g("symptoms_umls_loss_rate"),
            "MedConclusion – match rate": g("medicalconclusion_umls_match_rate"),
            "MedConclusion – loss rate": g("medicalconclusion_umls_loss_rate"),
            "Treatments – match rate": g("treatments_umls_match_rate"),
            "Treatments – loss rate": g("treatments_umls_loss_rate"),
        }

    def save_row_stats_image(self, idx: int, path: Optional[str] = None) -> str:
        """
        Sauve un graphique PNG des métriques (NLI + UMLS) pour la ligne `idx`.
        Retourne le chemin du fichier généré.
        """
        df = self.dataset_h.data
        if idx < 0 or idx >= len(df):
            raise IndexError(f"idx {idx} hors limites (0..{len(df)-1})")

        row = df.iloc[idx]
        metrics = self._row_metrics_dict(row)

        # Prépare données (on garde l'ordre du dict)
        labels = list(metrics.keys())
        values = [metrics[k] for k in labels]

        # Filtre les métriques totalement absentes (None)
        filtered = [(lab, val) for lab, val in zip(labels, values) if val is not None]
        if not filtered:
            raise ValueError("Aucune métrique disponible pour cette ligne.")

        labels, values = zip(*filtered)
        # clip [0,1] si besoin
        values = [max(0.0, min(1.0, float(v))) for v in values]

        # Chemin
        if path is None:
            path = f"row_{idx}_stats.png"

        # --- Matplotlib : un seul plot, pas de style/couleurs spécifiques (consignes) ---
        plt.figure(figsize=(10, max(4, 0.4 * len(labels))))  # hauteur auto
        y_pos = range(len(labels))
        plt.barh(y_pos, values)  # pas de couleur spécifique
        plt.yticks(y_pos, labels)
        plt.xlim(0, 1)
        plt.xlabel("Score [0–1]")
        title_left = row.get(self.dataset.field, "")
        title_left = (
            (title_left[:80] + "…")
            if isinstance(title_left, str) and len(title_left) > 80
            else title_left
        )
        plt.title(f"Stats – ligne {idx} | {title_left}")

        # annotations sur les barres
        for y, v in enumerate(values):
            plt.text(
                v + 0.01 if v <= 0.9 else v - 0.15,
                y,
                f"{v:.3f}",
                va="center",
                ha="left" if v <= 0.9 else "right",
            )

        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    # (optionnel) nom de fichier safe
    def _safe_filename(self, s: str) -> str:
        s = re.sub(r"[^\w\-.]+", "_", (s or "").strip())[:60]
        return s or "row"

    def _metric_category(self, label: str) -> str:
        """Retourne la catégorie d'une métrique pour colorer."""
        if label.startswith("NLI"):
            return "NLI"
        if label.startswith("UMLS – "):
            return "UMLS"
        if label.startswith("Symptoms"):
            return "Symptoms"
        if label.startswith("MedConclusion"):
            return "MedicalConclusion"
        if label.startswith("Treatments"):
            return "Treatments"
        return "Other"

    def _category_color(self, cat: str) -> str:
        """Couleur par catégorie (palette tab:* de Matplotlib)."""
        palette = {
            "NLI": "tab:blue",
            "UMLS": "tab:orange",
            "Symptoms": "tab:green",
            "MedicalConclusion": "tab:purple",
            "Treatments": "tab:red",
            "Other": "tab:gray",
        }
        return palette.get(cat, "tab:gray")

    def save_row_stats_image(self, idx: int, path: Optional[str] = None) -> str:
        """
        Sauve un graphique PNG des métriques (NLI + UMLS) pour la ligne `idx`, avec couleurs par catégorie.
        """
        df = self.dataset_h.data
        if idx < 0 or idx >= len(df):
            raise IndexError(f"idx {idx} hors limites (0..{len(df)-1})")

        row = df.iloc[idx]
        metrics = self._row_metrics_dict(row)

        labels = list(metrics.keys())
        values = [metrics[k] for k in labels]

        # filtre None
        items = [(lab, val) for lab, val in zip(labels, values) if val is not None]
        if not items:
            raise ValueError("Aucune métrique disponible pour cette ligne.")

        labels, values = zip(*items)
        values = [max(0.0, min(1.0, float(v))) for v in values]

        # couleurs par catégorie
        cats = [self._metric_category(lab) for lab in labels]
        colors = [self._category_color(c) for c in cats]

        # chemin
        if path is None:
            title_left = row.get(self.dataset.field, "")
            base = self._safe_filename(
                title_left if isinstance(title_left, str) else f"row_{idx}"
            )
            path = f"{base}_row_{idx}_stats.png"

        # plot
        plt.figure(figsize=(10, max(4, 0.45 * len(labels))))
        y_pos = range(len(labels))
        plt.barh(y_pos, values, color=colors)
        plt.yticks(y_pos, labels)
        plt.xlim(0, 1)
        plt.xlabel("Score [0–1]")

        title_left = row.get(self.dataset.field, "")
        title_left = (
            (title_left[:80] + "…")
            if isinstance(title_left, str) and len(title_left) > 80
            else title_left
        )
        plt.title(f"Stats – ligne {idx} | {title_left}")

        # annotations
        for y, v in enumerate(values):
            plt.text(
                v + 0.01 if v <= 0.9 else v - 0.15,
                y,
                f"{v:.3f}",
                va="center",
                ha="left" if v <= 0.9 else "right",
            )

        # légende
        legend_items = []
        seen = set()
        for cat, col in zip(cats, colors):
            if cat not in seen:
                legend_items.append(Patch(facecolor=col, edgecolor="none", label=cat))
                seen.add(cat)
        if legend_items:
            plt.legend(handles=legend_items, loc="lower right")

        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def generer_table(
        self,
        lignes: Iterable,
        colonnes: Iterable,
        fonction: Callable[[Any, Any], Dict],
    ) -> List[List[Dict]]:
        return [[self._prettier(fonction(i, j)) for j in colonnes] for i in lignes]

    @staticmethod
    def _prettier(res: Dict) -> Dict:
        probs = (res or {}).get("probs", {}) or {}
        # Les clés sont déjà normalisées en minuscules dans nli()
        for k in ("entailment", "neutral", "contradiction"):
            probs.setdefault(k, None)
        return probs

    def average(self, lignes: Iterable, colonnes: Iterable, matrice: List[List[Dict]]):
        df = pd.DataFrame(matrice, index=list(lignes), columns=list(colonnes))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            entailments = df.applymap(
                lambda x: x.get("entailment") if isinstance(x, dict) else None
            )

        best_col_per_row = entailments.idxmax(axis=1)

        best_ent_vals, best_neu_vals, best_con_vals = [], [], []
        for i in df.index:
            best_col = best_col_per_row.loc[i]
            cell = df.loc[i, best_col]
            if isinstance(cell, dict):
                best_ent_vals.append(cell.get("entailment"))
                best_neu_vals.append(cell.get("neutral"))
                best_con_vals.append(cell.get("contradiction"))

        mean_best_ent = float(np.nanmean(best_ent_vals)) if best_ent_vals else None
        mean_best_neu = float(np.nanmean(best_neu_vals)) if best_neu_vals else None
        mean_best_con = float(np.nanmean(best_con_vals)) if best_con_vals else None

        print(
            f"Moyennes — entailment={mean_best_ent}, neutral={mean_best_neu}, contradiction={mean_best_con}"
        )
        return {
            "entailment": mean_best_ent,
            "neutral": mean_best_neu,
            "contradiction": mean_best_con,
        }

    # ------------------------- Export -------------------------

    def to_excel(self) -> str:
        """Exporte le DataFrame `dataset_h.data` en Excel."""
        path = "dataset_h.xlsx"
        self.dataset_h.data.to_excel(path, index=False)
        return path
