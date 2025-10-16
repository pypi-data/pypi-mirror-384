from inspect_ai import task, Task
from inspect_ai.model import GenerateConfig
from openbench.utils.mcq import MCQEval, MCQSample
from openbench.utils.text import MULTIPLE_CHOICE_PROMPT_TEMPLATE

# Adapted from https://github.com/openai/simple-evals

SUBJECT_TO_CATEGORY = {
    "abstract_algebra": "stem",
    "anatomy": "other",
    "astronomy": "stem",
    "business_ethics": "other",
    "clinical_knowledge": "other",
    "college_biology": "stem",
    "college_chemistry": "stem",
    "college_computer_science": "stem",
    "college_mathematics": "stem",
    "college_medicine": "other",
    "college_physics": "stem",
    "computer_security": "stem",
    "conceptual_physics": "stem",
    "econometrics": "social_sciences",
    "electrical_engineering": "stem",
    "elementary_mathematics": "stem",
    "formal_logic": "humanities",
    "global_facts": "other",
    "high_school_biology": "stem",
    "high_school_chemistry": "stem",
    "high_school_computer_science": "stem",
    "high_school_european_history": "humanities",
    "high_school_geography": "social_sciences",
    "high_school_government_and_politics": "social_sciences",
    "high_school_macroeconomics": "social_sciences",
    "high_school_mathematics": "stem",
    "high_school_microeconomics": "social_sciences",
    "high_school_physics": "stem",
    "high_school_psychology": "social_sciences",
    "high_school_statistics": "stem",
    "high_school_us_history": "humanities",
    "high_school_world_history": "humanities",
    "human_aging": "other",
    "human_sexuality": "social_sciences",
    "international_law": "humanities",
    "jurisprudence": "humanities",
    "logical_fallacies": "humanities",
    "machine_learning": "stem",
    "management": "other",
    "marketing": "other",
    "medical_genetics": "other",
    "miscellaneous": "other",
    "moral_disputes": "humanities",
    "moral_scenarios": "humanities",
    "nutrition": "other",
    "philosophy": "humanities",
    "prehistory": "humanities",
    "professional_accounting": "other",
    "professional_law": "humanities",
    "professional_medicine": "other",
    "professional_psychology": "social_sciences",
    "public_relations": "social_sciences",
    "security_studies": "social_sciences",
    "sociology": "social_sciences",
    "us_foreign_policy": "social_sciences",
    "virology": "other",
    "world_religions": "humanities",
}

LANGUAGES = [
    "AR_XY",
    "BN_BD",
    "DE_DE",
    "ES_LA",
    "FR_FR",
    "HI_IN",
    "ID_ID",
    "IT_IT",
    "JA_JP",
    "KO_KR",
    "PT_BR",
    "ZH_CN",
    "SW_KE",
    "YO_NG",
]


def record_to_mcq_sample(record: dict[str, str]) -> MCQSample:
    """Convert a MMLU record to an OpenBench MCQSample."""
    return MCQSample(
        input=MULTIPLE_CHOICE_PROMPT_TEMPLATE.format(
            prompt=record["Question"],
            option_a=record["A"],
            option_b=record["B"],
            option_c=record["C"],
            option_d=record["D"],
        ),
        target=record["Answer"],
        metadata={
            "subject": record["Subject"],
            "category": SUBJECT_TO_CATEGORY[record["Subject"]]
            if record["Subject"] in SUBJECT_TO_CATEGORY
            else "Invalid Subject: " + record["Subject"],
        },
    )


@task
def mmmlu(language: str = "") -> Task:
    """Evaluate the MMMLU dataset (MMLU translated to 15 languages). MCQ Abstracted."""
    if language == "EN_US":
        # redirect to mmlu if language is EN_US
        raise ValueError("EN_US is not supported by MMMLU. Use mmlu() instead.")
    elif language in LANGUAGES:
        # specific language, use the corresponding dataset
        dataset_path = "openai/MMMLU"
        subset_name = language
    elif not language.strip():
        # default: no language given → run all
        dataset_path = "openai/MMMLU"
        subset_name = None
    else:
        raise ValueError(
            f"Language {language} not supported. Make sure to use a valid language code: {LANGUAGES}"
        )

    return MCQEval(
        name="mmmlu",
        dataset_path=dataset_path,
        subset_name=subset_name,
        record_to_mcq_sample=record_to_mcq_sample,
        split="test",
        auto_id=True,
        config=GenerateConfig(
            temperature=0.5,
        ),
        group_keys=["category"],
    )


# Language-specific wrappers for individual evaluation
mmmlu_ar_xy = task(lambda: mmmlu(language="AR_XY"))
mmmlu_bn_bd = task(lambda: mmmlu(language="BN_BD"))
mmmlu_de_de = task(lambda: mmmlu(language="DE_DE"))
mmmlu_es_la = task(lambda: mmmlu(language="ES_LA"))
mmmlu_fr_fr = task(lambda: mmmlu(language="FR_FR"))
mmmlu_hi_in = task(lambda: mmmlu(language="HI_IN"))
mmmlu_id_id = task(lambda: mmmlu(language="ID_ID"))
mmmlu_it_it = task(lambda: mmmlu(language="IT_IT"))
mmmlu_ja_jp = task(lambda: mmmlu(language="JA_JP"))
mmmlu_ko_kr = task(lambda: mmmlu(language="KO_KR"))
mmmlu_pt_br = task(lambda: mmmlu(language="PT_BR"))
mmmlu_zh_cn = task(lambda: mmmlu(language="ZH_CN"))
mmmlu_sw_ke = task(lambda: mmmlu(language="SW_KE"))
mmmlu_yo_ng = task(lambda: mmmlu(language="YO_NG"))
