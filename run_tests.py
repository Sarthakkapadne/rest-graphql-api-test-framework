#!/usr/bin/env python3
"""
CLI Test Runner & Target Server Launcher for REST & GraphQL API Test Framework.
"""
import argparse
import subprocess
import sys
import os


def main():
    parser = argparse.ArgumentParser(description="REST & GraphQL Test Runner & Server Launcher")
    parser.add_argument(
        "--mode",
        choices=["test", "server"],
        default="test",
        help="Run pytest automation suite ('test') or start FastAPI/GraphQL dev server ('server')",
    )
    parser.add_argument(
        "--protocol",
        choices=["all", "rest", "graphql"],
        default="all",
        help="Filter tests by API protocol",
    )
    parser.add_argument(
        "--severity",
        choices=["all", "P1", "P2", "P3", "P4"],
        default="all",
        help="Filter tests by Jira Defect Severity",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)",
    )

    args = parser.parse_args()

    if args.mode == "server":
        print(f"🚀 Starting eCommerce Target API on http://127.0.0.1:{args.port} ...")
        print(f"   REST Docs:    http://127.0.0.1:{args.port}/docs")
        print(f"   GraphQL IDE:  http://127.0.0.1:{args.port}/graphql")
        import uvicorn
        uvicorn.run("server.app:app", host="127.0.0.1", port=args.port, reload=True)
        return

    # Mode == "test"
    os.makedirs("reports", exist_ok=True)
    cmd = [sys.executable, "-m", "pytest", "-v"]

    markers = []
    if args.protocol != "all":
        markers.append(args.protocol)
    if args.severity != "all":
        markers.append(f"jira and {args.severity}")

    if markers:
        cmd.extend(["-m", " and ".join(markers)])

    cmd.extend([
        "--html=reports/report.html",
        "--self-contained-html",
        "--alluredir=reports/allure-results",
    ])

    print("=" * 75)
    print("⚡ REST & GraphQL API Test Automation Suite")
    print(f"   Protocol: {args.protocol} | Severity Filter: {args.severity}")
    print(f"   Command:  {' '.join(cmd)}")
    print("=" * 75)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
