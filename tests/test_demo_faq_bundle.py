import json
from pathlib import Path


def test_demo_faq_bundle_structure_and_golden_suite():
    repo_root = Path(__file__).resolve().parents[1]
    bundle_root = repo_root / "data" / "bundles" / "demo" / "faq"

    required_files = [
        bundle_root / "manifest.yaml",
        bundle_root / "ontology" / "ontology.yaml",
        bundle_root / "entities" / "faq_answer.schema.yaml",
        bundle_root / "data" / "faq.json",
        bundle_root / "policies" / "security.yaml",
        bundle_root / "templates" / "faq_answer.j2",
        bundle_root / "suites" / "faq_golden.json",
        bundle_root / "metadata" / "bundle.yaml",
    ]

    for file_path in required_files:
        assert file_path.is_file(), f"Missing required bundle file: {file_path}"

    faq_data = json.loads((bundle_root / "data" / "faq.json").read_text(encoding="utf-8"))
    answers_by_question = {item["question"]: item["answer"] for item in faq_data}

    golden_cases = json.loads(
        (bundle_root / "suites" / "faq_golden.json").read_text(encoding="utf-8")
    )

    for case in golden_cases:
        tenant_id = case.get("tenant_id")
        assert isinstance(tenant_id, str) and tenant_id.strip(), "tenant_id must be a non-empty string"

        question = case["question"]
        expected_answer = case["expected_answer"]
        assert question in answers_by_question, f"Question not found in FAQ dataset: {question}"
        assert (
            answers_by_question[question] == expected_answer
        ), f"Answer mismatch for question: {question}"
