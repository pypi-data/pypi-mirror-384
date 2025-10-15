# Bookmark Domain Replace

A Python CLI tool to batch replace domains in browser bookmarks (HTML exports or Chrome JSON files).

## Features
- Replace only the **domain part** of URLs
- Supports **shorthand replacements** (like `.com`)
- Dry-run mode to preview changes
- Optional in-place modification

## Example Usage

Dry-run:
```bash
bookmark-domain-replace bookmarks.html --target amazon.de --replace .com --dry

bookmark-domain-replace bookmarks.html --target amazon.de --replace .com

bookmark-domain-replace bookmarks.html --target amazon.de --replace .com --inplace
```
