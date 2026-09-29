# Large original media from Google Drive

Use this route when remote camera originals exceed a connector's materialization limit or the internal disk cannot hold a streamed cache. Inventory file IDs, names, MIME types, exact byte sizes and the destination volume before transferring. Keep partial files separate from completed originals.

## Choose the actual download route

The tested Drive connector rejected `google_drive_fetch(download_raw_file=true, include_base64=false)` with HTTP 413 for a stored WAV larger than **268,435,456 bytes (256 MiB)**. This was that connector's raw materialization limit, not a Google Drive file-size limit. Disabling base64 did not remove it. Read the current response; do not repeatedly retry the same oversized route or apply this bound to unrelated export APIs.

An existing Drive Desktop folder may be usable, but on macOS File Provider its streamed-file cache cannot be relocated to an external volume. A large copy can therefore consume internal storage while materializing its source. Confirm the active mode and free space before relying on it. [Google's advanced Drive guide](https://support.google.com/drive/answer/16631477) documents the cache restriction.

File Provider normally exposes files under `~/Library/CloudStorage`; legacy Drive used `/Volumes/GoogleDrive`. Spotlight sees only a subset, so an empty Spotlight result does not establish absence. Search through the existing Drive UI when needed. Copy originals rather than moving them out of Drive. [Google's macOS guide](https://support.google.com/drive/answer/12178485) describes the locations, search limits and move behavior.

For a file explicitly shown as accessible to anyone with its link without sign-in, a direct public download can write to the destination SSD. `shared: true` alone does not establish public access. The tested public route used the official [gdown project](https://github.com/wkentaro/gdown), pinned to 6.2.0 in an isolated `uv` tool environment:

```sh
uv tool run --from gdown==6.2.0 gdown \
  --no-cookies --continue --output "$ABSOLUTE_DESTINATION_FILE" "$VERIFIED_DRIVE_FILE_ID"
```

Set the two variables from the verified inventory; retain the original filename and an explicit absolute output path on the intended volume. Keep TLS verification enabled. Public access may still be subject to quotas; a downloader error is not permission to alter sharing settings.

If authentication is required, use an already authenticated browser's supported download flow with the destination verified, or a supported authenticated connector that can stream the actual file. Do not extract tokens or browser cookies, change sharing permissions, or copy session credentials into a downloader. Resume after an actual sign-in requirement has been satisfied through the supported UI.

## Resume and verify

In the tested gdown version, an explicit output keeps its temporary `.part` beside the destination and `--continue` resumes it. An existing final file can be skipped without validating it. Therefore, verify every completion against the inventory's exact byte count, then record a local SHA-256 and probe the actual media. A locally computed hash is a reproducibility record; it proves remote integrity only when compared with an authoritative remote digest.

Use one owner/lock per file and a small bounded worker pool. Prioritize usable dialogue and camera ISOs; increase parallelism only when measured aggregate throughput improves. Record pending, downloading, complete and failed states, actual bytes, final paths, hashes and probe summaries. Never import a `.part` or sparse head/tail probe artifact as a camera original; a sparse file's logical size does not mean its bytes were downloaded.

No global Drive settings or caches need to change for the verified public-to-SSD route. Keep downloader logs and source verification records with the episode, outside reusable skill backups.
