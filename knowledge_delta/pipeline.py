"""One question against one snapshot; traces remain distinct from correctness judgments."""
from dataclasses import asdict, dataclass
import time

from .prompts import PROMPT_VERSION, SYSTEM, build_prompt
from .retrieval import INDEX_VERSION
from .responses import Answer, citation_compatibility
from .validation import ValidationError, digest

PIPELINE_VERSION = "snapshot-answering-v1"


@dataclass(frozen=True)
class RunConfiguration:
    version_filter: bool = False
    top_k: int = 2
    context_window: int = 4096
    max_output_tokens: int = 128
    max_attempts: int = 2

    def __post_init__(self):
        if type(self.version_filter) is not bool:
            raise ValidationError("version_filter must be a boolean")
        if type(self.top_k) is not int or not 1 <= self.top_k <= 20:
            raise ValidationError("top_k must be an integer in 1..20")
        if (type(self.context_window) is not int or type(self.max_output_tokens) is not int
                or self.max_output_tokens < 1 or self.context_window <= self.max_output_tokens + 256):
            raise ValidationError("invalid context/output token budgets")
        if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 2:
            raise ValidationError("max_attempts must be 1 or 2")


def run_question(question, snapshot, index, embedder, client, configuration=None):
    config = configuration if configuration is not None else RunConfiguration()
    started = time.perf_counter()
    origin = "live" if (embedder.mode == "local" and index.embedder_mode == "local"
                         and client.transport.mode == "local_http"
                         and all(chunk.tokenizer_mode == "local" for chunk in index.chunks)) else "test_double"
    result = {"schema_version": 1, "pipeline_version": PIPELINE_VERSION, "origin": origin,
              "snapshot_id": snapshot.snapshot_id, "case_id": question.case_id,
              "question": asdict(question), "configuration": asdict(config),
              "index_id": index.index_id, "embedder_id": embedder.identity,
              "requested_version": question.requested_version, "effective_version": None,
              "configuration_id": None,
              "pipeline_configuration_id": digest({"pipeline": PIPELINE_VERSION, "prompt": PROMPT_VERSION,
                  "system_prompt": SYSTEM, "index_version": INDEX_VERSION,
                  "chunker_configurations": index.chunker_configurations,
                  "settings": asdict(config), "embedder": embedder.identity,
                  "model": client.model}),
              "status": "run_error", "judgment": "needs_human_review", "answer": None,
              "retrieved_passages": [], "retrieval_exclusions": [], "generation": None,
              "generation_performed": False, "answer_cache_used": False,
              "error": None, "error_phase": None}
    phase = "retrieval"
    try:
        retrieval = index.search(question, snapshot, embedder, top_k=config.top_k,
                                 version_filter=config.version_filter)
        result["effective_version"] = retrieval.effective_version
        result["retrieved_passages"] = [dict(asdict(chunk), similarity=score)
                                        for chunk, score in zip(retrieval.chunks, retrieval.scores)]
        result["retrieval_exclusions"] = list(retrieval.excluded)
        if not retrieval.chunks:
            result.update(status="answered_pending_review", answer={"answer": "Insufficient applicable documentation evidence.",
                          "citations": [], "abstained": True}, answer_origin="policy_abstention")
        else:
            phase = "prompt"
            prompt = build_prompt(question, snapshot, retrieval.chunks,
                                  config.context_window, config.max_output_tokens)
            result["prompt"] = prompt  # Exact supplied context, not a claim about internal server truncation.
            phase = "generation"
            generation = client.answer(prompt, retrieval.chunks, max_attempts=config.max_attempts)
            result["generation"] = generation
            if generation.get("model_digest") is not None:
                result["configuration_id"] = digest({"pipeline_configuration_id": result["pipeline_configuration_id"],
                    "model_digest": generation["model_digest"],
                    "generation_configuration_id": generation.get("configuration_id")})
            result["generation_performed"] = generation["generation_performed"]
            result["status"] = generation["status"]
            result["answer"] = generation["answer"]
            result["answer_origin"] = generation["origin"]
            if generation["origin"] == "test_double":
                result["origin"] = "test_double"
            if generation["error"]:
                result["error"] = generation["error"]
                result["error_phase"] = phase
        if result["answer"] is not None:
            value = result["answer"]
            answer = Answer(value["answer"], tuple(value["citations"]), value["abstained"])
            result["citation_checks"] = list(citation_compatibility(answer, retrieval.chunks, retrieval.effective_version))
    except (ValidationError, RuntimeError, OSError) as exc:
        result.update(status="run_error", answer=None, error=str(exc), error_phase=phase)
    result["elapsed_seconds"] = time.perf_counter() - started
    return result
