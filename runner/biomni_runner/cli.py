"""Entry point for cluster-side tool execution.

Called from Databricks notebooks with tool name and JSON parameters.
"""

import argparse
import json
import sys

from biomni_runner.file_tools import FILE_TOOLS
from biomni_runner.glow_tools import GLOW_TOOLS


ALL_TOOLS = {**GLOW_TOOLS, **FILE_TOOLS}


def main():
    parser = argparse.ArgumentParser(description="Biomni tool runner")
    parser.add_argument("tool", choices=list(ALL_TOOLS.keys()), help="Tool to execute")
    parser.add_argument("--params", required=True, help="JSON-encoded parameters")
    args = parser.parse_args()

    params = json.loads(args.params)
    tool_fn = ALL_TOOLS[args.tool]
    result = tool_fn(**params)
    print(result)


if __name__ == "__main__":
    main()
