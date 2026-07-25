# Contributing to Instant Translate for Orca

Thank you for helping. Bug fixes, translations, documentation, accessibility
improvements, tests, and new ideas are all welcome. You do not need to be an
expert, and AI-assisted or “vibe coding” workflows are welcome too.

The important rule is simple: a human contributor must understand the change
well enough to review it and must manually verify that it works in Orca.
Automated checks are useful, but they do not replace manual testing with a
screen reader.

## Before making a change

- Keep the extension accessible by keyboard and understandable through speech
  and braille.
- Protect privacy. Never log source text, translated text, clipboard contents,
  or API keys.
- Use only Orca's documented user-extension API. Orca's other public-looking
  Python functions are internal and can change without notice.
- Keep network and other slow work away from Orca's main thread.
- Make focused changes that are easy to review and test.

For a larger feature or a behavior change, open an issue first so the approach
can be discussed before much work is done.

## Development setup

Python tools are declared in `pyproject.toml`. Orca, PyGObject, GTK, AT-SPI,
dconf, and libsecret are system packages and must be installed through your
Linux distribution.

Install the Python development tools:

```bash
python3 -m pip install -e '.[dev]'
```

Run the automated checks:

```bash
python3 -m pytest
python3 -m compileall -q instant_translate tests
ruff check .
mypy instant_translate
bandit -c pyproject.toml -r instant_translate
```

Add or update automated tests when practical. A passing test suite does not
prove that Orca presents the result correctly, so the manual checks below are
still required.

## Required manual testing

Install the draft into Orca's extension directory:

```bash
mkdir -p ~/.local/share/orca/extensions/instant_translate
cp -r instant_translate/. ~/.local/share/orca/extensions/instant_translate/
orca --approve-extension instant_translate
```

Restart Orca, then manually test all behavior affected by the change. At a
minimum:

1. Confirm the extension appears in **Orca Preferences → User Extensions** and
   its settings dialog opens.
2. Translate a selection from an accessible text control.
3. Translate ordinary text from the clipboard.
4. Confirm Orca speaks or displays the expected result without becoming
   unresponsive.
5. Exercise every setting, command, provider, success case, and error case
   touched by the change.
6. Check that no source text, result text, clipboard text, or API key appears in
   logs.
7. Restart Orca once more and check any setting or key-storage behavior that is
   expected to persist.

Use harmless sample text. If the change affects clipboard output, test it on
the display server you use and report whether that is Wayland or X11. If the
change affects localization, start a separate test session in the target
language and check settings, command descriptions, spoken messages, and errors.

Record the environment and results in the pull request, for example:

```text
Manual testing
- Orca version:
- Distribution and desktop:
- Wayland or X11:
- Providers tested:
- Steps performed:
- Result:
```

Do not mark a manual check as complete if it was only simulated, mocked, or run
by an automated test.

## Translations

User-visible text uses GNU gettext. Keep stable command names and setting keys
in English; translate labels, choices, messages, and errors.

When Python strings change, update the template and Turkish catalog from the
repository root:

```bash
xgettext --language=Python --from-code=UTF-8 \
    --keyword=_ \
    --keyword=N_ \
    --keyword=ngettext:1,2 \
    --keyword=pgettext:1c,2 \
    --keyword=npgettext:1c,2,3 \
    --add-comments=Translators \
    --sort-by-file \
    --output=instant_translate/po/instant_translate.pot \
    instant_translate/*.py instant_translate/backends/*.py

msgmerge --update \
    instant_translate/po/tr.po \
    instant_translate/po/instant_translate.pot

msgfmt --check \
    --output-file=instant_translate/locale/tr/LC_MESSAGES/instant_translate.mo \
    instant_translate/po/tr.po
```

Commit the `.pot`, `.po`, and compiled `.mo` files. Orca loads the `.mo` file at
runtime, and the source catalogs let translators maintain it.

## Pull requests

Before opening a pull request:

- Review the complete diff and remove unrelated changes.
- Run the automated checks.
- Complete the relevant manual tests in Orca.
- Explain what changed, why, and how it was manually verified.
- Mention known limitations and anything you could not test.

By contributing, you agree that your contribution is distributed under this
project's GNU General Public License, version 2 only. Preserve existing
copyright, SPDX, and attribution notices.

## For coding agents

Coding agents may inspect the repository, prepare draft code, run automated
checks, and write a draft pull-request description or manual-test plan. They
must not open, submit, or publish a pull request themselves.

An agent's work is always a draft for a human contributor. The agent must:

- Clearly summarize every changed file and any assumptions it made.
- Report the automated checks it actually ran without claiming they were
  manual tests.
- Give the human an exact manual-test checklist for the affected behavior.
- Call out privacy, accessibility, provider, and Orca API risks.
- Leave the final review, real Orca testing, and pull-request submission to the
  human.

A human contributor must inspect the draft, make any needed corrections,
perform the manual tests, and decide whether to open the pull request.
