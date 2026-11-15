"""Version comparison and update-note helpers."""
from ._nono_versions import (
    version_tag_key, is_version_tag, is_release_version, sort_version_tags, is_greater_version,
)


def select_kept_tags(tag_names, keep):
    """Return the version tags a repository keeps, newest first.

    The ``keep`` newest releases and the prereleases newer than the oldest of
    them, as the launcher's ``keep_releases`` does. With fewer releases than
    ``keep`` every version tag is kept.
    """
    kept = []
    releases = 0
    for name in sort_version_tags(tag_names):
        if releases >= keep:
            break
        if is_release_version(name):
            releases += 1
        kept.append(name)
    return kept


def is_supported_pyappify_version(version):
    """Return whether a PyAppify version is valid and supports version checks."""
    if not isinstance(version, str) or not version:
        return False

    normalized = version[1:] if version.startswith("v") else version
    parts = normalized.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return False

    return tuple(int(part) for part in parts) >= (1, 2, 2)


def entry_notes(entry, language=None):
    """A version entry's notes in ``language``, a locale such as ``zh_CN`` or ``ja``.

    Its ``localized_notes`` (present when the notes come from the app's
    changelogs) in ``language``, else its ``update_note``.
    """
    if language:
        from .i18n import language_from_locale

        language = language_from_locale(language)
    localized = entry.get("localized_notes") if language else None
    if isinstance(localized, dict) and isinstance(localized.get(language), list):
        return localized[language]
    raw_notes = entry.get("update_note") or []
    return raw_notes if isinstance(raw_notes, list) else [raw_notes]


def calculate_update_notes(update_notes, current_version, target_version, language=None):
    """Return descending notes without including versions newer than the target.

    With ``language`` (such as ``"zh-CN"``), versions whose notes come from the
    app's changelogs show them in that language; see :func:`entry_notes`.
    """
    if not isinstance(update_notes, list):
        raise TypeError("update_notes must be a list")

    versions = [
        item for item in update_notes
        if isinstance(item, dict) and item.get("version")
    ]

    def normalize(version):
        return str(version or "").lstrip("v")

    def find_index(version):
        normalized = normalize(version)
        return next(
            (index for index, item in enumerate(versions)
             if normalize(item["version"]) == normalized),
            None,
        )

    target_index = find_index(target_version)
    if target_index is None:
        return []

    current_index = find_index(current_version)
    if current_index is None:
        selected_versions = versions[target_index:]
    else:
        first = min(current_index, target_index)
        last = max(current_index, target_index)
        selected_versions = versions[first:last + 1]

    notes = []
    for item in selected_versions:
        notes.extend(entry_notes(item, language))
    return [str(note) for note in notes]
