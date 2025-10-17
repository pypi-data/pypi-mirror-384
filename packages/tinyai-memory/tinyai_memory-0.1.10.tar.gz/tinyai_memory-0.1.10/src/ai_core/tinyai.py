# ai_core/tinyai.py

import math
import random
import hashlib
from typing import Dict, List, Tuple, Any
from django.db import transaction
import re, math
from sympy import sympify, simplify, Eq

Number = float
SparseVec = Dict[int, Number]

# ---------- NumPy ----------
import numpy as np

# ---------- Semantic Embeddings (optional) ----------
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("⚠️ sentence-transformers not installed, disabling semantic embedding.")
    SentenceTransformer = None

# Load a small, CPU-friendly model only once (if available)
if SentenceTransformer:
    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
else:
    _embedder = None


def _load_models():
    """
    Lazy import of Django models to avoid importing them before settings are configured.
    Call this ONLY after ai_core.setup() has run (or when Django settings are already configured).
    """
    from .models import Memory, MemoryItem, Weight, MemoryLink, ActivityLog
    return Memory, MemoryItem, Weight, MemoryLink, ActivityLog


class TinyAIMemory:
    def __init__(self, dims: int = 1000, lr: float = 0.05, threshold: float = 3.0, memory: Any | None = None):
        # NOTE: we use Any for 'memory' to avoid importing models at type-check time
        self.dims = dims
        self.lr = lr
        self.threshold = threshold

        Memory, MemoryItem, Weight, MemoryLink, ActivityLog = _load_models()

        # Use most recent memory or create one
        self.memory = memory or Memory.objects.order_by("-id").first() or Memory.objects.create()
        self.learn_count = 0
        self.reflect_every = 10  # run reflection after every 10 learns

    # ---------- Hashing (sparse) ----------
    def _char_value(self, ch: str) -> float:
        return (ord(ch) % 32) / 32.0

    def text_to_sparseN(self, text: str, dims: int | None = None) -> SparseVec:
        dims = dims or self.dims
        buckets: SparseVec = {}
        for i, ch in enumerate(text.lower()):
            if not ch.strip():
                continue
            key = hashlib.md5(f"{i}-{ch}".encode()).hexdigest()
            idx = int(key, 16) % dims
            buckets[idx] = buckets.get(idx, 0.0) + self._char_value(ch)

        if not buckets:
            return {}
        mx = max(buckets.values()) or 1.0
        for k in list(buckets.keys()):
            buckets[k] = buckets[k] / mx
        return buckets

    # ---------- Helpers ----------
    def _normalize_stored_vec(self, vec: dict) -> SparseVec:
        out: SparseVec = {}
        for k, v in vec.items():
            try:
                out[int(k)] = float(v)
            except (ValueError, TypeError):
                continue
        return out

    def _l2norm(self, vec: SparseVec) -> SparseVec:
        s = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {k: v / s for k, v in vec.items()}

    # ---------- Math ----------
    def sparse_distance(self, a: SparseVec, b: SparseVec) -> float:
        keys = set(a.keys()) | set(b.keys())
        return math.sqrt(sum((a.get(k, 0.0) - b.get(k, 0.0)) ** 2 for k in keys))

    # ---------- Weights (DB) ----------
    def _get_weight(self, idx: int) -> float:
        _, _, Weight, _, _ = _load_models()
        w = Weight.objects.filter(memory=self.memory, index=idx).only("value").first()
        return w.value if w else 0.0

    def _set_weight(self, idx: int, value: float):
        _, _, Weight, _, _ = _load_models()
        Weight.objects.update_or_create(
            memory=self.memory,
            index=idx,
            defaults={"value": value},
        )

    def log_activity(self, role: str, text: str):
        _, _, _, _, ActivityLog = _load_models()
        step = ActivityLog.objects.filter(memory=self.memory).count() + 1
        ActivityLog.objects.create(memory=self.memory, step=step, role=role, text=text)

    # ---------- Learning ----------
    @transaction.atomic
    def learn(self, question: str, answer: str) -> float:
        Memory, MemoryItem, Weight, MemoryLink, ActivityLog = _load_models()

        q_vec = self._l2norm(self.text_to_sparseN(question))
        a_vec = self._l2norm(self.text_to_sparseN(answer))
        self.log_activity("user", f"Learned Q: {question}")
        self.log_activity("ai", f"Learned A: {answer}")

        keys = set(q_vec.keys()) | set(a_vec.keys())
        avg_err = sum(abs(a_vec.get(k, 0.0) - q_vec.get(k, 0.0)) for k in keys) / max(len(keys), 1)

        # Update weights
        for k, v in q_vec.items():
            w = self._get_weight(k)
            if w == 0.0:
                w = random.uniform(-1, 1)
            w += self.lr * avg_err * v
            self._set_weight(k, w)

        # Avoid duplicates
        if MemoryItem.objects.filter(memory=self.memory, input_text=question, answer_text=answer).exists():
            return 0.0

        # 🧠 Compute sentence embedding (semantic vector)
        text_for_embed = f"{question} {answer}"
        if _embedder is None:
            print("⚠️ Embedding model not available, skipping semantic link creation.")
            return avg_err
        embedding = _embedder.encode(text_for_embed, normalize_embeddings=True)
        # ensure plain python list
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()

        new_item = MemoryItem.objects.create(
            memory=self.memory,
            input_text=question,
            answer_text=answer,
            input_vec={str(k): v for k, v in q_vec.items()},
            target_vec={str(k): v for k, v in a_vec.items()},
            avg_error=avg_err,
            embedding=embedding,
        )

        # 🔗 Find semantically related memories
        related_items = MemoryItem.objects.filter(memory=self.memory).exclude(id=new_item.id)[:100]
        if not related_items.exists():
            return avg_err

        new_vec = np.array(embedding, dtype=float)

        for related_item in related_items:
            if not related_item.embedding:
                continue
            other_vec = np.array(related_item.embedding, dtype=float)

            # Cosine similarity
            denom = (np.linalg.norm(new_vec) * np.linalg.norm(other_vec) + 1e-9)
            similarity = float(np.dot(new_vec, other_vec) / denom)
            if similarity < 0.6:  # threshold can be tuned
                continue

            # Auto-select relation
            q_text = (question + " " + answer).lower()
            r_text = (related_item.input_text + " " + related_item.answer_text).lower()

            if "subset" in r_text or "type" in r_text:
                relation = "is a type of"
            elif "use" in r_text or "applied" in r_text:
                relation = "uses"
            elif "part" in r_text:
                relation = "is part of"
            else:
                relation = "is semantically related to"

            MemoryLink.objects.create(
                source=new_item,
                target=related_item,
                relation=relation,
                confidence=round(similarity, 3),
            )

        # 🔄 Self-reflection scheduler
        self.learn_count += 1
        if self.learn_count >= self.reflect_every:
            try:
                improvements = self.reflect()
                print(f"🧠 Reflection triggered automatically: {improvements} items improved.")
            except Exception as e:
                print(f"⚠️ Reflection error: {e}")
            self.learn_count = 0

        return avg_err

    def answer(self, question: str) -> tuple[str, float]:
        _, MemoryItem, _, _, _ = _load_models()

        qs = MemoryItem.objects.filter(memory=self.memory).only(
            "input_text", "answer_text", "input_vec", "embedding"
        )
        if not qs.exists():
            return ("I don't know this yet.", float("-inf"))

        q_vec = self.text_to_sparseN(question)

        # --- Compute semantic embedding of the question ---
        q_emb = None
        if _embedder:
            try:
                q_emb = _embedder.encode(question, normalize_embeddings=True)
                if hasattr(q_emb, "astype"):
                    q_emb = q_emb.astype(float)
            except Exception as e:
                print("⚠️ Embedding failed:", e)
                q_emb = None

        # --- Find the most similar stored memory ---
        closest = None
        best = -float("inf")  # maximize similarity

        for item in qs.iterator():
            # --- Symbolic (sparse) similarity ---
            t_vec = self._normalize_stored_vec(item.input_vec)
            sparse_dist = self.sparse_distance(q_vec, t_vec)
            sparse_sim = max(0.0, 1 - min(sparse_dist / 3, 1))  # normalize to 0–1

            # --- Semantic (embedding) similarity ---
            semantic_sim = 0.0
            if q_emb is not None and getattr(item, "embedding", None):
                item_emb = np.array(item.embedding, dtype=float)
                denom = (np.linalg.norm(q_emb) * np.linalg.norm(item_emb) + 1e-9)
                semantic_sim = float(np.dot(q_emb, item_emb) / denom)

            # --- Combine both similarities (semantic weighted higher) ---
            combined_score = 0.3 * sparse_sim + 0.7 * semantic_sim

            if closest is None or combined_score > best:
                best = combined_score
                closest = item

        if closest is None or best < 0.2:  # adjustable threshold
            return ("I don't know this yet. Can you teach me?", best)

        return (f"🧩 Similarity: {best:.3f}\n💬 '{closest.input_text}' → '{closest.answer_text}'", best)

    def answer_with_attention(self, question: str, top_k: int = 5) -> str:
        _, MemoryItem, _, _, _ = _load_models()

        qs = list(
            MemoryItem.objects.filter(memory=self.memory).only("answer_text", "target_vec", "embedding")
        )
        if not qs:
            return "I don't know yet."

        # Sparse vector for the question
        q_vec = self.text_to_sparseN(question)

        # Semantic embedding for the question
        q_emb = None
        if _embedder:
            try:
                q_emb = _embedder.encode(question, normalize_embeddings=True)
            except Exception as e:
                print("⚠️ Embedding failed in attention:", e)
                q_emb = None

        scored = []
        for item in qs:
            # --- sparse similarity (question vs. item's target_vec) ---
            t_vec = self._normalize_stored_vec(item.target_vec or {})
            d = self.sparse_distance(q_vec, t_vec)
            sparse_sim = max(0.0, 1 - min(d / 3, 1))  # normalize 0–1

            # --- semantic similarity (question embedding vs. item embedding) ---
            semantic_sim = 0.0
            if q_emb is not None and getattr(item, "embedding", None):
                item_emb = np.array(item.embedding, dtype=float)
                denom = (np.linalg.norm(q_emb) * np.linalg.norm(item_emb) + 1e-9)
                semantic_sim = float(np.dot(q_emb, item_emb) / denom)

            # --- combined score (semantic is usually more reliable for intent) ---
            combined = 0.7 * semantic_sim + 0.3 * sparse_sim
            scored.append((combined, item))

        # Sort by combined score (desc)
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:max(1, top_k)]

        # Convert to weights
        scores = [max(0.0, s) for s, _ in top]
        total = sum(scores) or 1.0
        weights = [s / total for s in scores]

        # Filter out weak hits
        MIN_CONFIDENCE = 0.08
        filtered = [(w, it) for w, (_, it) in zip(weights, top) if w >= MIN_CONFIDENCE]
        if not filtered and top:
            filtered = [(weights[0], top[0][1])]

        lines = [f"({w:.2f}) {it.answer_text.strip()}" for w, it in filtered]
        return "🧠 Attention Mode:\n" + "\n".join(lines)

    # ---------- Multi-hop Reasoning ----------
    def chain_reasoning(self, question: str, depth: int = 3):
        """
        Tries to reason step-by-step across multiple related questions.
        FIX: answer_with_attention returns a string, not a tuple.
        """
        first = self.answer_with_attention(question)
        chain = [first]
        for _ in range(max(0, depth - 1)):
            # naive follow-up generation
            next_q = chain[-1].split("→")[-1].strip().split("?")[0] + "?"
            next_a = self.answer_with_attention(next_q)
            chain.append(next_a)
        return " → ".join(chain)

    def compose_message(self, question: str, top_k: int = 5) -> str:
        """Merge top attention answers into a single coherent message."""
        raw = self.answer_with_attention(question, top_k=top_k)
        lines = [l.split(") ", 1)[1] for l in raw.split("\n") if ") " in l]
        if not lines:
            return raw
        # Join politely with transitions
        merged = " ".join(lines[:3])
        merged = merged.replace("..", ".").strip()
        if not merged.endswith("."):
            merged += "."
        return merged

    
    # ---------- Autonomous Cognitive Core (No LLM) ----------

    def _parse_attention(self, attention_text: str) -> list[tuple[float, str]]:
        """
        Parse answer_with_attention() into [(weight, text), ...].
        Expected lines like: '(0.28) some text...'
        """
        lines = []
        for line in attention_text.splitlines():
            line = line.strip()
            if not line or line.startswith("🧠"):
                continue
            m = re.match(r"^\(([\d\.]+)\)\s+(.*)$", line)
            if m:
                try:
                    w = float(m.group(1))
                except ValueError:
                    w = 0.0
                text = m.group(2).strip()
                if text:
                    lines.append((w, text))
        return lines

    def extract_pattern(self, text_block: str) -> str | None:
        """
        Abstraction step: find recurring tokens and form a proto-rule or theme.
        Very lightweight, but gives the system 'concept noticing'.
        """
        words = re.findall(r"\b[a-z]{3,}\b", text_block.lower())
        if not words:
            return None

        # remove very common stop-ish words without importing a list
        ignore = {"the","and","for","with","that","from","this","have","has","into","about","your","you","are","was","were","will","can","not"}
        freq = {}
        for w in words:
            if w in ignore:
                continue
            freq[w] = freq.get(w, 0) + 1

        if not freq:
            return None

        # top 3 recurring tokens as a theme
        top = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:3]
        keys = [k for k,_ in top]
        return f"Pattern: core concepts → {', '.join(keys)}"

    def reason(self, statement: str) -> str | None:
        """
        Deterministic symbolic reasoning.
        Captures common human-form rules: implication, causality, definitional linking.
        """
        s = (statement or "").strip()
        if not s:
            return None

        low = s.lower()

        # Implication / modus ponens style
        if "if" in low and "then" in low:
            # naive split; robust enough for short spans
            parts = re.split(r"\bthen\b", low, maxsplit=1)
            premise = parts[0].split("if", 1)[-1].strip()
            conclusion = parts[1].strip() if len(parts) > 1 else ""
            if premise and conclusion:
                # If the premise itself mentions 'true/holds', lean affirmative
                if any(k in premise for k in [" true", " holds", " given", " assume"]):
                    return f"Therefore, {conclusion}."
                else:
                    return f"The truth of '{conclusion}' depends on whether '{premise}' holds."
        
        # Causality
        if " because " in low:
            cause, effect = low.split(" because ", 1)
            cause = cause.strip(". ,;:")
            effect = effect.strip(". ,;:")
            if cause and effect:
                return f"It follows that {effect} results from {cause}."

        # Definition synthesis (X is Y → treat as categorization)
        m = re.match(r"^(.+?)\s+is\s+(.+)$", s, flags=re.IGNORECASE)
        if m:
            subj = m.group(1).strip(" .,:;")
            pred = m.group(2).strip(" .,:;")
            if subj and pred:
                return f"So, '{subj}' can be considered '{pred}'."

        return None

    def evaluate_emotion(self, text: str) -> float:
        """
        Crude affective valence for salience ([-1, 1]).
        Used to slightly favor or decay certain memories during reflection.
        """
        low = (text or "").lower()
        pos = len(re.findall(r"\b(good|love|joy|happy|clear|success|benefit|win|improve|helpful)\b", low))
        neg = len(re.findall(r"\b(bad|hate|fear|sad|fail|risk|harm|unclear|error|problem)\b", low))
        total = max(1, pos + neg)
        return (pos - neg) / total

    def conclude(self, thoughts: list[str], question: str) -> str:
        """
        Compose a human-readable answer from thought chain without any LLM.
        It extracts key steps and writes a readable mini-explanation.
        """
        # Collect key sentences
        steps = []
        for t in thoughts:
            frag = t.split("→", 1)[-1].strip()
            frag = frag[0:1].upper() + frag[1:] if frag else frag
            if frag and not frag.endswith("."):
                frag += "."
            if frag:
                steps.append(frag)

        # Minimal discourse shaping
        if not steps:
            return "I considered your question, but I need more detail."

        head = steps[0]
        middle = " ".join(steps[1:-1]) if len(steps) > 2 else ""
        tail = steps[-1] if len(steps) > 1 else ""
        answer = head
        if middle:
            answer += " " + middle
        if tail and tail != head:
            answer += " " + tail

        # Store as learned conclusion for future retrieval
        try:
            self.learn(question, answer)
        except Exception:
            pass

        return answer

    def think(self, question: str, depth: int = 3, breadth: int = 5) -> str:
        """
        Autonomous multi-step reasoning loop:
        Perceive → Recall → Abstract → Infer → Evaluate → Conclude.
        No LLM, purely algorithmic + semantic memory.
        """
        q = question.strip()
        thoughts = [f"Perceive → {q}"]

        for step in range(max(1, depth)):
            # 1) Recall
            attn = self.answer_with_attention(q, top_k=breadth)
            pairs = self._parse_attention(attn)
            if not pairs:
                thoughts.append("Recall → nothing strongly relevant found")
                break

            # preference by weight
            context = " ".join([txt for _, txt in pairs])
            thoughts.append(f"Recall → {', '.join([txt[:60].rstrip()+'…' if len(txt)>60 else txt for _, txt in pairs[:3]])}")

            # 2) Abstract (pattern)
            pattern = self.extract_pattern(context)
            if pattern:
                thoughts.append(f"Abstract → {pattern}")
            else:
                thoughts.append("Abstract → no clear pattern")
                pattern = q  # fallback

            # 3) Infer (symbolic)
            inference = self.reason(f"{q}. {pattern}")
            if inference:
                thoughts.append(f"Infer → {inference}")
                q = inference  # iterate over refined statement
            else:
                thoughts.append("Infer → no new inference")
                # stop early if we can't push the thought forward
                break

            # 4) Evaluate (affective salience; tiny nudge to future learning)
            val = self.evaluate_emotion(context + " " + (inference or ""))
            thoughts.append(f"Evaluate → valence={val:+.2f}")

        # 5) Conclude
        answer = self.conclude(thoughts, question)
        # Log a compact trail
        try:
            self.log_activity("ai", " | ".join(thoughts))
        except Exception:
            pass
        return answer

    # ---------- Replace your smart_answer with this NO-LLM version ----------
    def smart_answer(self, question: str) -> str:
        """
        Hybrid: exact math/symbolic first; otherwise run autonomous 'think' loop.
        No language model is used anywhere.
        """
        q = question.strip()

        # 1) Try explicit math safely with sympy
        if re.search(r"\d", q) or any(op in q for op in ["+", "-", "*", "/", "^", "(", ")"]):
            expr = re.sub(r"[^\d\+\-\*/\.\(\)\s\^]", "", q)
            try:
                if re.fullmatch(r"[0-9\+\-\*/\.\(\)\s\^]+", expr):
                    val = float(sympify(expr).evalf())
                    simplified = simplify(expr)
                    # Compose a natural sentence (no template fluff)
                    msg = f"{q.strip().rstrip('?')}: {simplified} = {val}."
                    try:
                        self.learn(q, msg)
                    except Exception:
                        pass
                    return msg
            except Exception:
                # fall through to autonomous thinking
                pass

        # 2) Try direct memory if very confident
        text, score = self.answer(q)
        if score >= 0.65:  # higher bar than default to avoid irrelevant blurbs
            try:
                self.learn(q, text)
            except Exception:
                pass
            # Strip the technical prefix to sound natural
            if "→" in text:
                return text.split("→", 1)[-1].strip().strip("'").strip()
            return text

        # 3) Autonomous cognitive loop
        return self.think(q, depth=3, breadth=5)

    
    @transaction.atomic
    def reflect(self) -> int:
        """
        Cross-check memories for contradictions and forget noisy ones.
        Hardened against KeyError: None.
        """
        _, MemoryItem, _, _, _ = _load_models()
        qs = list(MemoryItem.objects.filter(memory=self.memory))
        improvements = 0
        if not qs:
            return 0

        cache = {}
        for q in qs:
            if q.id and q.embedding:
                cache[q.id] = np.array(q.embedding, dtype=float)

        for i, item in enumerate(qs):
            if not getattr(item, "embedding", None) or not getattr(item, "id", None):
                continue
            vec_i = cache.get(item.id)
            if vec_i is None:
                continue

            for j in range(i + 1, len(qs)):
                other = qs[j]
                if not getattr(other, "embedding", None) or not getattr(other, "id", None):
                    continue
                vec_j = cache.get(other.id)
                if vec_j is None:
                    continue

                if item.input_text.lower().strip() == other.input_text.lower().strip():
                    denom = (np.linalg.norm(vec_i) * np.linalg.norm(vec_j) + 1e-9)
                    sim = float(np.dot(vec_i, vec_j) / denom)
                    if sim < 0.45:
                        bad = item if item.avg_error > other.avg_error else other
                        print(f"🧹 Deleted contradictory memory: {bad.input_text} → {bad.answer_text[:80]}")
                        bad.delete()
                        improvements += 1

        deleted, _ = MemoryItem.objects.filter(memory=self.memory, avg_error__gt=0.8).delete()
        improvements += deleted
        return improvements


