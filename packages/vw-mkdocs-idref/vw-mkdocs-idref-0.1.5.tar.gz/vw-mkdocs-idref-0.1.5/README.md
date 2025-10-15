# vw-mkdocs-idref

Link to pages by **front-matter `id`** using wiki-style syntax, and show **status** / **progress** / **title** inline—using your own **custom emoji icons**.

* `[[id:tm-gp]]` → plain ID as link text
* `[[id:s:tm-gp]]` → **status** (no parentheses if status alone)
* `[[id:as:tm-gp]]` → **auto status** from `auto_status:`
* `[[id:p:tm-gp]]` → **progress** (no angle brackets if progress alone)
* `[[id:ap1:tm-gp]]` → **auto progress 1** from `auto_progress_1:`
* `[[id:ap2:tm-gp]]` → **auto progress 2** from `auto_progress_2:`
* `[[id:t:tm-gp]]` → **title**
* `[[id:s:t:tm-gp]]` → **(status) title**
* `[[id:p:t:tm-gp]]` → **<progress> title**
* `[[id:s:p:t:tm-gp]]` → **(status) <progress> title**
* `[[id:s:p:tm-gp]]` → **(status) <progress>** (no title unless `:t` is present)

> “Wrappers” appear **only when multiple components** are shown:
> status → `(… )` only when paired with progress or title;
> progress → `<…>` only when paired with status or title.

---

## ✨ What it does

* Resolves `[[id:some-id]]` to a link that points to the page whose **front-matter** contains `id: some-id`.
* Link `href` is root-relative and (optionally) includes `#some-id`.
* Link text is built from **flags** you include:

  * `s` → show **status icon** (from front-matter `status:`)
  * `as` → show **auto status icon** (from front-matter `auto_status:`)
  * `p` → show **progress bar** (from front-matter `progress:` rounded to 0/20/40/60/80/100)
  * `ap1` → show **auto progress bar 1** (from `auto_progress_1:` rounded as above)
  * `ap2` → show **auto progress bar 2** (from `auto_progress_2:` rounded as above)
  * `t` → show **title** (from front-matter `title:`; falls back to page H1 if missing)

---

## 📦 Installation

Local (editable) install while developing:

```bash
pip install -e .
```

Or from your private index (example):

```bash
pip install vw-mkdocs-idref --extra-index-url=https://<your-private-index>/
```

---

## ⚙️ Configuration (`mkdocs.yml`)

### 1) Enable the plugin

```yaml
plugins:
  - search
  - idref:
      id_field: "id"
      title_field: "title"
      status_field: "status"
      progress_field: "progress"
      append_hash: true        # adds #<id> to the link target
      lowercase_ids: false
      debug: false
```

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
}
```

Auto-derived fields (`auto_status`, `auto_progress_1`, `auto_progress_2`) reuse these same icon maps, so no extra configuration is required.

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
   ├─ statustodo.svg
   ├─ statusinprogress.svg
   └─ statusdone.svg
```

> You can change filenames/shortcodes—just keep the **map** and **SVG names** in sync.

---

## 📝 Front-matter example

```yaml
---
id: tm-gp
title: Team – Gameplay
status: inprogress
progress: 63
auto_status: done
auto_progress_1: 18
auto_progress_2: 92
---
```

> Progress values are rounded to **0/20/40/60/80/100** (63 → 60 → `:board-prog60:`, 18 → 20, 92 → 100).
> Status fields (`status`, `auto_status`) accept `todo`, `inprogress`, `done`.

---

## 🔗 Usage examples

Given the front-matter above:

| Markup               | Link text produced                                            |
| -------------------- | ------------------------------------------------------------- |
| `[[id:tm-gp]]`       | `tm-gp`                                                       |
| `[[id:s:tm-gp]]`     | `:board-statusinprogress:`                                    |
| `[[id:as:tm-gp]]`    | `:board-statusdone:`                                          |
| `[[id:p:tm-gp]]`     | `:board-prog60:`                                              |
| `[[id:ap1:tm-gp]]`   | `:board-prog20:`                                              |
| `[[id:ap2:tm-gp]]`   | `:board-progdone:`                                            |
| `[[id:t:tm-gp]]`     | `Team – Gameplay`                                             |
| `[[id:s:t:tm-gp]]`   | `(:board-statusinprogress:) Team – Gameplay`                  |
| `[[id:p:t:tm-gp]]`   | `<:board-prog60:> Team – Gameplay`                            |
| `[[id:s:p:t:tm-gp]]` | `(:board-statusinprogress:) <:board-prog60:> Team – Gameplay` |
| `[[id:s:p:tm-gp]]`   | `(:board-statusinprogress:) <:board-prog60:>`                 |
| `[[id:as:ap1:ap2:t:tm-gp]]` | `(:board-statusdone:) <:board-prog20:> <:board-progdone:> Team – Gameplay` |

> Actual pages will render the shortcodes as SVG icons.
> **Status gets parentheses** and **Progress gets angle brackets** **only** when combined with another component on the same line. Auto variants (`as`, `ap1`, `ap2`) follow the same rule.

### Custom label (when showing title)

If you include `:t`, you can override the title:

```
[[id:s:t:tm-gp|Gameplay Team]]
```

→ `(:board-statusinprogress:) Gameplay Team`

If you **don’t** include `:t`, custom labels are **ignored** (no title is shown).

---

## 🔧 Link targets

* Links are emitted **root-relative**, e.g.
  `/safe/01_volworld_portfolio/arts/art-gp_core-gameplay/art-gp/#tm-gp`
* `append_hash: true` adds `#<id>` so the browser scrolls to the page anchor.

---

## 🧪 Quick test

1. Put your SVGs in `overrides/.icons/board/…`
2. Enable `pymdownx.emoji` as shown above
3. Add a test page with `id/status/progress/title` in front-matter
4. Use `[[id:…]]` links from another page
5. Run:

   ```bash
   mkdocs serve -v
   ```

   and verify the rendered icons/text and link targets

---

## 🛠 Troubleshooting

* **Shortcodes show as text**
  → Check `markdown_extensions.pymdownx.emoji` config and that your SVGs exist at the expected paths.

* **Link path repeats current page segments**
  → This plugin emits **root-relative** links; ensure you’re using the latest version.

* **No output / unresolved id**
  → The target page must have front-matter with `id: <value>`. Run with `-v` to see `[idref]` warnings.

---

## 📄 License

MIT (or your preferred license)

---

## 🤝 Contributing

PRs welcome!
Ideas: per-project icon maps, extra statuses, or a combined **interwiki+idref** plugin so `[[id:…]]` and `[[wiki:…]]` both work.
