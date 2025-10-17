# Author: Swati Swati (swati17293@gmail.com, swati.swati@unibw.de)

import pandas as pd
import numpy as np
import fairlearn
from fairlearn.metrics import *

import plotly.graph_objs as go
import plotly.io as pio

from rich.console import Console
console = Console()

import webbrowser
import tempfile
import os

import textwrap

def wrap_label(lbl, width):
    # Always treat lbl as a string
    text = str(lbl)
    return "\n".join(textwrap.wrap(text, width))


def render_html(html_content, filename="fairness_report.html"):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as f:
        f.write(html_content)
        file_path = f.name
    webbrowser.open("file://" + os.path.realpath(file_path))

def explaination_text():
    explanation_html = """ 
    <div class="explanation" style="margin-top: 10px; align: center">
        <h3 style="color: #2e1065;">Fairness Report Summary</h3>

        <p><strong>🧭 What this report tells:</strong><br>
        This fairness report compares how the machine learning model performs across different groups defined by sensitive attributes (like sex or race). It shows whether the model treats those groups equally.</p>

        <p><strong>📊 What to look at:</strong></p>

        <p><strong>1. Group-wise Fairness Metrics</strong><br>
        These tell how the model behaves per group (e.g. males vs females). For example:</p>
        <ul>
            <li><b>selection_rate</b>: how often the model predicts a positive outcome.</li>
            <li><b>true_positive_rate</b>: how well it catches positives correctly.</li>
            <li><b>false_positive_rate</b>: how often it wrongly labels negatives as positives.</li>
            <li><b>true_negative_rate</b>: how well it correctly identifies negative cases.</li>
            <li><b>false_negative_rate</b>: how often it misses actual positives.</li>
        </ul>
        <p>Good fairness means these values are <strong>similar across groups</strong>.</p>

        <p><strong>2. Scalar Fairness Metrics</strong></p>
        <p><strong>Key fairness definitions:</strong></p>
        <ul>
            <li><b>demographic_parity</b>: The model should give positive predictions equally to all groups, regardless of whether the outcome is correct.
                <br><i>Use when equal access to the outcome (e.g., a loan offer) is most important.</i></li>

            <li><b>equal_opportunity</b>: The model should correctly identify positives (true positives) equally across groups.
                <br><i>Use when missing a qualified candidate matters, e.g., job hiring, medical diagnosis.</i></li>

            <li><b>equalized_odds</b>: The model should balance both true positives and false positives across groups.
                <br><i>Use when fairness in both success and failure rates is important, e.g., parole decisions.</i></li>
        </ul>

        <p>These give summary differences between groups:</p>
        <ul>
            <li>If differences are smaller (closer to 0) → better (more equal treatment).</li>
            <li>If ratios are closer to 1 → better (balanced performance across groups).</li>
        </ul>

        <p><strong>✅ What’s a “fair” value?</strong></p>
        <ul>
            <li>Differences close to <strong>0.00</strong> = fair.</li>
            <li>Ratios close to <strong>1.00</strong> = fair.</li>
        </ul>
        <p>Generally, difference &gt; <strong>0.1</strong> or ratio &lt; <strong>0.8</strong> may indicate bias.</p>

        <p><strong>📚 Learn more:</strong><br>
        See the official Fairlearn documentation here:<br>
        <a href="https://fairlearn.org/main/user_guide/assessment/index.html" target="_blank">
            https://fairlearn.org/main/user_guide/assessment/index.html
        </a>
        </p>
    </div>
    """

    return explanation_html




def show_fairlearn_report(by_group, scalar_metrics, group_map=None):
    out = ""

    out += "\n[bold blue]>>> Group-wise[/] [blue]Fairness Metrics <<<[/]\n\n"

    df = by_group.copy().T
    df = df.reset_index()
    df.rename(columns={'index': 'Metric'}, inplace=True)

    if group_map is None:
        group_map = {}

    df.columns = ["Metric"] + [wrap_label(group_map.get(col, col), col_widths[i])for i, col in enumerate(df.columns[1:], start=1)]

    # Set widths to match formatter
    col_widths = [22] + [10] * (df.shape[1] - 1)

    # Format header manually
    header = "".join(f"{col:<{w}}" if i == 0 else f"{col:>{w}}" 
                    for i, (col, w) in enumerate(zip(df.columns, col_widths)))

    # Format each row using your formatters
    rows = []
    for _, row in df.iterrows():
        line = ""
        for i, (val, w) in enumerate(zip(row, col_widths)):
            if i == 0:
                line += f"{str(val):<{w}}"  # left-align Metric
            else:
                line += f"{val:>{w}.6f}"    # right-align values
        rows.append(line)

    # Combine lines
    lines = [header, "-" * len(header)] + rows
    out += "\n".join(lines) + "\n"
    out += "-" * 42 + "\n"

    out += "\n[bold blue]>>> Scalar[/] [blue]Fairness Metrics <<<[/]\n\n"
    out += f"{'Metric'.ljust(30)} {'Value'}\n"
    out += "-" * 39 + "\n"
    for metric, value in scalar_metrics.items():
        out += f"{metric.ljust(30)} {value:.6f}\n"
    out += "-" * 39 + "\n\n"

    return out

def generate_reports_from_fairlearn(
    report_type, sensitives, mmm_classifier, saIndex_test, y_pred, y_test, launch_browser=True, group_mappings=None
):
    report_type = report_type.lower()
    if report_type not in {"console", "table", "html"}:
        raise ValueError("report_type must be 'console', 'table' or 'html'.")

    out = ""
    out += "\n" + "=" * 67 + "\n"
    html_sections = []
    html_blocks = []
    plot_sections = []

    explanation_html = explaination_text()

    for i, attr in enumerate(sensitives):
        sensitive_column = saIndex_test[:, i]

        # Invert group mapping so you can label 0 → "fitz12", 1 → "fitz34", etc.
        group_map = {}
        if group_mappings and attr in group_mappings:
            group_map = {v: k for k, v in group_mappings[attr].items()}

        metric_frame = MetricFrame(
            metrics={
                "selection_rate": selection_rate,
                "true_positive_rate": true_positive_rate,
                "false_positive_rate": false_positive_rate,
                "true_negative_rate": true_negative_rate,
                "false_negative_rate": false_negative_rate,
            },
            y_true=y_test,
            y_pred=y_pred,
            sensitive_features=sensitive_column
        )

        scalar_metrics = {
            "demographic_parity_difference": demographic_parity_difference(y_test, y_pred, sensitive_features=sensitive_column),
            "demographic_parity_ratio": demographic_parity_ratio(y_test, y_pred, sensitive_features=sensitive_column),
            "equal_opportunity_difference": equal_opportunity_difference(y_test, y_pred, sensitive_features=sensitive_column),
            "equal_opportunity_ratio": equal_opportunity_ratio(y_test, y_pred, sensitive_features=sensitive_column),
            "equalized_odds_difference": equalized_odds_difference(y_test, y_pred, sensitive_features=sensitive_column),
            "equalized_odds_ratio": equalized_odds_ratio(y_test, y_pred, sensitive_features=sensitive_column),
        }

        if report_type == "console":
            out += f"[bold magenta]=== Fairness Report for the Protected Attribute: {attr} ===[/]\n"
            out += "=" * 67 + "\n"
            out += show_fairlearn_report(
                by_group=metric_frame.by_group,
                scalar_metrics=scalar_metrics,
                group_map=group_map
            )

            out += "=" * 67 + "\n"

        elif report_type == "table":
            # Prepare DataFrame
            df = metric_frame.by_group.copy().T.reset_index()
            df.rename(columns={'index': 'Metric'}, inplace=True)

            # Compute widths
            #    - Metric column grows to fit its longest name + 2 spaces
            first_col = df.columns[0]
            first_width = max(df[first_col].astype(str).map(len).max(), len(first_col)) + 2
            #    - All group/value columns fixed to len("0.904255") + 2 = 10
            numeric_width = len(f"{0.904255:.6f}") + 2  # → 10
            col_widths = [first_width] + [numeric_width] * (df.shape[1] - 1)

            # Wrap each group label into ≤2 lines
            raw_labels = [group_map.get(col, col) for col in df.columns[1:]]
            wrapped = [wrap_label(lbl, numeric_width) for lbl in raw_labels]
            split_lbls = [lbl.split("\n") for lbl in wrapped]
            max_lines = max(len(lines) for lines in split_lbls)
            for lines in split_lbls:
                lines += [""] * (max_lines - len(lines))

            # Build header‐block (multi‐line), **no leading blank** before each group col
            header_lines = []
            for line_idx in range(max_lines):
                # Start with the Metric header cell (blank for header)
                line = f"{'Metric':<{first_width}}" if line_idx == 0 else " " * first_width
                # Then each group header line, left‐aligned in its numeric column
                for col_idx in range(len(split_lbls)):
                    line += f"{split_lbls[col_idx][line_idx]:<{numeric_width}}"
                header_lines.append(line)

            # Separator under header
            sep = "─" * (first_width + numeric_width * len(split_lbls))

            # Build data rows using exact same widths
            data_rows = []
            for _, row in df.iterrows():
                line = f"{str(row.iloc[0]):<{first_width}}"
                for val in row.iloc[1:]:
                    line += f"{val:<{numeric_width}.6f}"
                data_rows.append(line)

            # Assemble group_block
            group_block = "\n".join(header_lines + [sep] + data_rows + [sep])

            # Scalar metrics (left-aligned under Metric col)
            scalar_lines = []
            scalar_header = f"{'Metric':<{first_width}} {'Value'}"
            scalar_sep    = "─" * (first_width + 1 + numeric_width)
            # scalar_lines.append(scalar_header)
            # scalar_lines.append(scalar_sep)
            for metric, value in scalar_metrics.items():
                scalar_lines.append(f"{metric:<{first_width}}: {value:.6f}")
            # scalar_lines.append(scalar_sep)
            scalar_block = "\n".join(scalar_lines)

            html_section = f"""
            <div style="font-family: monospace; font-size: 14px; margin-top: 10px; margin-left: 25px;">
                <div style="color: #2e1065; font-weight: bold;">
                    <div style="white-space: pre; overflow: hidden; text-overflow: ellipsis;">{"═" * 53}<br></div>
                        <span style="margin-left: 47px;">*** Protected Attribute: {attr} ***</span><br>
                    <div style="white-space: pre; overflow: hidden; text-overflow: ellipsis;">{"═" * 53}</div>
                </div>

                <div style="color: #2e1065; margin-left: 50px;">

                    <div style="color: #1e40af; font-weight: bold; margin-top: 10px;">>>> Group-wise Fairness Metrics <<<</div>
                    <pre style="color: #333;">{group_block}</pre>

                    <div style="color: #1e40af; font-weight: bold; margin-top: 10px;">>>> Scalar Fairness Metrics <<<</div>
                    <pre style="color: #333;">{scalar_block}</pre>
                </div>
            </div>
            """
            html_blocks.append(html_section)

        elif report_type == "html":

            # --- 1. Group-wise Fairness Metrics (Grouped Bar Chart) ---
            group_fig = go.Figure()

            # Transpose so rows = metrics, columns = groups
            group_data = metric_frame.by_group.T

            metrics = group_data.index.tolist()      # ['selection_rate', ...]
            groups = group_data.columns.tolist()     # [0, 1] (or 'Male', 'Female')

            # Plot one bar per group, per metric
            for group in groups:
                values = group_data[group].tolist()
                group_fig.add_trace(go.Bar(
                    name=f"{group_map.get(group, group)}",
                    y=metrics,        # metrics on Y-axis
                    x=values,         # values for this group
                    orientation='h',
                    text=[f"{v:.3f}" for v in values],
                    textposition='auto'
                ))

            group_fig.update_layout(
                colorway=pio.templates["plotly"].layout.colorway,  # use default palette
                barmode='group',
                title=f"Group-wise Fairness Metrics",
                xaxis_title="Value",
                yaxis_title="Metric",
                legend_title="Group",
                template="simple_white",
                height=300 + 25 * len(metrics),  
                bargap=0.2,                      
                bargroupgap=0.05                
            )

            group_plot_html = pio.to_html(group_fig, include_plotlyjs=False, full_html=False)

            # --- 2. Scalar Fairness Metrics (Simple Bar Chart) ---
            scalar_names = list(scalar_metrics.keys())
            scalar_values = list(scalar_metrics.values())

            scalar_fig = go.Figure(data=[
                go.Bar(
                    y=scalar_names,                       # Metrics on Y-axis
                    x=scalar_values,                      # Values on X-axis
                    orientation='h',
                    marker_color="#6366f1",
                    text=[f"{v:.3f}" for v in scalar_values],
                    textposition='auto'
                )
            ])

            scalar_fig.update_layout(
                colorway=pio.templates["plotly"].layout.colorway,  # use default palette
                title=f"Scalar Fairness Metrics",
                xaxis_title="Value",
                yaxis_title="Metric",
                template="simple_white",
                height=300 + 7 * len(scalar_names),  # Adjust height based on number of metrics
                bargap=0.2
            )

            scalar_plot_html = pio.to_html(scalar_fig, include_plotlyjs=False, full_html=False)


            # Combine both charts into one section
            plot_html = f"""
            <div style="font-family: monospace; font-size: 14px; margin-top: 10px; margin-left: 25px;">
                <div style="color: #2e1065; font-weight: bold;">
                    <div style="white-space: pre; overflow: hidden; text-overflow: ellipsis;">{"═" * 53}<br></div>
                        <span style="margin-left: 70px;">*** Protected Attribute: {attr} ***</span><br>
                    <div style="white-space: pre; overflow: hidden; text-overflow: ellipsis;">{"═" * 53}</div>
                </div>

                <div style="color: #2e1065; margin-left: 0px; margin-top: -60px; margin-bottom: -70px;">
                    <pre style="color: #333;">
                        {group_plot_html}
                    </pre>
                    <pre style="color: #333; margin-top: -130px;">
                        {scalar_plot_html}
                    </pre>
                </div>
            </div>
            """

            plot_sections.append(plot_html)

    if report_type == "console":
        console.print(out)
        return out

    elif report_type == "table":
        htmltext = f"""
        <html>
            <head>
                <meta charset="utf-8">
                <title>Report</title>
                <style>
                    body {{
                        font-family: monospace;
                        font-size: 14px;
                        margin: 40px;
                    }}
                    .container {{
                        display: flex;
                        gap: 40px;
                        align-items: flex-start;
                    }}
                    .report {{
                        flex: 2;
                        padding: 20px;
                        font-family: Arial, sans-serif;
                        font-size: 13px;
                        color: #333;
                        line-height: 1.6;
                        max-width: 500px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    }}
                    .explanation {{
                        flex: none;
                        background-color: #f0f4ff;
                        padding: 20px;
                        border-radius: 8px;
                        font-family: Arial, sans-serif;
                        font-size: 13px;
                        color: #333;
                        line-height: 1.6;
                        max-width: 460px;
                        margin-left: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="report" style="width: 50%; overflow-x: auto; white-space: nowrap;">
                        <div style="color: #2e1065; font-weight: bold; margin-left: 80px;" margin-right: 20px;">
                            <h1>Fairness Report</h1>
                        </div>
                        {''.join(html_blocks)}
                        <div style="color: #2e1065; font-weight: bold; margin-left: 25px;">
                            <div style="white-space: pre; overflow: hidden; text-overflow: ellipsis;">{"═" * 48}<br></div>
                        </div>
                    </div>
                    <div class="explanation" style="width: 50%; padding-left: 20px; overflow-x: auto; word-break: break-all;">
                        {explanation_html}
                    </div>
                </div>
            </body>
        </html>
        """
        if launch_browser:
            render_html(htmltext)  
        print("HTML report rendered.")
        return htmltext 

    elif report_type == "html":
        plot_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Plot Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: monospace;
                    font-size: 14px;
                    margin: 40px;
                }}
                .container {{
                    display: flex;
                    gap: 40px;
                    align-items: flex-start;
                }}
                .report {{
                    flex: 2;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                    font-size: 13px;
                    color: #333;
                    line-height: 1.6;
                    max-width: 500px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }}
                .explanation {{
                    flex: none;
                    background-color: #f0f4ff;
                    padding: 20px;
                    border-radius: 8px;
                    font-family: Arial, sans-serif;
                    font-size: 13px;
                    color: #333;
                    line-height: 1.6;
                    max-width: 460px;
                    margin-left: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="report">
                    <div style="color: #2e1065; font-weight: bold; margin-left: 45px;">
                        <h1>Fairness Report: Plots</h1>
                    </div>
                    {"".join(plot_sections)}
                    <div style="color: #2e1065; font-weight: bold; margin-left: 25px;">
                        <div style="white-space: pre; overflow: hidden; text-overflow: ellipsis;">{"═" * 48}<br></div>
                    </div>
                </div>
                <div class="explanation">
                    {explanation_html}
                </div>
            </div>
        </body>
        </html>
        """
        if launch_browser:
            render_html(plot_html)
        print("Fairness Plot Report rendered.")
        return plot_html

    return ""
