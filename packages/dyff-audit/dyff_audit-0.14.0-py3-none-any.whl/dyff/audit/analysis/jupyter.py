# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import nbconvert
import nbformat

# mypy: disable-error-code="import-untyped"
from bs4 import BeautifulSoup

from dyff.audit.analysis.context import AnalysisContext
from dyff.schema.platform import MethodImplementationKind, MethodOutputKind


def _bs4_parse(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, features="lxml")


def run_jupyter_notebook() -> None:
    ctx = AnalysisContext()

    implementation = ctx.analysis.method.implementation
    if (
        implementation.kind != MethodImplementationKind.JupyterNotebook
        or implementation.jupyterNotebook is None
    ):
        raise ValueError("expected method.implementation as JupyterNotebook")
    output = ctx.analysis.method.output
    if output.kind != MethodOutputKind.SafetyCase or output.safetyCase is None:
        raise ValueError("expected method.output as SafetyCase")

    notebook_path = (
        ctx.local_storage_root
        / implementation.jupyterNotebook.notebookModule
        / implementation.jupyterNotebook.notebookPath
    )
    with open(str(notebook_path), "r") as fin:
        notebook = nbformat.read(fin, as_version=4)

    resources: dict = {}
    clear_output_preprocessor = nbconvert.preprocessors.ClearOutputPreprocessor()
    notebook, resources = clear_output_preprocessor.preprocess(notebook, resources)

    execute_preprocessor = nbconvert.preprocessors.ExecutePreprocessor()
    notebook, resources = execute_preprocessor.preprocess(notebook, resources)

    html_exporter = nbconvert.HTMLExporter(
        exclude_input=True, exclude_input_prompt=True, exclude_output_prompt=True
    )
    html_body, resources = html_exporter.from_notebook_node(notebook, resources)

    # Note: It is arguably cleaner to do this step in a custom Jupyter exporter,
    # but this way is much easier to distribute and it works fine as long as
    # the number of changes needed is minimal.
    soup = _bs4_parse(html_body)
    # Insert tailwind CSS in <head> by reference
    head = soup.find("head")
    tailwind_css = soup.new_tag(
        "script",
        src="https://cdn.tailwindcss.com",
    )
    body_style = _bs4_parse(
        """
        <style type="text/css">
            @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;700&display=swap');

            body {
                padding: 0 !important;
                margin: 0 !important;
            }

            main {
                padding: 0;
                display: grid;
                grid-template-columns: repeat(10, 1fr);
            }

            .jp-Cell {
                @media (width < 768px) {
                    grid-column: span 10 !important;
                }
                @media (768px <= width < 1000px) {
                    grid-column: 2 / span 8 !important;
                }
                @media (1000px <= width <= 1500px) {
                    grid-column: 3 / span 6 !important;
                }
                @media (1500px < width) {
                    grid-column: 4 / span 4 !important;
                }
            }

            .jp-Cell:has(.jp-all-columns) {
                grid-column: span 10 !important;
                padding: 0 !important;
            }

            .jp-RenderedHTML:not(:has(.jp-all-columns)) {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .jp-RenderedHTML {
                padding: 0 !important;
            }

            .jp-mod-noOutputs .jp-mod-noInput .jp-OutputArea-prompt .jp-InputArea-prompt {
                display: none !important;
            }

            :root {
                --jp-notebook-padding: 0;
                --jp-cell-padding: 10px;

                --jp-content-line-height: 1.6;
                --jp-content-font-scale-factor: 1.2
                --jp-content-font-size0: 1rem;
                --jp-content-font-size1: 1.125rem;
                --jp-content-font-size2: 1.25rem;
                --jp-content-font-size3: 1.5rem;
                --jp-content-font-size4: 2rem;
                --jp-content-font-size5: 3rem;


                --jp-ui-font-scale-factor: 1.2;
                --jp-ui-font-size0: 1rem;
                --jp-ui-font-size1: 1.125rem; /* Base font size */
                --jp-ui-font-size2: 1.25rem;
                --jp-ui-font-size3: 1.5rem;

                --jp-code-font-size: 1.125rem;
                --jp-code-line-height: 1.6;
                --jp-code-font-family-default: menlo, consolas, 'DejaVu Sans Mono', monospace;
                --jp-code-font-family: var(--jp-code-font-family-default);

                --jp-content-font-family: system-ui, -apple-system, blinkmacsystemfont,
                    'Segoe UI', helvetica, arial, sans-serif, 'Apple Color Emoji',
                    'Segoe UI Emoji', 'Segoe UI Symbol';
                --jp-ui-font-family: system-ui, -apple-system, blinkmacsystemfont, 'Segoe UI',
                    helvetica, arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji',
                    'Segoe UI Symbol';
            }
        </style>
        """
    )

    date_script = _bs4_parse(
        """
        <script type="text/javascript">
            window.onload = (_) => {
                const dateEl = document.querySelector("#date_berry");
                if (!dateEl) return;
                const isoDateStr = dateEl.innerHTML;
                let styledDateStr = isoDateStr;
                try {
                    const isoDateObj = new Date(isoDateStr);
                    styledDateStr = isoDateObj.toLocaleDateString();
                } catch (_) {
                    // Pass
                }
                dateEl.innerHTML = styledDateStr;
            };
        </script>
        """
    )
    head.append(tailwind_css)
    head.append(body_style)
    head.append(date_script)
    html_body = str(soup)

    ctx.output_path.mkdir(parents=True, exist_ok=True)
    with open(ctx.output_path / "index.html", "w") as fout:
        fout.write(html_body)
