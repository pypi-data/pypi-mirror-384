"""Command-line interface for searching and downloading arXiv papers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from textwrap import fill, indent
from typing import Iterable, List, Optional

import arxiv
import requests


SORT_CHOICES = {
    "relevance": arxiv.SortCriterion.Relevance,
    "submitted": arxiv.SortCriterion.SubmittedDate,
    "updated": arxiv.SortCriterion.LastUpdatedDate,
}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search arXiv.org and optionally download PDFs using the arxiv Python package."
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of results fetched per API call (default: 100).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Delay in seconds between API calls to avoid rate limiting (default: 3.0).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retries for transient API errors (default: 3).",
    )

    subparsers = parser.add_subparsers(dest="command")

    search = subparsers.add_parser("search", help="Search arXiv and display the results.")
    add_query_arguments(search)
    search.add_argument(
        "--summary",
        action="store_true",
        help="Show the abstract summary for each result.",
    )
    search.add_argument(
        "--json",
        action="store_true",
        help="Emit search results as JSON (ignores --summary).",
    )

    download = subparsers.add_parser(
        "download", help="Download PDFs for the results of a search or specific paper IDs."
    )
    add_query_arguments(download)
    download.add_argument(
        "--dest",
        type=Path,
        default=Path.cwd(),
        help="Directory where PDFs will be saved (default: current directory).",
    )
    download.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that are already present instead of raising an error.",
    )
    download.add_argument(
        "--prefer-source",
        action="store_true",
        help="Download source tarballs when available instead of PDFs.",
    )

    parser.set_defaults(command="search")
    return parser.parse_args(argv)


def add_query_arguments(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "query",
        nargs="*",
        help="Free-form query terms (joined with spaces).",
    )
    subparser.add_argument(
        "--author",
        "-a",
        action="append",
        help="Filter by author name; repeat for multiple authors.",
    )
    subparser.add_argument(
        "--title",
        "-t",
        action="append",
        help="Filter by title terms; repeat for multiple values.",
    )
    subparser.add_argument(
        "--category",
        "-c",
        action="append",
        help="Restrict to categories such as hep-th or cs.LG; repeat for multiple categories.",
    )
    subparser.add_argument(
        "--id",
        "-i",
        action="append",
        help="Fetch specific arXiv identifiers (e.g. 2101.01234); repeat for multiple IDs.",
    )
    subparser.add_argument(
        "--max-results",
        "-n",
        type=int,
        default=10,
        help="Maximum number of results to retrieve (default: 10).",
    )
    subparser.add_argument(
        "--sort",
        choices=sorted(SORT_CHOICES.keys()),
        default="submitted",
        help="Sort order for search results (default: submitted).",
    )
    subparser.add_argument(
        "--ascending",
        action="store_true",
        help="Sort in ascending order (default: descending).",
    )


def create_client(args: argparse.Namespace) -> arxiv.Client:
    return arxiv.Client(
        page_size=args.page_size,
        delay_seconds=args.delay,
        num_retries=args.retries,
    )


def build_search(args: argparse.Namespace) -> arxiv.Search:
    query_string = compose_query(
        free_text=" ".join(args.query) if args.query else "",
        authors=args.author,
        titles=args.title,
        categories=args.category,
    )
    sort_by = SORT_CHOICES[args.sort]
    sort_order = arxiv.SortOrder.Ascending if args.ascending else arxiv.SortOrder.Descending

    return arxiv.Search(
        query=query_string or None,
        id_list=args.id or [],
        max_results=args.max_results,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def compose_query(
    free_text: str = "",
    authors: Optional[Iterable[str]] = None,
    titles: Optional[Iterable[str]] = None,
    categories: Optional[Iterable[str]] = None,
) -> str:
    tokens: List[str] = []
    if free_text:
        tokens.append(free_text)
    if authors:
        tokens.extend(f'au:"{_escape_quotes(author)}"' for author in authors)
    if titles:
        tokens.extend(f'ti:"{_escape_quotes(title)}"' for title in titles)
    if categories:
        tokens.extend(f'cat:{category}' for category in categories)
    return " AND ".join(token for token in tokens if token)


def _escape_quotes(value: str) -> str:
    return value.replace("\"", "\\\"")


def run_search(args: argparse.Namespace, client: arxiv.Client) -> int:
    search = build_search(args)
    try:
        results = list(limited_results(client.results(search), args.max_results))
    except requests.exceptions.RequestException as exc:
        print(f"Failed to query arXiv: {exc}", file=sys.stderr)
        return 1
    except (arxiv.HTTPError, arxiv.UnexpectedEmptyPageError, arxiv.ArxivError) as exc:
        print(f"arXiv API error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        json_results = [serialize_result(result) for result in results]
        json.dump(json_results, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not results:
        print("No results found.")
        return 0

    for index, result in enumerate(results, start=1):
        print(format_result(result, index=index, show_summary=args.summary))
    return 0


def limited_results(results: Iterable[arxiv.Result], limit: int) -> Iterable[arxiv.Result]:
    for index, result in enumerate(results):
        if index >= limit:
            break
        yield result


def serialize_result(result: arxiv.Result) -> dict:
    return {
        "id": result.entry_id,
        "short_id": result.entry_id.split("/")[-1],
        "title": result.title,
        "summary": result.summary,
        "published": result.published.isoformat() if result.published else None,
        "updated": result.updated.isoformat() if result.updated else None,
        "authors": [getattr(author, "name", str(author)) for author in result.authors],
        "primary_category": result.primary_category,
        "categories": list(result.categories),
        "pdf_url": result.pdf_url,
        "comment": result.comment,
        "journal_ref": result.journal_ref,
        "doi": result.doi,
    }


def format_result(result: arxiv.Result, *, index: int, show_summary: bool) -> str:
    authors = ", ".join(getattr(author, "name", str(author)) for author in result.authors)
    identifier = result.entry_id.split("/")[-1]
    lines = [
        f"[{index}] {result.title.strip()}",
        f"    id: {identifier}",
        f"    primary: {result.primary_category}; categories: {', '.join(result.categories)}",
        f"    authors: {authors}",
    ]
    if result.published:
        lines.append(f"    published: {result.published:%Y-%m-%d}")
    if result.updated:
        lines.append(f"    updated: {result.updated:%Y-%m-%d}")
    if result.pdf_url:
        lines.append(f"    pdf: {result.pdf_url}")
    if show_summary and result.summary:
        wrapped = fill(result.summary.strip(), width=88)
        lines.append(indent(wrapped, "    abstract: "))
    return "\n".join(lines)


def run_download(args: argparse.Namespace, client: arxiv.Client) -> int:
    destination = args.dest.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    search = build_search(args)
    try:
        results = list(limited_results(client.results(search), args.max_results))
    except requests.exceptions.RequestException as exc:
        print(f"Failed to query arXiv: {exc}", file=sys.stderr)
        return 1
    except (arxiv.HTTPError, arxiv.UnexpectedEmptyPageError, arxiv.ArxivError) as exc:
        print(f"arXiv API error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No results to download.")
        return 0

    for result in results:
        identifier = result.entry_id.split("/")[-1]
        try:
            downloader = result.download_source if args.prefer_source else result.download_pdf
            path = downloader(dirpath=str(destination))
            print(f"Downloaded {identifier} -> {path}")
        except FileExistsError:
            if args.skip_existing:
                print(f"Skipping {identifier} (already exists)")
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to download {identifier}: {exc}", file=sys.stderr)
    return 0

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    client = create_client(args)

    if args.command == "search":
        return run_search(args, client)
    if args.command == "download":
        return run_download(args, client)
    raise ValueError(f"Unhandled command: {args.command}")


__all__ = ["main", "parse_args"]
