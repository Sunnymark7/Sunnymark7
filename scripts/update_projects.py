#!/usr/bin/env python3
"""Build a project-first GitHub Profile README from repository topics."""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
CONFIG_PATH = ROOT / "data" / "projects.json"
START_MARKER = "<!-- AUTO-PROJECTS:START -->"
END_MARKER = "<!-- AUTO-PROJECTS:END -->"
API_ROOT = "https://api.github.com"
CONTROL_TOPIC_PREFIXES = ("project-", "portfolio-", "status-")


def api_get(path: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Sunnymark7-profile-sync",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{API_ROOT}{path}", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def api_get_all(path: str, token: str | None) -> list[dict[str, Any]]:
    """Read every GitHub API page instead of silently stopping at 100 repos."""
    repositories: list[dict[str, Any]] = []
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        batch = api_get(f"{path}{separator}per_page=100&page={page}", token)
        if not isinstance(batch, list):
            raise TypeError("GitHub repository response must be a list")
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def fetch_repositories(owner: str) -> tuple[list[dict[str, Any]], bool]:
    """Fetch private repos when configured; fail closed if that source is unavailable."""
    profile_token = os.environ.get("PROFILE_REPO_TOKEN", "").strip()
    github_token = os.environ.get("GITHUB_TOKEN", "").strip() or None

    if profile_token:
        try:
            repositories = api_get_all(
                "/user/repos?affiliation=owner&visibility=all&sort=pushed",
                profile_token,
            )
            owned = [
                repo
                for repo in repositories
                if repo.get("owner", {}).get("login", "").casefold() == owner.casefold()
            ]
            return owned, True
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
            detail = getattr(error, "code", error.__class__.__name__)
            raise RuntimeError(
                f"private repository lookup failed ({detail}); refusing to publish partial counts"
            ) from error

    encoded_owner = urllib.parse.quote(owner, safe="")
    public_path = f"/users/{encoded_owner}/repos?type=owner&sort=pushed"
    try:
        return api_get_all(public_path, github_token), False
    except urllib.error.HTTPError as error:
        if not github_token or error.code not in {401, 403}:
            raise
        print(
            f"warning: public token lookup failed ({error.code}); retrying anonymously",
            file=sys.stderr,
        )
        return api_get_all(public_path, None), False


def topic_names(repo: dict[str, Any]) -> list[str]:
    return [str(topic).casefold() for topic in repo.get("topics") or []]


def is_visible_repo(repo: dict[str, Any], config: dict[str, Any]) -> bool:
    if repo.get("name", "").casefold() == config["profile_repository"].casefold():
        return False
    if repo.get("fork") and not config.get("include_forks", False):
        return False
    if repo.get("archived") and not config.get("include_archived", False):
        return False
    return "portfolio-hide" not in topic_names(repo)


def words(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold()))


def repository_words(repo: dict[str, Any]) -> set[str]:
    values = [str(repo.get("name", "")), str(repo.get("description") or "")]
    values.extend(str(topic) for topic in repo.get("topics") or [])
    return words(" ".join(values))


def project_topics(repo: dict[str, Any]) -> list[str]:
    return sorted({topic for topic in topic_names(repo) if topic.startswith("project-")})


def classify(repo: dict[str, Any], categories: list[dict[str, Any]]) -> str | None:
    """Prefer an explicit project topic; otherwise use token-aware keywords."""
    topics = project_topics(repo)
    configured_order = [str(category["topic"]).casefold() for category in categories]
    if topics:
        if len(topics) > 1:
            if repo.get("private"):
                warning = "private repository has multiple project topics; using configured order"
            else:
                warning = (
                    f"{repo.get('name', 'repository')} has multiple project topics: "
                    + ", ".join(topics)
                )
            print(f"warning: {warning}", file=sys.stderr)
        for configured_topic in configured_order:
            if configured_topic in topics:
                return configured_topic
        return topics[0]

    repo_words = repository_words(repo)
    for category in categories:
        for keyword in category.get("keywords", []):
            keyword_words = words(str(keyword))
            if keyword_words and keyword_words <= repo_words:
                return str(category["topic"])
    return None


def dynamic_category(topic: str | None) -> dict[str, Any]:
    if topic is None:
        return {
            "topic": "repository-inbox",
            "source_key": None,
            "icon": "◌",
            "title": "Project Inbox",
            "subtitle": "待归类",
            "description": "已自动发现，但还没有 project-* Topic 的公开仓库。",
            "stack": ["Needs topic"],
        }
    slug = topic.removeprefix("project-") or "untitled"
    title = " ".join(part.capitalize() for part in slug.split("-") if part)
    return {
        "topic": topic,
        "icon": "✦",
        "title": title,
        "subtitle": "自动创建的项目族",
        "description": f"由 `{topic}` Topic 自动发现；可在 data/projects.json 中补充正式说明。",
        "stack": ["Auto-routed"],
    }


def validate_config(config: dict[str, Any]) -> None:
    topics = [str(category["topic"]).casefold() for category in config["categories"]]
    if len(topics) != len(set(topics)):
        raise ValueError("category topics must be unique")
    invalid_topics = [topic for topic in topics if not topic.startswith("project-")]
    if invalid_topics:
        raise ValueError(f"category topics must start with project-: {invalid_topics}")
    known = set(topics)
    for project in config.get("curated_projects", []):
        if str(project["category"]).casefold() not in known:
            raise ValueError(f"curated project uses unknown category: {project['category']}")


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def html_text(value: Any) -> str:
    return html.escape(clean_text(value), quote=True)


def repo_technologies(repo: dict[str, Any]) -> list[str]:
    technologies: list[str] = []
    language = clean_text(repo.get("language"))
    if language:
        technologies.append(language)
    for topic in repo.get("topics") or []:
        topic = clean_text(topic)
        if not topic or topic.casefold().startswith(CONTROL_TOPIC_PREFIXES):
            continue
        if topic.casefold() in {value.casefold() for value in technologies}:
            continue
        technologies.append(topic)
        if len(technologies) == 3:
            break
    return technologies or ["Repository"]


def status_from_repo(repo: dict[str, Any]) -> str:
    statuses = {
        "status-active": "Active",
        "status-research": "Research",
        "status-prototype": "Prototype",
        "status-maintained": "Maintained",
        "status-completed": "Completed",
    }
    topics = set(topic_names(repo))
    for topic, label in statuses.items():
        if topic in topics:
            return label
    return "Archived" if repo.get("archived") else "Maintained"


def public_project(
    repo: dict[str, Any],
    category: str,
    overrides: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    override = overrides.get(str(repo.get("name")), {})
    pushed = clean_text(repo.get("pushed_at"))[:7] or "recently"
    technologies = override.get("technologies") or repo_technologies(repo)
    return {
        "category": category,
        "title": override.get("title") or repo.get("name") or "Repository",
        "eyebrow": override.get("eyebrow") or "PUBLIC REPOSITORY",
        "status": override.get("status") or status_from_repo(repo),
        "description": override.get("description")
        or repo.get("description")
        or "说明正在完善的工程仓库。",
        "technologies": list(technologies)[:3],
        "meta": override.get("meta") or f"Last delivery · {pushed}",
        "url": repo.get("html_url"),
        "preview": override.get("preview"),
        "featured": bool(override.get("featured") or "portfolio-featured" in topic_names(repo)),
        "pushed_at": repo.get("pushed_at") or "",
    }


def render_technologies(technologies: list[str]) -> str:
    return " ".join(f"<code>{html_text(value)}</code>" for value in technologies[:3])


def render_project_card(project: dict[str, Any]) -> list[str]:
    title = html_text(project["title"])
    url = clean_text(project.get("url"))
    title_html = f'<a href="{html_text(url)}">{title}</a>' if url else title
    lines = [
        f"<sub><strong>{html_text(project.get('eyebrow'))}</strong> · "
        f"<code>{html_text(project.get('status')).upper()}</code></sub>",
    ]
    preview = clean_text(project.get("preview"))
    if preview:
        image = (
            f'<img src="{html_text(preview)}" width="70%" '
            f'alt="{title} preview">'
        )
        preview_html = f'<a href="{html_text(url)}">{image}</a>' if url else image
        lines.extend([f'<p align="center">{preview_html}</p>'])
    lines.extend(
        [
            f"<h3>{title_html}</h3>",
            f"<p>{html_text(project.get('description'))}</p>",
            f"<p>{render_technologies(list(project.get('technologies') or []))}</p>",
            f"<sub>{html_text(project.get('meta'))}</sub>",
        ]
    )
    if url:
        lines.append(f'<p><a href="{html_text(url)}"><strong>View repository →</strong></a></p>')
    reference_url = clean_text(project.get("reference_url"))
    if reference_url:
        reference_label = project.get("reference_label") or "View reference →"
        lines.append(
            f'<p><a href="{html_text(reference_url)}"><strong>'
            f"{html_text(reference_label)}</strong></a></p>"
        )
    return lines


def render_cards(projects: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for project in projects:
        lines.extend(["<table>", "  <tr>", '    <td width="100%" valign="top">'])
        lines.extend(f"      {line}" for line in render_project_card(project))
        lines.extend(["    </td>", "  </tr>", "</table>", ""])
    return lines


def render_atlas_card(category: dict[str, Any], system_count: int) -> list[str]:
    topic = html_text(category["topic"])
    noun = "system" if system_count == 1 else "systems"
    stack = render_technologies(list(category.get("stack") or []))
    count_label = category.get("count_label") or f"{system_count} {noun}"
    href = category.get("href") or f"#{topic}"
    return [
        f"<h3>{html_text(category.get('icon'))} {html_text(category.get('title'))}</h3>",
        f"<sub>{html_text(category.get('subtitle'))}</sub>",
        f"<p>{html_text(category.get('description'))}</p>",
        f"<p><code>{html_text(count_label)}</code> {stack}</p>",
        f'<a href="{html_text(href)}"><strong>{html_text(category.get("link_label") or "Explore project family →")}</strong></a>',
    ]


def render_atlas(categories: list[tuple[dict[str, Any], int]]) -> list[str]:
    lines = ["<table>"]
    for index in range(0, len(categories), 2):
        pair = categories[index : index + 2]
        lines.append("  <tr>")
        for category, system_count in pair:
            width = "100%" if len(pair) == 1 else "50%"
            colspan = ' colspan="2"' if len(pair) == 1 else ""
            lines.append(f'    <td width="{width}" valign="top"{colspan}>')
            lines.extend(
                f"      {line}" for line in render_atlas_card(category, system_count)
            )
            lines.append("    </td>")
        lines.append("  </tr>")
    lines.append("</table>")
    return lines


def render_index(
    repositories: list[dict[str, Any]],
    config: dict[str, Any],
    private_access: bool,
) -> str:
    categories = list(config["categories"])
    configured = {str(category["topic"]): category for category in categories}
    grouped_repositories: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    private_inbox_count = 0
    for repo in repositories:
        assigned_topic = classify(repo, categories)
        if repo.get("private") and assigned_topic not in configured:
            private_inbox_count += 1
            continue
        grouped_repositories[assigned_topic].append(repo)

    curated_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for project in config.get("curated_projects", []):
        curated = dict(project)
        curated["featured"] = bool(curated.get("featured"))
        curated_by_category[str(project["category"])].append(curated)

    discovered_topics = sorted(
        topic
        for topic in grouped_repositories
        if topic is not None and topic not in configured
    )
    if None in grouped_repositories:
        discovered_topics.append(None)
    all_categories = categories + [dynamic_category(topic) for topic in discovered_topics]

    sections: list[tuple[dict[str, Any], list[dict[str, Any]], int]] = []
    overrides = config.get("repository_overrides", {})
    for category in all_categories:
        topic = str(category["topic"])
        source_key = category.get("source_key", topic)
        category_repositories = grouped_repositories.get(source_key, [])
        public_projects = [
            public_project(repo, topic, overrides)
            for repo in category_repositories
            if not repo.get("private")
        ]
        public_projects.sort(
            key=lambda project: (bool(project.get("featured")), str(project.get("pushed_at"))),
            reverse=True,
        )
        curated_projects = curated_by_category.get(topic, [])
        if private_access:
            fetched_private_count = sum(bool(repo.get("private")) for repo in category_repositories)
            extra_private_count = max(0, fetched_private_count - len(curated_projects))
        else:
            extra_private_count = 0
        projects = curated_projects + public_projects
        if projects or extra_private_count:
            sections.append((category, projects, extra_private_count))

    if private_access and private_inbox_count:
        sections.append(
            (
                {
                    "topic": "private-inbox",
                    "icon": "🔒",
                    "title": "Private Inbox",
                    "subtitle": "等待安全策展",
                    "description": "已发现新的私有工作，但不会公开仓库名、Topic 或技术细节。",
                    "stack": ["Private", "Unpublished"],
                },
                [],
                private_inbox_count,
            )
        )

    total_systems = sum(len(projects) + extra for _, projects, extra in sections)
    lines = [
        START_MARKER,
        "<!-- Generated by scripts/update_projects.py; do not edit this block manually. -->",
        "",
        '<p align="center">',
        f"  <strong>{total_systems} organized systems</strong> · {len(sections)} project families · topic-routed &amp; auto-synced",
        "</p>",
        "",
    ]
    atlas_categories = [
        (category, len(projects) + extra)
        for category, projects, extra in sections
    ]
    atlas_categories.append(
        (
            {
                "topic": "automation",
                "icon": "⚙️",
                "title": "Auto Routing",
                "subtitle": "仓库自动整理",
                "description": "Topic 决定项目族，工作流负责发现、排序、隐私过滤和页面更新。",
                "stack": ["Topics", "Actions", "Privacy"],
                "count_label": "Every 6h",
                "href": "#automation",
                "link_label": "Add or organize a repository →",
            },
            0,
        )
    )
    lines.extend(render_atlas(atlas_categories))
    lines.extend(["", "## ✦ Engineering systems", ""])

    for category, projects, extra_private_count in sections:
        topic = html_text(category["topic"])
        lines.extend(
            [
                f'<a id="{topic}"></a>',
                f"### {category.get('icon', '✦')} {category['title']} · {category.get('subtitle', '')}",
                "",
                clean_text(category.get("description")),
                "",
                f"<sub><code>{topic}</code> · {len(projects) + extra_private_count} "
                f"{'system' if len(projects) + extra_private_count == 1 else 'systems'}</sub>",
                "",
            ]
        )
        feature_asset = clean_text(category.get("feature_asset"))
        if feature_asset:
            lines.extend(
                [
                    '<p align="center">',
                    f'  <img src="{html_text(feature_asset)}" width="100%" alt="{html_text(category["title"])} signal path">',
                    "</p>",
                    "",
                ]
            )
        if projects:
            lines.extend(render_cards(projects))
            lines.append("")
        if extra_private_count:
            noun = "repository" if extra_private_count == 1 else "repositories"
            verb = "is" if extra_private_count == 1 else "are"
            lines.extend(
                [
                    f"<sub>🔒 {extra_private_count} additional private {noun} {verb} grouped here; names and links stay private.</sub>",
                    "",
                ]
            )

    access_note = "公开仓库自动同步；不会自动公开未经策展的私有仓库名称和链接，只展示人工确认的项目标题、安全摘要或额外数量。"
    lines.extend([f"<sub>{access_note}</sub>", "", END_MARKER])
    return "\n".join(lines)


def replace_generated_section(readme: str, generated: str) -> str:
    if readme.count(START_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise ValueError("README must contain exactly one generated project section")
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.DOTALL,
    )
    return pattern.sub(lambda _: generated, readme)


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    validate_config(config)
    repositories, private_access = fetch_repositories(config["owner"])
    repositories = [repo for repo in repositories if is_visible_repo(repo, config)]

    readme = README_PATH.read_text(encoding="utf-8")
    generated = render_index(repositories, config, private_access)
    updated = replace_generated_section(readme, generated)
    README_PATH.write_text(updated.rstrip() + "\n", encoding="utf-8", newline="\n")

    visibility = "public + private counts" if private_access else "public + curated private"
    print(f"profile atlas updated from {len(repositories)} repositories ({visibility})")


if __name__ == "__main__":
    main()
