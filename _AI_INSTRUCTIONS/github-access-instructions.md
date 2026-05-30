# GitHub Access Instructions for ChatGPT

Primary repository:

`Satobloc/SAT_THEORY_ARCHIVE_2023-25`

These notes document the practical GitHub access pathway established during testing, including the earlier public-web limitations, path-reconstruction workarounds, and the working GitHub connector + PDF extraction workflow.

---

## 1. Prefer the GitHub connector when available

Use the GitHub connector first, not ordinary web browsing, when accessing Nathan's GitHub repositories.

Recommended connector pattern:

1. Confirm repository access with `GitHub.get_repo` or `GitHub.list_repositories` if needed.
2. For plaintext, code, Markdown, JSON, YAML, CSV, LaTeX, and similar text-based files, use `GitHub.fetch_file` with `encoding="utf-8"`.
3. For known paths, fetch directly by repository path rather than searching the public web.
4. For discovery, use `GitHub.search` with:

   `repository_name="Satobloc/SAT_THEORY_ARCHIVE_2023-25"`

5. Treat connector write access cautiously. Read by default. Write only when Nathan explicitly asks or when performing the established PDF extraction-request workflow.

---

## 2. Public web access versus connector access

Before the GitHub connector became available, public web access was tested extensively. The result was a useful but limited fallback map.

Public GitHub web pages can sometimes be read as ordinary web pages, but this is not the same as true repository access.

Observed public-web behavior:

- GitHub repository root and folder pages can expose directory listings through `/tree/main/...` URLs.
- GitHub file pages using `/blob/main/...` expose HTML wrapper pages, not always raw file contents.
- Raw plaintext files can usually be read through `raw.githubusercontent.com`.
- GitHub-hosted PDFs generally cannot be extracted through ordinary public-web access in this chat environment.
- GitHub PDF preview pages, including `viewscreen.githubusercontent.com`, expose a viewer shell rather than extractable PDF text.
- `github.dev` URLs open the web editor shell and are not useful for content extraction.

The public-web fallback is useful mainly for public text files and directory navigation, not PDFs or other binary documents.

---

## 3. Public-web path reconstruction fallback

If the GitHub connector is unavailable but public web access works, folder and text-file access may still be possible by reconstructing URLs.

Folder-page pattern:

```text
https://github.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/tree/main/<URL-ENCODED-FOLDER-PATH>
```

Example:

```text
https://github.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/tree/main/000%20Earliest%20SAT_RMS
```

Blob-file pattern:

```text
https://github.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/blob/main/<URL-ENCODED-FILE-PATH>
```

Raw-text pattern:

```text
https://raw.githubusercontent.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/main/<URL-ENCODED-FILE-PATH>
```

For older or permalinked commits:

```text
https://raw.githubusercontent.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/<COMMIT-SHA>/<URL-ENCODED-FILE-PATH>
```

Examples:

```text
https://raw.githubusercontent.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/main/PARADIGM%20SHIFT.txt
```

```text
https://raw.githubusercontent.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/main/Towards%20the%20Holy%20Grail.txt
```

This worked for `.txt`, `.md`, source-code files, extensionless text files such as `LICENSE`, and other text-like repository files.

---

## 4. Why PDF access failed through public web URLs

The earlier PDF problem was not simply a bad URL. Several URL forms were tested:

- GitHub blob URLs, e.g. `github.com/.../blob/main/file.pdf`
- Raw GitHub URLs, e.g. `raw.githubusercontent.com/.../file.pdf`
- GitHub raw download URLs, e.g. `github.com/.../raw/.../file.pdf`
- GitHub web-editor URLs, e.g. `github.dev/...`
- GitHub PDF preview/viewer URLs, e.g. `viewscreen.githubusercontent.com/view/pdf?...`

These exposed metadata, raw binary payloads, or viewer shells, but not reliably accessible extracted text.

The core distinction:

1. Text files arrive as text and can be read directly.
2. PDF files arrive as binary data and require a PDF parser.
3. GitHub's browser PDF viewer renders visually, usually through client-side JavaScript/canvas/image layers, not through a simple server-side plaintext endpoint.
4. In this chat environment, ordinary public-web retrieval could not bridge from GitHub-hosted PDF bytes to extracted text.

This is why path tricks helped for `.txt` files but not for PDFs.

---

## 5. PDF access problem and its resolution

Direct PDF access has two separate layers:

1. Permission/access to the repository file.
2. Extraction of readable text from binary PDF content.

The GitHub connector can fetch PDF file bytes as base64. However, large base64 responses may be truncated before the file can be reconstructed locally inside the chat. Therefore, do not rely on direct PDF parsing from `GitHub.fetch_file` for ordinary work.

The established solution is an on-demand GitHub Actions PDF extraction bridge.

---

## 6. Installed PDF extraction workflow

Workflow file:

```text
.github/workflows/extract-pdf-text.yml
```

Trigger/request file:

```text
_AI_REQUESTS/pdf_extract_request.json
```

Generated text folder:

```text
_AUTO_EXTRACTED_TEXT/
```

The workflow watches changes to `_AI_REQUESTS/pdf_extract_request.json`. When the request file is created or updated, GitHub Actions checks out the repository, uses PyMuPDF to extract text from the requested PDF, and commits a `.txt` version into `_AUTO_EXTRACTED_TEXT/`.

The workflow extracts only the requested PDF. It does not bulk-convert the archive.

The workflow creates the output directory automatically. The `_AUTO_EXTRACTED_TEXT/` folder does not need to exist beforehand.

---

## 7. How to request PDF extraction

To request a PDF extraction:

1. Fetch `_AI_REQUESTS/pdf_extract_request.json` to get its current SHA.
2. Update it using `GitHub.update_file`.
3. Use JSON of this form:

```json
{
  "pdf_path": "PATH/TO/FILE.pdf",
  "requested_by": "ChatGPT",
  "request_id": "unique timestamp or descriptive id"
}
```

Suggested commit message:

```text
Request PDF text extraction for PATH/TO/FILE.pdf
```

After GitHub Actions runs, fetch the corresponding output file:

```text
_AUTO_EXTRACTED_TEXT/PATH/TO/FILE.txt
```

Root-level example:

PDF:

```text
PROTO_RESUME.pdf
```

Generated output:

```text
_AUTO_EXTRACTED_TEXT/PROTO_RESUME.txt
```

Folder example:

PDF:

```text
SAT O Core Modules/example.pdf
```

Generated output:

```text
_AUTO_EXTRACTED_TEXT/SAT O Core Modules/example.txt
```

---

## 8. Verified test result

The workflow was tested with:

```text
PROTO_RESUME.pdf
```

It generated:

```text
_AUTO_EXTRACTED_TEXT/PROTO_RESUME.txt
```

The generated text file reported:

- Source PDF: `PROTO_RESUME.pdf`
- Extraction engine: PyMuPDF
- Pages: 1
- Characters extracted: 1086

This verified the full loop:

```text
ChatGPT updates request JSON
→ GitHub Action runs
→ PDF text is generated and committed
→ ChatGPT reads generated TXT through the GitHub connector
```

---

## 9. Do not confuse these paths

Use these distinctions:

- `github.com/.../tree/...` = folder listing HTML
- `github.com/.../blob/...` = GitHub HTML wrapper for a file
- `raw.githubusercontent.com/...` = raw file payload, good for text files
- `github.dev/...` = browser editor shell, not useful for extraction
- `viewscreen.githubusercontent.com/view/pdf?...` = GitHub PDF viewer shell, not useful for text extraction
- GitHub connector `fetch_file` = preferred repo-native access
- GitHub Actions extraction workflow = preferred PDF-to-text bridge

---

## 10. Operational cautions

- Do not modify repository files unless Nathan explicitly asks or the change is part of the PDF extraction request workflow.
- Do not bulk-convert all PDFs unless specifically requested.
- Prefer on-demand extraction.
- If a PDF extraction output already exists in `_AUTO_EXTRACTED_TEXT/`, fetch and use it before triggering a new extraction unless Nathan asks for a fresh run.
- If the extraction returns very little text, the PDF may be scanned, image-based, or otherwise lacking a usable embedded text layer. Consider adding OCR fallback to the workflow if needed.
