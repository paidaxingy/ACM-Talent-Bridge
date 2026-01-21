from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ExternalContestItem:
    source: str
    external_id: str
    name: str
    url: str
    start_at: datetime  # stored as naive UTC
    duration_seconds: int
    contest_type: str | None = None
    raw: str | None = None


class ContestSource(Protocol):
    source_name: str

    def fetch(self) -> list[ExternalContestItem]: ...


def _dt_utc_from_ts(seconds: int) -> datetime:
    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(tzinfo=None)


class CodeforcesSource:
    source_name = "codeforces"

    def fetch(self) -> list[ExternalContestItem]:
        url = "https://codeforces.com/api/contest.list?gym=false"
        with httpx.Client(timeout=15) as client:
            r = client.get(url, headers={"User-Agent": "ACM-Talent-Bridge/1.0"})
            r.raise_for_status()
            data = r.json()

        if data.get("status") != "OK":
            raise RuntimeError(f"Codeforces API error: {data.get('comment')}")

        items: list[ExternalContestItem] = []
        for c in data.get("result", []):
            # Only keep upcoming or running contests for now
            phase = c.get("phase")
            if phase not in {"BEFORE", "CODING"}:
                continue

            cid = str(c.get("id"))
            name = str(c.get("name", "")).strip()
            start = int(c.get("startTimeSeconds") or 0)
            dur = int(c.get("durationSeconds") or 0)
            ctype = c.get("type")
            items.append(
                ExternalContestItem(
                    source=self.source_name,
                    external_id=cid,
                    name=name,
                    url=f"https://codeforces.com/contest/{cid}",
                    start_at=_dt_utc_from_ts(start),
                    duration_seconds=dur,
                    contest_type=str(ctype) if ctype else None,
                    raw=json.dumps(c, ensure_ascii=False),
                )
            )
        return items


class AtCoderSource:
    source_name = "atcoder"

    def fetch(self) -> list[ExternalContestItem]:
        url = "https://atcoder.jp/contests/"
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            r = client.get(url, headers={"User-Agent": "ACM-Talent-Bridge/1.0"})
            r.raise_for_status()
            html = r.text

        soup = BeautifulSoup(html, "html.parser")
        items: list[ExternalContestItem] = []

        def parse_table(table_id: str):
            table = soup.find("table", {"id": table_id})
            if not table:
                return
            tbody = table.find("tbody")
            if not tbody:
                return
            for tr in tbody.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) < 2:
                    continue
                # Start time
                time_tag = tds[0].find("time")
                start_at: datetime | None = None
                if time_tag:
                    if time_tag.has_attr("data-time"):
                        try:
                            start_at = _dt_utc_from_ts(int(time_tag["data-time"]))
                        except Exception:  # noqa: BLE001 (best-effort)
                            start_at = None
                    elif time_tag.has_attr("datetime"):
                        try:
                            dt = datetime.fromisoformat(str(time_tag["datetime"]).replace("Z", "+00:00"))
                            start_at = dt.astimezone(timezone.utc).replace(tzinfo=None)
                        except Exception:  # noqa: BLE001 (best-effort)
                            start_at = None

                # Contest link
                a = tds[1].find("a")
                if not a or not a.get("href"):
                    continue
                href = a["href"]
                m = re.match(r"^/contests/([^/]+)/?$", href)
                if not m:
                    continue
                slug = m.group(1)
                name = a.get_text(strip=True)

                # Duration (usually HH:MM)
                dur_sec = 0
                if len(tds) >= 3:
                    dur_txt = tds[2].get_text(strip=True)
                    if re.match(r"^\\d{1,2}:\\d{2}$", dur_txt):
                        h, mm = dur_txt.split(":")
                        dur_sec = int(h) * 3600 + int(mm) * 60

                # Rated range / type
                ctype = None
                if len(tds) >= 4:
                    ctype = tds[3].get_text(strip=True) or None

                if start_at is None:
                    # If we can't parse start time, skip to avoid wrong data.
                    continue

                items.append(
                    ExternalContestItem(
                        source=self.source_name,
                        external_id=slug,
                        name=name,
                        url=f"https://atcoder.jp/contests/{slug}",
                        start_at=start_at,
                        duration_seconds=dur_sec,
                        contest_type=ctype,
                        raw=None,
                    )
                )

        # AtCoder page uses these IDs
        parse_table("contest-table-upcoming")
        parse_table("contest-table-active")
        return items


class NowcoderSource:
    source_name = "nowcoder"

    def fetch(self) -> list[ExternalContestItem]:
        # Many Nowcoder contest pages are dynamic / may require anti-bot measures.
        # We keep a safe stub here and can enhance it with a stable endpoint later.
        return []


def default_sources() -> list[ContestSource]:
    return [CodeforcesSource(), AtCoderSource(), NowcoderSource()]

