from __future__ import annotations

import re
from typing import List


# Keep parity with the TS SDK default
MAX_FRAGMENT_CHARS: int = 15000


def fragment_markdown(markdown_content: str, max_fragment_chars: int = MAX_FRAGMENT_CHARS) -> List[str]:
    """Split markdown into fragments by headers and merge up to a size threshold.

    The algorithm mirrors the TypeScript implementation in sdk/typescript/src/fragment.ts:
    - Identify markdown headers (lines beginning with 1-6 '#') as fragment boundaries
    - Preserve any content before the first header as its own fragment if non-empty
    - Merge adjacent fragments as long as the concatenation does not exceed
      max_fragment_chars and does not break image references of the form
      ![alt](url)
    """

    # Lines starting with 1-6 '#' followed by at least one space
    header_pattern = re.compile(r"^#{1,6}\s+.*$", re.MULTILINE)
    # Image references of the form ![alt](url)
    image_pattern = re.compile(r"!\[.*?\]\(.*?\)", re.DOTALL)

    headers: List[re.Match[str]] = list(header_pattern.finditer(markdown_content))

    fragments: List[str] = []

    if not headers:
        return [markdown_content]

    # Content before the first header
    pre_header_end = headers[0].start()
    if pre_header_end > 0:
        pre_header_content = markdown_content[:pre_header_end]
        if pre_header_content.strip():
            fragments.append(pre_header_content)

    # Split content between headers
    for i, header_match in enumerate(headers):
        start_pos = header_match.start()
        end_pos = headers[i + 1].start() if i < len(headers) - 1 else len(markdown_content)
        fragment_content = markdown_content[start_pos:end_pos]
        fragments.append(fragment_content)

    # Merge fragments up to threshold, without breaking image references
    merged_fragments: List[str] = []
    current_content: str = ""

    for fragment in fragments:
        combined_content = current_content + fragment

        if len(combined_content) <= max_fragment_chars:
            # Count image references in combined vs separate contents.
            combined_refs = list(image_pattern.finditer(combined_content))
            current_refs = list(image_pattern.finditer(current_content))
            next_refs = list(image_pattern.finditer(fragment))

            # If concatenation does not reduce the count of complete image refs,
            # consider it safe w.r.t breaking an image token.
            if not current_content or len(combined_refs) >= len(current_refs) + len(next_refs):
                current_content = combined_content
            else:
                if current_content:
                    merged_fragments.append(current_content)
                current_content = fragment
        else:
            if current_content:
                merged_fragments.append(current_content)
            current_content = fragment

    if current_content:
        merged_fragments.append(current_content)

    return merged_fragments or [markdown_content]


