import os
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests


EXTCCE_CATALOG_URL = "https://data.black-holes.org/waveforms/extcce_catalog.html"


class _RowParser(HTMLParser):
    """
    Collect each <tr> row as:
      - visible row text
      - links found inside the row
    """
    def __init__(self):
        super().__init__()
        self.in_tr = False
        self.current_text = []
        self.current_links = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.in_tr = True
            self.current_text = []
            self.current_links = []
        elif self.in_tr and tag == "a":
            href = attrs.get("href")
            if href:
                self.current_links.append(href)

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_tr:
            text = " ".join("".join(self.current_text).split())
            self.rows.append((text, self.current_links[:]))
            self.in_tr = False

    def handle_data(self, data):
        if self.in_tr and data.strip():
            self.current_text.append(data.strip() + " ")


def _fetch_catalog_html(timeout=60):
    r = requests.get(EXTCCE_CATALOG_URL, timeout=timeout)
    r.raise_for_status()
    return r.text


def _parse_catalog_rows(catalog_html):
    parser = _RowParser()
    parser.feed(catalog_html)
    return parser.rows


def _extract_alt_name_from_row_text(row_text):
    """
    Extract alt names like:
      q1_nospin
      q4_precessing
      q1_aligned_chi0_2
    from a row's text.
    """
    m = re.search(r"\b(q[0-9A-Za-z]+(?:_[0-9A-Za-z]+)+)\b", row_text)
    if m:
        return m.group(1)
    return None


def _extract_zenodo_like_link(links):
    for href in links:
        href_abs = urljoin(EXTCCE_CATALOG_URL, href)
        if "zenodo" in href_abs or "doi.org/10.5281/zenodo." in href_abs:
            return href_abs
    return None


def get_extcce_catalog_map(timeout=60):
    """
    Returns:
      {alt_name: zenodo_or_doi_url}
    """
    html = _fetch_catalog_html(timeout=timeout)
    rows = _parse_catalog_rows(html)

    mapping = {}
    for row_text, links in rows:
        alt_name = _extract_alt_name_from_row_text(row_text)
        if not alt_name:
            continue

        zenodo_link = _extract_zenodo_like_link(links)
        if zenodo_link:
            mapping[alt_name] = zenodo_link

    return mapping


def list_extcce_alt_names(timeout=60):
    return sorted(get_extcce_catalog_map(timeout=timeout).keys())


def extcce_alt_name_exists(alt_name, timeout=60):
    return alt_name in get_extcce_catalog_map(timeout=timeout)


def _find_zenodo_link_for_alt_name(alt_name, timeout=60):
    mapping = get_extcce_catalog_map(timeout=timeout)
    if alt_name not in mapping:
        sample = sorted(mapping.keys())[:30]
        raise ValueError(
            f"Alt name '{alt_name}' was not found in the Ext-CCE catalog.\n"
            f"Some available alt names: {sample}"
        )
    return mapping[alt_name]


def _resolve_zenodo_record_id(url, timeout=60):
    r = requests.get(url, allow_redirects=True, timeout=timeout)
    r.raise_for_status()
    final_url = r.url.rstrip("/")

    m = re.search(r"zenodo\.org/records/(\d+)", final_url)
    if not m:
        m = re.search(r"zenodo\.(\d+)", final_url)
    if not m:
        raise ValueError(f"Could not resolve Zenodo record ID from URL: {final_url}")

    record_id = m.group(1)
    return record_id, f"https://zenodo.org/records/{record_id}"


def _fetch_zenodo_record_json(record_id, timeout=60):
    api_url = f"https://zenodo.org/api/records/{record_id}"
    r = requests.get(api_url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _iter_record_files(record_json):
    files = record_json.get("files", [])
    if not isinstance(files, list):
        raise ValueError(f"Unexpected Zenodo 'files' structure: {type(files).__name__}")
    for f in files:
        yield f


def _get_file_path_and_url(file_entry):
    file_path = file_entry.get("key") or file_entry.get("filename") or ""
    links = file_entry.get("links", {}) or {}
    url = (
        links.get("self")
        or links.get("content")
        or file_entry.get("download")
        or ""
    )
    return file_path, url


def _extract_lev5_radii(file_entries):
    radii = set()

    for f in file_entries:
        file_path, _ = _get_file_path_and_url(f)
        if not file_path.startswith("Lev5/"):
            continue
        m = re.search(r"_R(\d+)", file_path)
        if m:
            radii.add(int(m.group(1)))

    return sorted(radii)


def _choose_second_smallest_radius(file_entries):
    radii = _extract_lev5_radii(file_entries)
    if len(radii) < 2:
        raise ValueError(f"Need at least two Lev5 radii, found: {radii}")
    return radii[1]


def _select_files(file_entries, radius_int):
    radius_tag = f"R{radius_int:04d}"
    selected = []

    for f in file_entries:
        file_path, url = _get_file_path_and_url(f)
        if not file_path or not url:
            continue
        if not file_path.startswith("Lev5/"):
            continue

        base = os.path.basename(file_path).lower()

        # Always include metadata
        if file_path == "Lev5/metadata.json":
            selected.append((file_path, url))
            continue

        # Chosen radius only
        if radius_tag not in file_path:
            continue

        # Exclude any file with "news" in the filename
        if "news" in base:
            continue

        selected.append((file_path, url))

    deduped = []
    seen = set()
    for file_path, url in selected:
        if file_path not in seen:
            seen.add(file_path)
            deduped.append((file_path, url))

    return deduped, radius_tag


def get_extcce_download_plan(alt_name, timeout=60):
    """
    Inspect what would be downloaded, without downloading.
    """
    zenodo_link = _find_zenodo_link_for_alt_name(alt_name, timeout=timeout)
    record_id, record_url = _resolve_zenodo_record_id(zenodo_link, timeout=timeout)
    record_json = _fetch_zenodo_record_json(record_id, timeout=timeout)
    file_entries = list(_iter_record_files(record_json))

    radius_int = _choose_second_smallest_radius(file_entries)
    selected_files, radius_tag = _select_files(file_entries, radius_int)

    if not selected_files:
        raise ValueError(f"No matching files found for alt name '{alt_name}' at radius {radius_tag}")

    return {
        "alt_name": alt_name,
        "zenodo_record_id": record_id,
        "zenodo_record_url": record_url,
        "radius_int": radius_int,
        "radius_tag": radius_tag,
        "local_dir": alt_name,
        "files": selected_files,
    }


def download_extcce_simulation(alt_name, base_dir=".", timeout=60, verbose=True):
    """
    Download into:
      <base_dir>/<alt_name>/

    Saved files are flattened by basename, e.g.
      <alt_name>/metadata.json
      <alt_name>/r2Psi4_BondiCce_R0237_CoM.h5
    """
    plan = get_extcce_download_plan(alt_name, timeout=timeout)

    local_dir = os.path.join(base_dir, alt_name)
    os.makedirs(local_dir, exist_ok=True)

    downloaded = []
    skipped = []
    failed = []

    for remote_path, url in plan["files"]:
        local_path = os.path.join(local_dir, os.path.basename(remote_path))

        if os.path.exists(local_path):
            skipped.append(local_path)
            if verbose:
                print(f"Exists:  {local_path}")
            continue

        if verbose:
            print(f"Downloading: {local_path}")
            print(f"  from: {url}")

        result = subprocess.run(["wget", "-c", url, "-O", local_path])

        if result.returncode == 0 and os.path.exists(local_path):
            downloaded.append(local_path)
        else:
            failed.append(local_path)

    return {
        "alt_name": plan["alt_name"],
        "zenodo_record_id": plan["zenodo_record_id"],
        "zenodo_record_url": plan["zenodo_record_url"],
        "radius_int": plan["radius_int"],
        "radius_tag": plan["radius_tag"],
        "local_dir": local_dir,
        "requested_files": [os.path.basename(x[0]) for x in plan["files"]],
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
    }
