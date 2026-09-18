import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from load_benchmark import validate_dataset


REQUIRED_RULES = {f"R{number:02d}" for number in range(1, 15)}
REQUIRED_CATEGORIES = {
    "HOTEL",
    "MEALS",
    "TRANSPORTATION",
    "AIRFARE",
    "SOFTWARE",
    "OFFICE_SUPPLIES",
}
REQUIRED_ROUTES = {
    "SCREENING_COMPLETE",
    "NEEDS_INFORMATION",
    "HUMAN_REVIEW",
    "POLICY_CLARIFICATION",
    "SYSTEM_RECOVERY",
    "NOT_ADMITTED",
}
REQUIRED_RELATIONSHIPS = {
    "COUNTERFACTUAL",
    "BOUNDARY_VARIANT",
    "DUPLICATE_VARIANT",
    "ADVERSARIAL",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audita cobertura y separación del benchmark NERIA"
    )
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.fixture.read_text(encoding="utf-8"))
    cases, dataset_hash = validate_dataset(payload)
    manifest = payload["manifest"]

    split_counts = Counter(case["split"] for case in cases)
    family_members: dict[str, list[dict]] = defaultdict(list)
    rule_counts: Counter[str] = Counter()
    category_counts = Counter(case["category_hint"] for case in cases)
    route_counts = Counter(case["label"]["expected_route"] for case in cases)
    relationship_counts: Counter[str] = Counter()

    for case in cases:
        family_members[case["family_key"]].append(case)
        rule_counts.update(
            rule["rule_code"] for rule in case["label"]["rules"]
        )
        relationship = case.get("relationship")
        if relationship:
            relationship_counts[relationship["relationship_type"]] += 1

    require(len(cases) == 300, "Expected exactly 300 cases")
    require(split_counts["DEVELOPMENT"] == 180, "Expected 180 DEVELOPMENT cases")
    require(split_counts["HOLDOUT"] == 120, "Expected 120 HOLDOUT cases")
    require(manifest["holdout_locked"] is True, "HOLDOUT must be locked")
    require(len(family_members) == 150, "Expected exactly 150 families")
    require(
        all(len(members) == 2 for members in family_members.values()),
        "Every family must contain exactly two cases",
    )
    require(
        all(len({case["split"] for case in members}) == 1
            for members in family_members.values()),
        "A family leaked between DEVELOPMENT and HOLDOUT",
    )
    require(REQUIRED_RULES <= set(rule_counts), "R01-R14 coverage is incomplete")
    require(
        REQUIRED_CATEGORIES <= set(category_counts),
        "Category coverage is incomplete",
    )
    require(REQUIRED_ROUTES <= set(route_counts), "Route coverage is incomplete")
    require(
        REQUIRED_RELATIONSHIPS <= set(relationship_counts),
        "Relationship coverage is incomplete",
    )

    print("Coverage: PASS")
    print(f"Dataset hash: {dataset_hash}")
    print(f"Cases: {len(cases)}")
    print(f"Families: {len(family_members)}")
    print(f"Splits: {dict(sorted(split_counts.items()))}")
    print(f"Rules covered: {', '.join(sorted(rule_counts))}")
    print(f"Categories: {dict(sorted(category_counts.items()))}")
    print(f"Routes: {dict(sorted(route_counts.items()))}")
    print(f"Relationships: {dict(sorted(relationship_counts.items()))}")


if __name__ == "__main__":
    main()
