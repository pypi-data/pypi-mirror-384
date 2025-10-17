# mkdocs-vwidref

A MkDocs plugin that lets you **link to pages by front-matter ID** with a compact wiki-style syntax and show **status / progress / title** inline.

- Title appears **only** when `:t` is present.  
- Status (`:s`) and Progress (`:p`) can be shown alone or together.  
- Parentheses / angle brackets appear **only** when multiple items are shown.  
- Links are emitted as **root-relative** URLs to avoid path concatenation issues and respect MkDocs’ `use_directory_urls` setting (`.html` links when disabled).

---

## 🧩 Installation

```bash
pip install mkdocs-vwidref
````

Enable in `mkdocs.yml`:

```yaml
plugins:
  - search
  - vwidref
```

Optional configuration (defaults shown):

```yaml
plugins:
  - vwidref:
      id_field: "id"
      title_field: "title"
      status_field: "status"
      progress_field: "progress"
      auto_status_field: "auto_status"
      auto_progress_1_field: "auto_progress_1"
      auto_progress_2_field: "auto_progress_2"
      append_hash: true
      lowercase_ids: false
      debug: false
      url_prefix: ""
```

* `append_hash`: append `#<id>` to the link.
* `lowercase_ids`: allow case-insensitive `[[id:...]]` lookup.
* `debug`: verbose transformation logs.
* `auto_status_field`: optional derived status (shown with `[[id:as:...]]`).
* `auto_progress_1_field` / `auto_progress_2_field`: optional derived progress bars (shown with `[[id:ap1:...]]` and `[[id:ap2:...]]`).
* Progress values below zero render as the empty bar (`:board-progempty:`) before rounding.
* `url_prefix`: prepend a fixed path or URL (for example `safety/`) to every generated link; leave blank for root-relative URLs.

---

### 2) Enable **custom emoji** rendering (Material for MkDocs)

```yaml
markdown_extensions:
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
      options:
        custom_icons:
          - overrides/.icons
```

> **Place your SVG icons** under `overrides/.icons/board/…` so the shortcodes below resolve.

---

## 🎨 Custom Emoji Shortcodes

The plugin outputs **shortcodes**, which the emoji extension renders to SVG.
Update your plugin’s **icon maps** (already set by default) to:

```python
PROGRESS_BARS = {
    -1:  ":board-progempty:",
    0:   ":board-progtodo:",
    20:  ":board-prog20:",
    40:  ":board-prog70:",
    60:  ":board-prog60:",
    80:  ":board-prog80:",
    100: ":board-progdone:",
}

STATUS_ICONS = {
    "todo": ":board-statustodo:",
    "inprogress": ":board-statusinprogress:",
    "done": ":board-statusdone:",
    "deprecated": ":board-statusdeprecated:",
}
```

### 📁 Icon file placement

With the `custom_icons` path set to `overrides/.icons`, the shortcode `:board-XYZ:` resolves to:

```
overrides/.icons/board/XYZ.svg
```

Required files for the map above:

```
overrides/.icons/
└─ board/
   ├─ progtodo.svg
   ├─ prog20.svg
   ├─ prog70.svg
   ├─ prog60.svg
   ├─ prog80.svg
   ├─ progdone.svg
   ├─ progempty.svg
   ├─ statustodo.svg
   ├─ statusinprogress.svg
   ├─ statusdeprecated.svg
   └─ statusdone.svg
```

> You can change filenames / shortcodes — just keep the **map** and **SVG names** in sync.

---

## 🧭 Authoring

**Target page front-matter:**

```yaml
---
id: tm-gp
title: Team – Gameplay
status: inprogress
progress: 63
auto_status: done
auto_progress_1: 80
auto_progress_2: 100
---
# Team – Gameplay
```

**Linking from another page:**

```md
[[id:tm-gp]]            → tm-gp
[[id:s:tm-gp]]          → 🔄
[[id:p:tm-gp]]          → 🟨🟨🟨⬛⬛      (63 → rounded to 60)
[[id:t:tm-gp]]          → Team – Gameplay
[[id:s:t:tm-gp]]        → (🔄) Team – Gameplay
[[id:p:t:tm-gp]]        → <🟨🟨🟨⬛⬛> Team – Gameplay
[[id:s:p:t:tm-gp]]      → (🔄) <🟨🟨🟨⬛⬛> Team – Gameplay
[[id:s:p:tm-gp]]        → (🔄) <🟨🟨🟨⬛⬛>   # no title without :t
[[id:as:tm-gp]]         → ✅
[[id:ap1:t:tm-gp]]      → <🟦🟦🟦🟦⬛> Team – Gameplay
[[id:t:test-id#architecture|Arch]]   → Arch   
```

!!! note "Custom labels"
A custom label (`[[id:s:t:tm-gp|Custom Label]]`) is used **only** when `:t` is present.
Without `:t`, any `|Label` is ignored (title is suppressed by design).

---

## 🔗 Linking to a specific section

You can link directly to a **section inside the target page** by appending a `#fragment` after the ID.

```md
[[id:t:test-id#section-id]]
```

* Finds the page whose front-matter includes `id: test-id`.
* Links to that page’s `#section-id`.
* Displays the title (or custom label) because `:t` is present.

---

## ⚙️ Flags Summary

| Flag | Meaning       | Output rule                                                                                      |
| ---- | ------------- | ------------------------------------------------------------------------------------------------ |
| `:s`  | Show status        | Show **status only** (no parentheses) if it’s the only item; wrap as **`(status)`** if combined. |
| `:as` | Show auto status   | Mirrors `:s`, but reads from `auto_status_field`.                                                 |
| `:p`  | Show progress      | Show **bar only** (no brackets) if it’s the only item; wrap as **`<bar>`** if combined.          |
| `:ap1`| Show auto progress | Mirrors `:p`, but reads from `auto_progress_1_field`.                                             |
| `:ap2`| Show auto progress | Mirrors `:p`, but reads from `auto_progress_2_field`.                                             |
| `:t`  | Show title         | Include **title** (or custom label). Title appears **only** when `:t` is present.                |

**Combinations**

* `[[id:s:foo]]` / `[[id:as:foo]]` → `⏳ / 🔄 / ✅`
* `[[id:p:foo]]`, `[[id:ap1:foo]]`, `[[id:ap2:foo]]` → one of `⬛⬛⬛⬛⬛`, `🟧🟧⬛⬛⬛`, `🟩🟩🟩🟩🟩`, etc.
* `[[id:s:t:foo]]` → `(⏳) Title`
* `[[id:p:t:foo]]` → `<🟧🟧⬛⬛⬛> Title`
* `[[id:as:ap1:t:foo]]` → `(🔄) <🟧🟧⬛⬛⬛> Title`
* `[[id:s:p:t:foo]]` → `(⏳) <🟧🟧⬛⬛⬛> Title`
* `[[id:s:p:foo]]` → `(⏳) <🟧🟧⬛⬛⬛>` (no title)
* `[[id:foo]]` → `foo` (raw id string)

---

## 🔢 Status & Progress Mapping

**Status → Icon**

| Status value | Icon |
| ------------ | ---- |
| `todo`       | ⏳    |
| `inprogress` | 🔄   |
| `done`       | ✅    |
| `deprecated` | 🗑️    |

**Progress → Bar**

Rounded to nearest 0 / 20 / 40 / 60 / 80 / 100 →

|   % | Bar        |
| --: | :--------- |
| <0  | (empty)    |
|   0 | ⬛⬛⬛⬛⬛      |
|  20 | 🟥⬛⬛⬛⬛     |
|  40 | 🟧🟧⬛⬛⬛    |
|  60 | 🟨🟨🟨⬛⬛   |
|  80 | 🟦🟦🟦🟦⬛  |
| 100 | 🟩🟩🟩🟩🟩 |

!!! tip
Missing components (no `status` or `progress`) are silently skipped.
If nothing remains, the plugin falls back to the raw `id`.

---

## 🔗 How It Links

* Links point to the **page containing the ID**, with optional `#<id>` anchor.
* Hrefs are **root-relative**, e.g.:

  ```
  /safe/01_volworld_portfolio/arts/art-gp_core-gameplay/art-gp/#art-gp
  ```

  This avoids concatenation with the current page’s path.

---

## 🩺 Troubleshooting

* **Wrong URL** → ensure you’re using `mkdocs-vwidref >= 1.0.0`.
* **No replacement** → confirm your target page’s front-matter starts at the file top and includes `id:`.
* **No title** → you must include `:t`.
* **Case sensitivity** → set `lowercase_ids: true` for case-insensitive matches.

---

## 🧾 Changelog

**1.0.0**

* Initial public release.
* Syntax `[[id:s|p|t:...]]` with progress rounding, status icons, and root-relative links.
* Emoji shortcode support for Material for MkDocs.

---

## 📜 License

MIT License © 2025 Gobidesert
