# Copyright 2025 MOSTLY AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import tempfile

import pandas as pd
from fastmcp import Context, FastMCP

from mostlyai.mock.core import _asample

SAMPLE_MOCK_TOOL_DESCRIPTION = f"""
Synthetic Mock Data.

Use LLMs to generate any Tabular Data towards your needs. Create from scratch, expand existing datasets, or enrich tables with new columns.

This tool is a proxy to the `mostlyai.mock.core._asample` function, but returns a dictionary of paths to the generated CSV files.

Present the result nicely to the user, in Markdown format. Example:

Mock data can be found under the following paths:
- `/tmp/tmpl41bwa6n/players.csv`
- `/tmp/tmpl41bwa6n/seasons.csv`

== mostlyai.mock.core._asample docstring ==
{_asample.__doc__}
"""

mcp = FastMCP(name="MostlyAI Mock MCP Server")


def _store_locally(data: dict[str, pd.DataFrame]) -> dict[str, str]:
    temp_dir = tempfile.mkdtemp()
    locations = {}
    for table_name, df in data.items():
        csv_path = os.path.join(temp_dir, f"{table_name}.csv")
        df.to_csv(csv_path, index=False)
        locations[table_name] = csv_path
    return locations


@mcp.tool(description=SAMPLE_MOCK_TOOL_DESCRIPTION)
async def mock_data(
    ctx: Context,
    *,
    tables: dict[str, dict],
    sample_size: int,
    model: str = "openai/gpt-5-nano",
    api_key: str | None = None,
    temperature: float = 1.0,
    top_p: float = 0.95,
) -> dict[str, str]:
    data = await _asample(
        tables=tables,
        sample_size=sample_size,
        model=model,
        api_key=api_key,
        temperature=temperature,
        top_p=top_p,
        return_type="dict",
        progress_callback=ctx.report_progress,
    )
    locations = _store_locally(data)
    return locations


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
