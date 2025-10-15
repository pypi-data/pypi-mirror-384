#!/usr/bin/env python3
import argparse
import json
import os
import re
from urllib.parse import urlparse, urlunparse


def replace_domain(url, target, replacement):
    parsed = urlparse(url)
    domain = parsed.netloc

    if replacement.startswith("."):
        target_domain, _, _ = target.partition(".")
        replacement = target_domain + replacement

    if domain == target:
        new_domain = replacement
    elif domain.endswith(target):
        new_domain = domain[: -len(target)] + replacement
    else:
        return url, False

    new_parsed = parsed._replace(netloc=new_domain)
    return urlunparse(new_parsed), True
	
	
def process_html(content, target, replacement, dry):
    changes = []

    def repl(match):
        url = match.group(1)
        new_url, changed = replace_domain(url, target, replacement)
        if changed:
            changes.append((url, new_url))
        return f'HREF="{new_url}"'

    new_content = re.sub(r'HREF="([^"]+)"', repl, content)

    if dry:
        for old, new in changes:
            print(f"🔹 {old}  →  {new}")
        print(f"\n💡 Total changes: {len(changes)}")

    return new_content if not dry else content


def process_json(data, target, replacement, dry, changes):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == "url" and isinstance(v, str):
                new_url, changed = replace_domain(v, target, replacement)
                if changed:
                    if dry:
                        changes.append((v, new_url))
                    else:
                        data[k] = new_url
            else:
                process_json(v, target, replacement, dry, changes)
    elif isinstance(data, list):
        for item in data:
            process_json(item, target, replacement, dry, changes)
    return data


def main_cli():
    parser = argparse.ArgumentParser(
        description="Batch replace bookmark domains safely (HTML or Chrome JSON)."
    )
    parser.add_argument("file", help="Path to bookmarks file (.html or Chrome JSON)")
    parser.add_argument("--target", required=True, help="Target domain to replace (e.g. amazon.de)")
    parser.add_argument("--replace", required=True, help="Replacement domain or extension (e.g. amazon.com or .com)")
    parser.add_argument("--inplace", action="store_true", help="Modify the file in place (default: false)")
    parser.add_argument("--dry", action="store_true", help="Perform a dry run: only print changes, don’t write to file")
    args = parser.parse_args()

    if args.inplace and args.dry:
        print("⚠️  --inplace and --dry cannot be used together.")
        return

    input_file = args.file
    if args.inplace:
        output_file = input_file
    else:
        name, ext = os.path.splitext(input_file)
        output_file = f"{name}_updated{ext}"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    if input_file.lower().endswith(".html"):
        new_content = process_html(content, args.target, args.replace, args.dry)
    else:
        data = json.loads(content)
        changes = []
        new_data = process_json(data, args.target, args.replace, args.dry, changes)

        if args.dry:
            for old, new in changes:
                print(f"🔹 {old}  →  {new}")
            print(f"\n💡 Total changes: {len(changes)}")
            return

        new_content = json.dumps(new_data, indent=2, ensure_ascii=False)

    if not args.dry:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        if args.inplace:
            print(f"✅ In-place update complete: {input_file}")
        else:
            print(f"✅ Done! Updated file saved as: {output_file}")
    else:
        print("\n✅ Dry run complete (no files were modified).")
