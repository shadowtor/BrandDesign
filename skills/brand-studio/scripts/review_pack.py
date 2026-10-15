#!/usr/bin/env python3
"""Assemble the packet for the independent design-review sub-agent (see references/review-agent.md).

  python3 scripts/review_pack.py --brief brief.md --concepts concepts.png --svgs a.svg b.svg c.svg \
      --round 1 --out review/round-1

Writes <out>/REVIEW-PACKET.md: the business brief (verbatim, from the user's words), the audit output for each SVG,
the files the reviewer must look at, the checklist and the exact reply format. Paste its content as the sub-agent's
prompt (the sub-agent has no other context). It deliberately contains NO statement of which concept you prefer:
a reviewer handed your hypothesis tends to confirm it.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "templates", "review-brief.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", required=True, help="markdown file with the business brief")
    ap.add_argument("--concepts", help="concept sheet PNG")
    ap.add_argument("--svgs", nargs="*", default=[])
    ap.add_argument("--extra", nargs="*", default=[], help="other files to look at (test sheets, mockups)")
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--stage", choices=["concepts", "kit"], default="concepts")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)
    audits = []
    for s in a.svgs:
        r = subprocess.run([sys.executable, os.path.join(HERE, "svg_audit.py"), s], capture_output=True, text=True)
        audits.append(f"### {os.path.basename(s)}\n```\n{(r.stdout or r.stderr).strip()}\n```")
    files = [f for f in [a.concepts, *a.svgs, *a.extra] if f]
    tpl = open(TEMPLATE, encoding="utf-8").read()
    text = (tpl.replace("{{BRIEF}}", open(a.brief, encoding="utf-8").read().strip())
               .replace("{{FILES}}", "\n".join(f"- {os.path.abspath(f)}" for f in files) or "- (none)")
               .replace("{{AUDITS}}", "\n\n".join(audits) or "(no SVG audits)")
               .replace("{{ROUND}}", str(a.round)).replace("{{STAGE}}", a.stage))
    p = os.path.join(a.out, "REVIEW-PACKET.md")
    open(p, "w", encoding="utf-8").write(text)
    print("wrote", p)


if __name__ == "__main__":
    main()
