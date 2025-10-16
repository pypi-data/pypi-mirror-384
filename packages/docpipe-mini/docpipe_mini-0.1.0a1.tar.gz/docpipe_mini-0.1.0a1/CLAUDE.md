# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview
**docpipe** – a *minimal-dependency*, **typed** document-to-jsonl serializer.
Goal: 5 MB install, 300 ms/MB, zero model, zero OCR, **just give AI clean text with coordinates**.

## Project Status
- **Phase**: early-dev / prototype
- **Version**: 0.1.0a1
- **Python**: 3.11+ locked
- **Package manager**: `uv`

## Architecture at a Glance
```
┌-------------┐     typed stream      ┌-------------┐     ┌-------------┐
│ Loader[MIME]│ ──── PageStream ────▶ │Processor[In,Out]│ ──▶ │ Formatter │ ──▶ IO[bytes]
└-------------┘  (lazy, ≤ max_mem)    └-------------┘     └-------------┘
```
- All stages speak **only** through strongly-typed streams (`src/docpipe/_types.py`).
- Generic `Processor[InT, OutT]` guarantees *static* type safety (`src/docpipe/_protocols.py`).
- Everything else is **plug-in**; core wheel **has zero third-party deps**.

## Typed Streams (summary)
| Stream      | Purpose                          | Key Fields |
|-------------|----------------------------------|------------|
| `PageStream` | 1 per page, carries width/height/dpi | `page_num`, `bbox`, `dpi` |
| `BlockStream` | text block with bbox & style | `text`, `bbox`, `font`, `size` |
| `TableStream` | table as list-of-rows | `data: list[list[str]]`, `bbox` |
| `ImageStream` | raw bytes + bbox | `bytes`, `bbox`, `ext` |

*Users can add custom streams by subclassing `TypedStream`.*

## Core Design Rules
1. **Zero-Dep Default** – core wheel only uses stdlib; heavy deps live in **extras**.
2. **Generic Processors** – `Processor[InT, OutT]` = callable + type inference; mypy strict passes.
3. **Lazy & Memory-Capped** – streams produced on-demand; `max_mem_mb` kills worker if RSS exceeded.
4. **JSONL Output** – every formatter can fall back to `{"doc_id": …, "type": …, "text": …}` so **any** pipeline ends with `cat *.jsonl | jq` ready data.
5. **Plugin > Inheritance** – new format? implement `Processor[PageStream, MyStream]` and register via entry-point; **no** deep subclass tree.

## Minimal User Journey
```bash
uv add docpipe-mini            # 5 MB download
python -m docpipe-mini paper.pdf > paper.jsonl
```
```python
import docpipe_mini as dp
for obj in dp.serialize("paper.pdf"):
    print(obj)                 # {"doc_id":"...","page":1,"bbox":[x,y,w,h],"type":"text","text":"..."}
```

## Dependencies
| Extra | Size | License | Note |
|-------|------|---------|------|
| *(none)* | 0 MB | PSF | **default**, stdlib only |
| `pdf` | +11 MB | AGPL | `pymupdf>=1.23` *optional* speed-up |
| `docx` | +3 MB | MIT | `python-docx>=0.8.11` *optional* |
| `xlsx` | +2 MB | MIT | `openpyxl>=3.1.0` *optional* |
| `image`| +3 MB | HPND | `Pillow>=10.0.0` *optional* |
| `dev` | +80 MB | mixed | pytest, mypy, pytest-benchmark |

## Development Setup
```bash
git clone <repo> && cd docpipe
uv sync --extra dev            # full env
uv sync                        # core only (zero dep)
pytest -m "not bench"          # fast tests
pytest -m bench                # large-file benchmarks (manual)
mypy --strict                  # must pass
```

## Directory Layout
```
src/docpipe/
├── __init__.py
├── _types.py          # TypedStream hierarchy
├── _protocols.py      # LoaderProto, Processor[In,Out], FormatterProto
├── _memory.py         # RSS guardrail (psutil + subprocess)
├── pipeline.py        # single entry `pipeline(src, *, loader, processor, fmt)`
├── loaders/
│   ├── _base.py
│   ├── _pdfium.py     # zero-dep PDF (default)
│   └── _pymupdf.py    # AGPL plugin (entry-point register)
├── formatters/
│   └── _jsonl.py      # default JSONL output
└── cli/
    └── _typer.py      # typer app (future)
```

## Known Gotchas (read before coding)
| Gotcha | Mitigation |
|--------|------------|
| **GPL/AGPL** | `pymupdf` is AGPL; keep it **optional** and provide BSD fallback (`pypdfium2`). |
| **Memory guardrail** | PyMuPDF/Pillow allocate outside Python; we run **loader in subprocess** + `psutil.RSS` kill switch. |
| **PDF reading order** | No layout model; we use pdfium text extraction order → **good-enough for GPT**, but **not** for human-typesetting. |
| **DOCX revision/track-changes** | stdlib parser **ignores** `<w:ins`, `<w:del`; if user needs it, tell them to use `python-docx` plugin. |
| **Test matrix** | Add any failing file to `tests/fixtures/` **without** fix; goal is **regression capture**, not perfection. |

## Implementation Roadmap (4-week sprint)
| Week | Deliverable | Note |
|------|-------------|------|
| W1 | `typed streams` + `Processor[In,Out]` + mypy strict | must compile |
| W2 | `pdfium` loader (zero dep) + `jsonl` formatter | 300 ms/MB target |
| W3 | `docx` + `xlsx` stdlib loaders + CLI `typer` | `cat file.xlsx | docpipe-seq` |
| W4 | plugins entry-points + `pymupdf` speed plugin + bench CI | publish `0.1.0a2` |

## Success Criteria for PR #1
- [ ] `PdfiumLoader` produces `PageStream → BlockStream` with bbox.
- [ ] `_jsonl.py` formatter writes **valid JSONL** ≤ 2× input size.
- [ ] `pytest -m "not bench"` passes + `mypy --strict` green.
- [ ] `uv build` wheel ≤ 1 MB (core).

---

Ready to code — start with `src/docpipe/loaders/_pdfium.py` and open PR #1.