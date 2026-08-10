from __future__ import annotations

import importlib.util
import io
import os
import sys
import unittest
import urllib.error
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_projects.py"
SPEC = importlib.util.spec_from_file_location("update_projects", SCRIPT)
assert SPEC and SPEC.loader
update_projects = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = update_projects
SPEC.loader.exec_module(update_projects)


CATEGORIES = [
    {
        "topic": "project-ehand",
        "title": "eHand",
        "keywords": ["smart-glove", "tactile"],
    },
    {
        "topic": "project-embedded",
        "title": "Embedded",
        "keywords": ["esp32", "firmware"],
    },
]


class ProjectRoutingTests(unittest.TestCase):
    def test_explicit_topic_wins_over_keywords(self) -> None:
        repo = {
            "name": "esp32-tool",
            "description": "firmware",
            "topics": ["project-ehand"],
        }
        self.assertEqual(update_projects.classify(repo, CATEGORIES), "project-ehand")

    def test_unknown_project_topic_creates_new_group(self) -> None:
        repo = {"name": "arm", "topics": ["project-robotics"]}
        self.assertEqual(update_projects.classify(repo, CATEGORIES), "project-robotics")

    def test_keyword_matching_uses_tokens_not_substrings(self) -> None:
        near_miss = {"name": "myesp32ishthing", "topics": []}
        match = {"name": "esp32-firmware-tool", "topics": []}
        self.assertIsNone(update_projects.classify(near_miss, CATEGORIES))
        self.assertEqual(update_projects.classify(match, CATEGORIES), "project-embedded")

    def test_multiple_topics_are_deterministic(self) -> None:
        repo = {
            "name": "mixed",
            "topics": ["project-embedded", "project-ehand"],
        }
        with patch("sys.stderr") as stderr:
            self.assertEqual(update_projects.classify(repo, CATEGORIES), "project-ehand")
            self.assertTrue(stderr.write.called)

    def test_private_multiple_topic_warning_is_anonymous(self) -> None:
        repo = {
            "name": "confidential-client-name",
            "private": True,
            "topics": ["project-secret-alpha", "project-secret-beta"],
        }
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            update_projects.classify(repo, CATEGORIES)
        warning = stderr.getvalue()
        self.assertIn("private repository", warning)
        self.assertNotIn("confidential-client-name", warning)
        self.assertNotIn("secret-alpha", warning)

    def test_hidden_fork_archived_and_profile_repositories_are_filtered(self) -> None:
        config = {
            "profile_repository": "Sunnymark7",
            "include_forks": False,
            "include_archived": False,
        }
        self.assertFalse(
            update_projects.is_visible_repo(
                {"name": "secret", "topics": ["portfolio-hide"]}, config
            )
        )
        self.assertFalse(update_projects.is_visible_repo({"name": "fork", "fork": True}, config))
        self.assertFalse(
            update_projects.is_visible_repo({"name": "old", "archived": True}, config)
        )
        self.assertFalse(update_projects.is_visible_repo({"name": "Sunnymark7"}, config))


class ApiTests(unittest.TestCase):
    def test_pagination_reads_beyond_one_hundred(self) -> None:
        first_page = [{"name": f"repo-{index}"} for index in range(100)]
        with patch.object(
            update_projects, "api_get", side_effect=[first_page, [{"name": "last"}]]
        ) as api_get:
            repos = update_projects.api_get_all("/repos?sort=pushed", "token")
        self.assertEqual(len(repos), 101)
        self.assertIn("page=1", api_get.call_args_list[0].args[0])
        self.assertIn("page=2", api_get.call_args_list[1].args[0])

    def test_invalid_private_token_fails_closed(self) -> None:
        unauthorized = urllib.error.HTTPError(None, 401, "bad token", None, None)
        env = {"PROFILE_REPO_TOKEN": "invalid-private", "GITHUB_TOKEN": "workflow-token"}
        with patch.dict(os.environ, env, clear=True), patch.object(
            update_projects,
            "api_get_all",
            side_effect=unauthorized,
        ) as api_get_all:
            with self.assertRaisesRegex(RuntimeError, "refusing to publish partial counts"):
                update_projects.fetch_repositories("Sunnymark7")
        self.assertEqual(api_get_all.call_count, 1)


class RenderingTests(unittest.TestCase):
    def config(self) -> dict:
        return {
            "owner": "Sunnymark7",
            "profile_repository": "Sunnymark7",
            "include_forks": False,
            "include_archived": False,
            "categories": [
                {
                    "topic": "project-ehand",
                    "icon": "H",
                    "title": "eHand",
                    "subtitle": "Tactile",
                    "description": "Signal loop",
                    "stack": ["Python"],
                    "keywords": ["ehand"],
                }
            ],
            "curated_projects": [],
            "repository_overrides": {},
        }

    def test_private_repository_name_and_url_never_render(self) -> None:
        repo = {
            "name": "confidential-name",
            "html_url": "https://example.test/private-url",
            "private": True,
            "topics": ["project-ehand"],
        }
        rendered = update_projects.render_index([repo], self.config(), private_access=True)
        self.assertNotIn("confidential-name", rendered)
        self.assertNotIn("private-url", rendered)
        self.assertIn("1 additional private repository", rendered)

    def test_unknown_private_topic_is_anonymized(self) -> None:
        repo = {
            "name": "confidential-client-name",
            "html_url": "https://example.test/private-url",
            "private": True,
            "topics": ["project-secret-medical-device"],
        }
        rendered = update_projects.render_index([repo], self.config(), private_access=True)
        self.assertIn("Private Inbox", rendered)
        self.assertIn("1 additional private repository", rendered)
        self.assertNotIn("confidential-client-name", rendered)
        self.assertNotIn("private-url", rendered)
        self.assertNotIn("secret-medical-device", rendered)
        self.assertNotIn("Secret Medical Device", rendered)

    def test_dynamic_group_and_html_escaping(self) -> None:
        repo = {
            "name": "robot<lab>",
            "html_url": "https://example.test/robot",
            "description": "A & B",
            "private": False,
            "topics": ["project-robotics"],
            "pushed_at": "2026-08-01T00:00:00Z",
        }
        rendered = update_projects.render_index([repo], self.config(), private_access=False)
        self.assertIn("Robotics", rendered)
        self.assertIn("robot&lt;lab&gt;", rendered)
        self.assertIn("A &amp; B", rendered)

    def test_generated_section_replacement_is_idempotent(self) -> None:
        readme = "before\n<!-- AUTO-PROJECTS:START -->old<!-- AUTO-PROJECTS:END -->\nafter"
        generated = "<!-- AUTO-PROJECTS:START -->new<!-- AUTO-PROJECTS:END -->"
        once = update_projects.replace_generated_section(readme, generated)
        twice = update_projects.replace_generated_section(once, generated)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
