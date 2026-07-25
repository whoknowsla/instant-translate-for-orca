# Instant Translate for Orca

Instant Translate adds quick translation commands to the
[Orca screen reader](https://help.gnome.org/users/orca/stable/). Select text,
press a shortcut, and hear the translation through Orca. You can also translate
clipboard text, identify a language, and quickly swap the source and target
languages.

The extension supports:

- Google Translate without an account.
- Yandex Translate without an account.
- DeepL with your own API key.
- A Turkish interface for settings, commands, messages, errors, and language
  names.

Network work runs in the background, so Orca remains responsive while a
translation is in progress.

## Before you install

Instant Translate sends the text you ask it to translate to the selected
provider. Do not use it for passwords, tokens, confidential documents, or other
sensitive text unless you trust that provider.

Google and Yandex use unofficial endpoints that can change or stop working.
DeepL uses its official API and may consume quota or incur costs under your
DeepL plan.

## Requirements

- Linux with a recent Orca release that supports user extensions.
- Python 3.11 or newer.
- PyGObject with GTK 3 and AT-SPI 2.
- Internet access.
- GNOME Secret Service/libsecret if you want to use DeepL.

## Install

Download or clone this repository, open a terminal in its folder, and run:

```bash
mkdir -p ~/.local/share/orca/extensions/instant_translate
cp -r instant_translate/. ~/.local/share/orca/extensions/instant_translate/
orca --approve-extension instant_translate
```

You can also approve it from **Orca Preferences → User Extensions**. Restart
Orca after installing.

Orca protects users by hashing approved extensions. After every update, copy
the files again and re-approve the extension before restarting Orca.

## Use

`Orca` below means your configured Orca modifier key.

| Shortcut | Action |
| --- | --- |
| `Orca+Alt+X` | Translate selected text |
| `Orca+Alt+C` | Translate clipboard text |
| `Orca+Alt+I` | Identify the selected text's language |
| `Orca+Alt+S` | Swap the source and target languages |
| `Orca+Alt+A` | Announce the current languages |

If an application does not expose its selection to accessibility tools, copy
the text and use the clipboard command instead.

## Configure

Open **Orca Preferences → User Extensions → Instant Translate → Settings**.

Choose Google, Yandex, or DeepL, then select the source and target languages.
The source can be set to **Auto-detect**. Each provider remembers its own
language choices.

After changing the translation engine, apply the setting and reopen the
extension settings to see that engine's options.

Other options let you:

- Copy successful translations to the clipboard.
- Replace underscores with spaces before translating.
- Cache repeated translations in memory for the current Orca session.
- Use Google's optional third-party mirror.
- Limit the size of Yandex and DeepL requests.

Clipboard output is best effort because desktop security rules, especially on
Wayland, can prevent Orca from keeping text on the clipboard.

### DeepL

Select the Free or Pro plan and enter your API key. On the next DeepL request,
the extension removes the key from Orca's normal settings and stores it in the
desktop keyring.

Orca currently shows extension text settings as visible fields, so protect the
screen while entering a key. If the keyring is unavailable, the current request
can use the key, but it will not be saved.

## Turkish interface

Orca loads the Turkish catalog automatically when the desktop language is
Turkish. The interface language does not restrict translation languages; you
can still translate between any languages offered by the active provider.

After changing a catalog, remember to copy and re-approve the whole package.
Catalog files are part of Orca's extension approval hash.

## Troubleshooting

- **Orca says “No selection.”** The application may not expose selected text
  through AT-SPI. Copy it and use `Orca+Alt+C`.
- **New engine settings are missing.** Apply the engine choice, close the
  settings dialog, and reopen it.
- **The extension disappeared after an update.** Re-approve it because its
  package hash changed.
- **Google or Yandex stopped working.** Their unofficial endpoints may be
  unavailable or rate-limited. Try again later or choose another provider.
- **DeepL rejects the key.** Check the key and make sure the selected Free or
  Pro plan matches your account.

## Contributing

Everyone is welcome to contribute, including people who use AI-assisted or
“vibe coding” workflows. Every change must still be manually tested in Orca by
a human before a pull request is opened. See [CONTRIBUTING.md](CONTRIBUTING.md)
for the checklist and the special rules for coding agents.

## License and attribution

Instant Translate for Orca is licensed under the GNU General Public License,
version 2 only. See [LICENSE](LICENSE).

The project is based on the NVDA
[Instant Translate](https://github.com/nvdaaddons/instantTranslate) add-on.
Yandex-related language data and request behavior include work adapted from
[YandexTranslate for NVDA](https://github.com/alekssamos/YandexTranslate). See
[NOTICE](NOTICE) for attribution.
