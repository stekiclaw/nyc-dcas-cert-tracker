#!/usr/bin/env bash
# Optional CLI helper; the ChatGPT skill itself remains prompt-only.
set -Eeuo pipefail

usage() {
  cat <<'USAGE'
Fetch a complete *filtered* NYC Socrata SODA2 dataset as a JSON array.
Requires: bash, curl, jq. Optional: SODA_APP_TOKEN environment variable.

Usage:
  scripts/fetch-soda.sh --where "exam_no='4034' AND last_name='EXAMPLE'" \
    [--dataset a9md-ynri] [--out certs.json] [--page-size 1000] [--max-rows 50000]

Use official API field names. Supply a selective SoQL predicate; never run a
multi-million-row unfiltered scrape. Single quotes inside a SoQL string must
be doubled (e.g., O''NEILL). The script checks counts before/after paging.
A failed or inconsistent run never replaces the prior output file.
USAGE
}

dataset="a9md-ynri"
where=""
out="soda-results.json"
page_size=1000
max_rows=50000
order=''

while (($#)); do
  case "$1" in
    --dataset|--where|--out|--page-size|--max-rows|--order)
      if (($# < 2)); then echo "Missing value for $1" >&2; exit 2; fi
      case "$1" in
        --dataset) dataset=$2 ;;
        --where) where=$2 ;;
        --out) out=$2 ;;
        --page-size) page_size=$2 ;;
        --max-rows) max_rows=$2 ;;
        --order) order=$2 ;;
      esac
      shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ "$dataset" =~ ^[a-z0-9]{4}-[a-z0-9]{4}$ ]] || { echo 'Invalid dataset ID' >&2; exit 2; }
[[ -n "\${where//[[:space:]]/}" ]] || { echo 'Required: --where with a selective SoQL predicate' >&2; exit 2; }
[[ "$page_size" =~ ^[0-9]+$ ]] && ((10#$page_size >= 1 && 10#$page_size <= 5000)) || { echo 'Invalid page size (1..5000)' >&2; exit 2; }
[[ "$max_rows" =~ ^[0-9]+$ ]] && ((10#$max_rows >= 1 && 10#$max_rows <= 1000000)) || { echo 'Invalid max rows (1..1000000)' >&2; exit 2; }
if [[ -z "$order" ]]; then
  if [[ "$dataset" == 'a9md-ynri' ]]; then order='request_date DESC, :id DESC'
  else order=':id DESC'; fi
fi
for tool in curl jq mktemp; do command -v "$tool" >/dev/null || { echo "Missing dependency: $tool" >&2; exit 2; }; done

url="https://data.cityofnewyork.us/resource/\${dataset}.json"
workdir="$(mktemp -d)"
out_tmp=""
cleanup() { rm -rf -- "$workdir"; [[ -z "$out_tmp" ]] || rm -f -- "$out_tmp"; }
trap cleanup EXIT

curl_args=(--silent --show-error --location --fail-with-body --retry 5 --retry-delay 2 \
  --retry-max-time 180 --connect-timeout 10 --max-time 60 --header 'Accept: application/json' --get)
if [[ -n "\${SODA_APP_TOKEN:-}" ]]; then
  curl_args+=(--header "X-App-Token: \${SODA_APP_TOKEN}")
fi

fetch_count() {
  local path=$1
  curl "\${curl_args[@]}" --output "$path" \
    --data-urlencode '$select=count(*) as total' \
    --data-urlencode "\$where=$where" "$url"
  jq -er 'if type == "array" and length == 1 then (.[0].total | tonumber)
    else error("Expected one count record") end' "$path"
}

echo "Fetching count (\${dataset})..." >&2
expected="$(fetch_count "$workdir/before.json")" || { echo 'Count query failed' >&2; exit 1; }
[[ "$expected" =~ ^[0-9]+$ ]] || { echo 'Invalid count from Socrata' >&2; exit 1; }
((expected <= 10#$max_rows)) || { echo "Refusing $expected rows (max: $max_rows); refine --where" >&2; exit 1; }

page=0
received=0
while ((received < expected)); do
  offset=$((page * 10#$page_size))
  filename="$(printf '%s/page-%08d.json' "$workdir" "$page")"
  curl "\${curl_args[@]}" --output "$filename" \
    --data-urlencode "\$where=$where" \
    --data-urlencode "\$order=$order" \
    --data-urlencode "\$limit=$page_size" \
    --data-urlencode "\$offset=$offset" "$url" || { echo "Page fetch failed at offset $offset" >&2; exit 1; }
  rows="$(jq -er 'if type == "array" then length else error("Not a JSON array") end' "$filename")" || exit 1
  left=$((expected - received))
  target=$((left < 10#$page_size ? left : 10#$page_size))
  ((rows == target)) || { echo "Incomplete page: offset=$offset expected=$target received=$rows" >&2; exit 1; }
  received=$((received + rows))
  page=$((page + 1))
done

actual="$(fetch_count "$workdir/after.json")" || { echo 'Final count query failed' >&2; exit 1; }
[[ "$actual" == "$expected" ]] || { echo "Dataset changed during retrieval ($expected -> $actual); discard and rerun" >&2; exit 1; }

mkdir -p -- "$(dirname -- "$out")"
out_tmp="$(mktemp "$(dirname -- "$out")/.soda-results.XXXXXXXX")"
if ((expected == 0)); then
  printf '[]\n' > "$out_tmp"
else
  jq -s 'add' "$workdir"/page-*.json > "$out_tmp"
fi
final_length="$(jq -r 'length' "$out_tmp")"
((final_length == expected)) || { echo "Output length mismatch: $final_length != $expected" >&2; exit 1; }
mv -f -- "$out_tmp" "$out"
out_tmp=""
echo "Verified $expected rows across $page page(s); saved $out" >&2
