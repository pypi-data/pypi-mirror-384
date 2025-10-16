"""
Registry for inspect_ai extensions (model providers and tasks).
This module is the entry point for inspect_ai to discover our extensions.
"""

from typing import Type
from inspect_ai.model import ModelAPI
from inspect_ai.model._registry import modelapi


# Model Provider Registration


@modelapi(name="huggingface")
def huggingface() -> Type[ModelAPI]:
    """Register Hugging Face Inference Providers router provider."""
    from .model._providers.huggingface import HFInferenceProvidersAPI

    return HFInferenceProvidersAPI


@modelapi(name="cerebras")
def cerebras() -> Type[ModelAPI]:
    """Register Cerebras provider."""
    from .model._providers.cerebras import CerebrasAPI

    return CerebrasAPI


@modelapi(name="sambanova")
def sambanova() -> Type[ModelAPI]:
    """Register SambaNova provider."""
    from .model._providers.sambanova import SambaNovaAPI

    return SambaNovaAPI


@modelapi(name="nebius")
def nebius() -> Type[ModelAPI]:
    """Register Nebius provider."""
    from .model._providers.nebius import NebiusAPI

    return NebiusAPI


@modelapi(name="nous")
def nous() -> Type[ModelAPI]:
    """Register Nous Research provider."""
    from .model._providers.nous import NousAPI

    return NousAPI


@modelapi(name="lambda")
def lambda_provider() -> Type[ModelAPI]:
    """Register Lambda provider."""
    from .model._providers.lambda_ai import LambdaAPI

    return LambdaAPI


@modelapi(name="baseten")
def baseten() -> Type[ModelAPI]:
    """Register Baseten provider."""
    from .model._providers.baseten import BasetenAPI

    return BasetenAPI


@modelapi(name="hyperbolic")
def hyperbolic() -> Type[ModelAPI]:
    """Register Hyperbolic provider."""
    from .model._providers.hyperbolic import HyperbolicAPI

    return HyperbolicAPI


@modelapi(name="novita")
def novita() -> Type[ModelAPI]:
    """Register Novita provider."""
    from .model._providers.novita import NovitaAPI

    return NovitaAPI


@modelapi(name="parasail")
def parasail() -> Type[ModelAPI]:
    """Register Parasail provider."""
    from .model._providers.parasail import ParasailAPI

    return ParasailAPI


@modelapi(name="crusoe")
def crusoe() -> Type[ModelAPI]:
    """Register Crusoe provider."""
    from .model._providers.crusoe import CrusoeAPI

    return CrusoeAPI


@modelapi(name="deepinfra")
def deepinfra() -> Type[ModelAPI]:
    """Register DeepInfra provider."""
    from .model._providers.deepinfra import DeepInfraAPI

    return DeepInfraAPI


@modelapi(name="ai21")
def ai21() -> Type[ModelAPI]:
    """Register AI21 Labs provider."""
    from .model._providers.ai21 import AI21API

    return AI21API


@modelapi(name="minimax")
def minimax() -> Type[ModelAPI]:
    """Register MiniMax provider."""
    from .model._providers.minimax import MiniMaxAPI

    return MiniMaxAPI


@modelapi(name="friendli")
def friendli() -> Type[ModelAPI]:
    """Register Friendli provider."""
    from .model._providers.friendli import FriendliAPI

    return FriendliAPI


@modelapi(name="reka")
def reka() -> Type[ModelAPI]:
    """Register Reka provider."""
    from .model._providers.reka import RekaAPI

    return RekaAPI


@modelapi(name="cohere")
def cohere() -> Type[ModelAPI]:
    """Register Cohere provider."""
    from .model._providers.cohere import CohereAPI

    return CohereAPI


@modelapi(name="moonshot")
def moonshot() -> Type[ModelAPI]:
    """Register Moonshot provider."""
    from .model._providers.moonshot import MoonshotAPI

    return MoonshotAPI


@modelapi(name="vercel")
def vercel() -> Type[ModelAPI]:
    """Register Vercel AI Gateway provider."""
    from .model._providers.vercel import VercelAPI

    return VercelAPI


@modelapi(name="openrouter")
def openrouter() -> Type[ModelAPI]:
    """Register OpenRouter provider."""
    from .model._providers.openrouter import OpenRouterAPI

    return OpenRouterAPI


def _override_builtin_groq_provider():
    """Replace Inspect AI's built-in groq provider with enhanced openbench version."""
    from inspect_ai._util.registry import _registry
    from .model._providers.groq import GroqAPI
    from inspect_ai.model._registry import modelapi

    @modelapi(name="groq")
    def openbench_groq_override():
        return GroqAPI

    # Force override the inspect_ai/groq entry with openbench implementation
    _registry["modelapi:inspect_ai/groq"] = openbench_groq_override

    return openbench_groq_override


def _override_builtin_openrouter_provider():
    """Replace Inspect AI's built-in openrouter provider with enhanced openbench version."""
    from inspect_ai._util.registry import _registry
    from .model._providers.openrouter import OpenRouterAPI
    from inspect_ai.model._registry import modelapi

    @modelapi(name="openrouter")
    def openbench_openrouter_override():
        return OpenRouterAPI

    # Force override the inspect_ai/openrouter entry with openbench implementation
    _registry["modelapi:inspect_ai/openrouter"] = openbench_openrouter_override

    return openbench_openrouter_override


# Execute the overrides
_override_builtin_groq_provider()
_override_builtin_openrouter_provider()


# Task Registration

# Core benchmarks
from .evals.arc import arc_easy, arc_challenge  # noqa: F401, E402
from .evals import bigbench, bigbench_hard, global_mmlu  # noqa: F401, E402
from .evals.clockbench import clockbench  # noqa: F401, E402
from .evals.drop import drop  # noqa: F401, E402
from .evals.gpqa_diamond import gpqa_diamond  # noqa: F401, E402
from .evals.gpqa import gpqa  # noqa: F401, E402
from .evals.graphwalks import graphwalks  # noqa: F401, E402
from .evals.headqa import headqa, headqa_en, headqa_es  # noqa: F401, E402
from .evals.healthbench import healthbench, healthbench_hard, healthbench_consensus  # noqa: F401, E402
from .evals.hellaswag import hellaswag  # noqa: F401, E402
from .evals.hle import hle, hle_text  # noqa: F401, E402
from .evals.humaneval import humaneval  # noqa: F401, E402
from .evals.exercism.exercism import (  # noqa: F401, E402
    exercism,
    exercism_python,
    exercism_javascript,
    exercism_go,
    exercism_java,
    exercism_rust,
)
from .evals.livemcpbench import livemcpbench  # noqa: F401, E402
from .evals.math import math, math_500  # noqa: F401, E402
from .evals.mbpp import mbpp  # noqa: F401, E402
from .evals.medmcqa import medmcqa  # noqa: F401, E402
from .evals.medqa import medqa  # noqa: F401, E402
from .evals.mgsm import mgsm, mgsm_en, mgsm_latin, mgsm_non_latin  # noqa: F401, E402
from .evals.mmlu import mmlu  # noqa: F401, E402
from .evals.mmlu_pro import mmlu_pro  # noqa: F401, E402
from .evals.multichallenge import multichallenge  # noqa: F401, E402
from .evals.mrcr import openai_mrcr, openai_mrcr_2n, openai_mrcr_4n, openai_mrcr_8n  # noqa: F401, E402
from .evals.mmstar import mmstar  # noqa: F401, E402
from .evals.musr import musr  # noqa: F401, E402
from .evals.openbookqa import openbookqa  # noqa: F401, E402
from .evals.pubmedqa import pubmedqa  # noqa: F401, E402
from .evals.piqa import piqa  # noqa: F401, E402
from .evals.prost import prost  # noqa: F401, E402
from .evals.scicode import scicode  # noqa: F401, E402
from .evals.swag import swag  # noqa: F401, E402
from .evals.simpleqa import simpleqa  # noqa: F401, E402
from .evals.tumlu import tumlu  # noqa: F401, E402
from .evals.winogrande import winogrande  # noqa: F401, E402
from .evals.wsc273 import wsc273  # noqa: F401, E402
from .evals.detailbench import detailbench  # noqa: F401, E402
from .evals.supergpqa import supergpqa  # noqa: F401, E402
from .evals.mmmlu import mmmlu  # noqa: F401, E402
from .evals.mmmu import (  # noqa: F401, E402
    mmmu,
    mmmu_mcq,
    mmmu_open,
    mmmu_accounting,
    mmmu_agriculture,
    mmmu_architecture_and_engineering,
    mmmu_art,
    mmmu_art_theory,
    mmmu_basic_medical_science,
    mmmu_biology,
    mmmu_chemistry,
    mmmu_clinical_medicine,
    mmmu_computer_science,
    mmmu_design,
    mmmu_diagnostics_and_laboratory_medicine,
    mmmu_economics,
    mmmu_electronics,
    mmmu_energy_and_power,
    mmmu_finance,
    mmmu_geography,
    mmmu_history,
    mmmu_literature,
    mmmu_manage,
    mmmu_marketing,
    mmmu_materials,
    mmmu_math,
    mmmu_mechanical_engineering,
    mmmu_music,
    mmmu_pharmacy,
    mmmu_physics,
    mmmu_psychology,
    mmmu_public_health,
    mmmu_sociology,
)
from .evals.mmmu_pro import mmmu_pro, mmmu_pro_vision  # noqa: F401, E402
from .evals.arc_agi import arc_agi, arc_agi_1, arc_agi_2  # noqa: F401, E402
from .evals.mockaime import otis_mock_aime, otis_mock_aime_2024, otis_mock_aime_2025  # noqa: F401, E402

# GLUE/SuperGLUE benchmarks
from .evals import anli  # noqa: F401, E402
from .evals import glue  # noqa: F401, E402
from .evals import glue_standard  # noqa: F401, E402

# Cross-lingual benchmarks
from .evals import xcopa  # noqa: F401, E402
from .evals import xstorycloze  # noqa: F401, E402
from .evals import xwinograd  # noqa: F401, E402

# AGIEval benchmarks
from .evals import agieval  # noqa: F401, E402

# Ethics & Social Understanding benchmarks
from .evals import ethics  # noqa: F401, E402
from .evals import social_iqa  # noqa: F401, E402
from .evals import toxigen  # noqa: F401, E402

# Reading Comprehension benchmarks
from .evals import race  # noqa: F401, E402
from .evals import qa4mre  # noqa: F401, E402
from .evals import qasper  # noqa: F401, E402

# Knowledge QA benchmarks
from .evals import logiqa  # noqa: F401, E402
from .evals import mathqa  # noqa: F401, E402
from .evals import sciq  # noqa: F401, E402
from .evals import truthfulqa  # noqa: F401, E402

# Linguistic Phenomena benchmarks
from .evals import blimp  # noqa: F401, E402

# MathArena benchmarks
from .evals.matharena.aime_2023_I.aime_2023_I import aime_2023_I  # noqa: F401, E402
from .evals.matharena.aime_2023_II.aime_2023_II import aime_2023_II  # noqa: F401, E402
from .evals.matharena.aime_2024_I.aime_2024_I import aime_2024_I  # noqa: F401, E402
from .evals.matharena.aime_2024_II.aime_2024_II import aime_2024_II  # noqa: F401, E402
from .evals.matharena.aime_2024.aime_2024 import aime_2024  # noqa: F401, E402
from .evals.matharena.aime_2025.aime_2025 import aime_2025  # noqa: F401, E402
from .evals.matharena.aime_2025_II.aime_2025_II import aime_2025_II  # noqa: F401, E402
from .evals.matharena.brumo_2025.brumo_2025 import brumo_2025  # noqa: F401, E402
from .evals.matharena.hmmt_feb_2023.hmmt_feb_2023 import hmmt_feb_2023  # noqa: F401, E402
from .evals.matharena.hmmt_feb_2024.hmmt_feb_2024 import hmmt_feb_2024  # noqa: F401, E402
from .evals.matharena.hmmt_feb_2025.hmmt_feb_2025 import hmmt_feb_2025  # noqa: F401, E402

# Domain-Specific benchmarks
from .evals.arabic_exams import (  # noqa: F401, E402
    arabic_exams,
    arabic_exams_accounting_university,
    arabic_exams_arabic_language_general,
    arabic_exams_arabic_language_grammar,
    arabic_exams_arabic_language_high_school,
    arabic_exams_arabic_language_middle_school,
    arabic_exams_arabic_language_primary_school,
    arabic_exams_biology_high_school,
    arabic_exams_civics_high_school,
    arabic_exams_civics_middle_school,
    arabic_exams_computer_science_high_school,
    arabic_exams_computer_science_middle_school,
    arabic_exams_computer_science_primary_school,
    arabic_exams_computer_science_university,
    arabic_exams_driving_test,
    arabic_exams_economics_high_school,
    arabic_exams_economics_middle_school,
    arabic_exams_economics_university,
    arabic_exams_general_knowledge,
    arabic_exams_general_knowledge_middle_school,
    arabic_exams_general_knowledge_primary_school,
    arabic_exams_geography_high_school,
    arabic_exams_geography_middle_school,
    arabic_exams_geography_primary_school,
    arabic_exams_history_high_school,
    arabic_exams_history_middle_school,
    arabic_exams_history_primary_school,
    arabic_exams_islamic_studies_general,
    arabic_exams_islamic_studies_high_school,
    arabic_exams_islamic_studies_middle_school,
    arabic_exams_islamic_studies_primary_school,
    arabic_exams_law_professional,
    arabic_exams_management_university,
    arabic_exams_math_primary_school,
    arabic_exams_natural_science_middle_school,
    arabic_exams_natural_science_primary_school,
    arabic_exams_philosophy_high_school,
    arabic_exams_physics_high_school,
    arabic_exams_political_science_university,
    arabic_exams_social_science_middle_school,
    arabic_exams_social_science_primary_school,
)
from .evals.legalsupport import legalsupport  # noqa: F401, E402
