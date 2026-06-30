"""Tests for query-aware candidate fit parsing."""

from talentscreen.agents.query_parsing import (
    candidate_has_skill,
    extract_min_years,
    extract_query_skills,
)


def test_extract_ai_ml_skills() -> None:
    skills = extract_query_skills("who has AI ML experience with min 2y experience")
    assert "ai" in skills
    assert "ml" in skills


def test_extract_java_aws() -> None:
    skills = extract_query_skills("Who has Java and AWS experience?")
    assert "java" in skills
    assert "aws" in skills


def test_extract_min_years() -> None:
    assert extract_min_years("min 2y experience") == 2
    assert extract_min_years("at least 5 years") == 5
    assert extract_min_years("no years mentioned") is None


def test_skill_matches_partial() -> None:
    assert candidate_has_skill(["Spring Boot", "AWS"], "spring")
    assert not candidate_has_skill(["Java", "AWS"], "ml")
