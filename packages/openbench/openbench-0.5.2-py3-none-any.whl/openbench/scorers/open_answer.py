"""Open-answer scorer for text-based questions that require parsing and normalization.

This scorer handles open-ended questions by:
1. Parsing the response to extract key information
2. Normalizing both predicted and gold answers
3. Checking for matches across different representations (string and numeric)

Originally extracted from MMMU scorer for reusability across benchmarks.
"""

from typing import Callable, Optional, Sequence, Union, List, Any
import re

from inspect_ai.scorer import scorer, accuracy, stderr, std, Score, Target
from inspect_ai.solver import TaskState

from openbench.metrics.grouped import grouped


def _build_metrics(group_keys: Optional[List[str]] = None) -> List[Any]:
    """Build metrics list with optional grouping."""
    metrics: List[Any] = [accuracy(), stderr(), std()]
    if group_keys:
        for key in group_keys:
            metrics.append(grouped(group_key=key, metric=[accuracy(), stderr(), std()]))
    return metrics


def create_open_answer_scorer(
    group_keys: Optional[List[str]] = None,
    answer_key: str = "answer",
) -> Callable:
    """Create a scorer for open-answer questions with text parsing and normalization.

    This scorer is designed for questions where the model needs to provide a free-form
    answer that should be compared against a gold standard answer. It handles:
    - Extracting key information from model responses
    - Normalizing answers for comparison (both string and numeric)
    - Flexible matching across different representations

    Args:
        group_keys: Optional metadata keys to group metrics by.
        answer_key: Metadata key where the gold answer is stored (default: "answer").

    Returns:
        A scorer function that can be used with Inspect AI tasks.
    """

    @scorer(metrics=_build_metrics(group_keys))
    def open_answer_scorer() -> Callable:
        async def score(state: TaskState, target: Target) -> Score:
            # Parse model response to extract predictions
            parsed_predictions = _parse_open_response(state.output.completion or "")

            # Get gold answer from metadata or target text
            answer = state.metadata.get(answer_key, target.text)

            # Evaluate if the response is correct
            is_correct = _eval_open(answer, parsed_predictions)

            return Score(
                value=1.0 if is_correct else 0.0,
                answer=state.output.completion,
                metadata={"open_eval": True, "pred_list": parsed_predictions},
            )

        return score

    return open_answer_scorer


# ------------------------
# Open-answer parsing logic
# ------------------------


def _extract_numbers(text: str) -> list[Union[float, str]]:
    """Extract numerical values from text."""
    numbers: list[Union[float, str]] = []
    for match in re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", "")):
        try:
            num = float(match)
            numbers.append(num)
        except ValueError:
            continue
    return numbers


def _normalize_str(value: Union[str, float, int]) -> list[Union[str, float]]:
    """Normalize a value into comparable string and numeric forms."""
    if isinstance(value, (float, int)):
        return [float(value)]

    s = str(value).strip().strip(".").strip().lower()
    # Remove extra punctuation/spaces
    s = re.sub(r"\s+", " ", s)

    # Try to add a numeric interpretation if it parses
    out: list[Union[str, float]] = []
    try:
        num = float(s.replace(",", ""))
        out.append(float(num))
    except ValueError:
        pass

    if s:
        out.append(s)
    return out


def _parse_open_response(response: str) -> list[Union[str, float]]:
    """Parse an open response to extract key predictions."""

    def get_key_subresponses(resp: str) -> list[str]:
        """Extract key sub-responses that likely contain the answer."""
        key_responses: list[str] = []
        resp = resp.strip().strip(".").lower()
        sub_responses = re.split(r"\.\s(?=[A-Z])|\n", resp)

        indicators_of_keys = [
            "could be ",
            "so ",
            "is ",
            "thus ",
            "therefore ",
            "final ",
            "answer ",
            "result ",
        ]

        for index, sub in enumerate(sub_responses):
            local_indicators = list(indicators_of_keys)
            if index == len(sub_responses) - 1:
                local_indicators.extend(["="])

            shortest: Optional[str] = None
            for indicator in local_indicators:
                if indicator in sub:
                    candidate = sub.split(indicator)[-1].strip()
                    if not shortest or len(candidate) < len(shortest):
                        shortest = candidate

            if shortest and shortest not in [":", ",", ".", "!", "?", ";", ":", "'"]:
                key_responses.append(shortest)

        if not key_responses:
            return [resp]
        return key_responses

    key_responses = get_key_subresponses(response or "")
    pred_list: list[Union[str, float]] = list(key_responses)

    # Extract numbers from each response
    for resp in key_responses:
        pred_list.extend(_extract_numbers(resp))

    # Normalize all predictions
    tmp: list[Union[str, float]] = []
    for item in pred_list:
        tmp.extend(_normalize_str(item))

    # Remove duplicates while preserving order
    pred_list = list(dict.fromkeys(tmp))
    return pred_list


def _eval_open(
    gold: Union[str, Sequence[Any]], pred_list: list[Union[str, float]]
) -> bool:
    """Evaluate if any prediction matches the gold answer(s)."""

    # Normalize gold answers into comparable forms (strings and floats)
    norm_answers: list[Union[str, float]] = []
    if isinstance(gold, (str, float, int)):
        norm_answers = _normalize_str(gold)
    elif isinstance(gold, Sequence):
        for ans in gold:
            value: Union[str, float, int]
            if isinstance(ans, (str, float, int)):
                value = ans
            else:
                value = str(ans)
            norm_answers.extend(_normalize_str(value))
    else:
        norm_answers = _normalize_str(str(gold))

    # Check if any prediction matches any normalized answer
    correct = False
    for pred in pred_list:
        if isinstance(pred, str):
            for norm_ans in norm_answers:
                if isinstance(norm_ans, str) and norm_ans in pred:
                    correct = True
                    break
        else:
            if pred in norm_answers:
                correct = True
        if correct:
            break

    return correct


# Pre-configured scorer for common use cases
def simple_open_answer_scorer() -> Callable:
    """Simple open-answer scorer with just accuracy, stderr, and std metrics."""
    return create_open_answer_scorer()()


def grouped_open_answer_scorer(group_key: str) -> Callable:
    """Open-answer scorer with grouping by a single metadata key."""
    return create_open_answer_scorer(group_keys=[group_key])()
