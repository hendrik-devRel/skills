# Adobe resource checks during rendering

Use this when a long native render stalls, a cache-space warning appears, or several tasks share a Mac. A previous successful render does not establish capacity for a longer composition.

## Coordinate the workload

Give one task ownership of the shared Adobe application. Reading transcripts, selecting excerpts and preparing small operation plans can proceed separately. Serialize expensive AE/Premiere renders, FFmpeg encodes and speech models while diagnosing pressure. A second `aerender` process can add memory load; it does not provide resource isolation.

Before a native render, save the project and inspect the render queue. When enabling one item at a time, **configure output modules and render settings first, set render flags last, then inspect that exactly the intended item is QUEUED**. In the observed AE workflow, applying output-module settings re-enabled previously disabled items and unintentionally ran a continuous queue.

After a `render.start` timeout, inspect progress through the native UI; the application and original script may still be running. Wait for that script to finish before another AE MCP call, **including read-only render status**. A premature status request in the observed run triggered a second-script warning. Dismiss that warning without choosing an override to run a competing script; allow the dispatcher lock to release normally rather than deleting or bypassing it. An unresponsive bridge alone is not evidence of an out-of-memory crash.

Native Stop can leave a partial item and create a **WILL_CONTINUE** queue entry targeting the same path. Once the original script is finished, inspect queue state, frame ranges and paths before resuming. If the plan requires a complete segment, disable/remove the continuation and render the intended whole range to an unambiguous output; do not mistake a resumed tail for a complete segment.

## Measure the current state

The read-only macOS helper `scripts/resource_snapshot.py` records physical RAM, the kernel pressure flag, swap, VM compression, disk headroom and process RSS. Run it in a bounded foreground job with a unique output path:

```sh
python3 /absolute/skill/path/scripts/resource_snapshot.py \
  --project-path /absolute/project/path \
  --samples 4 --interval 10 \
  --output /absolute/project/path/resource-check.json
```

Compare a baseline, the active render and completion. Keep the raw readings and timestamps. The helper changes no settings, caches, projects or processes and makes no automatic safety decision. Missing measurements are null. Process names omit command arguments.

Interpret the measurements together:

- Sustained warning/critical pressure and growing swap merit reducing the workload. High memory usage alone does not establish a fault.
- RSS excludes compressed memory and is not the process physical footprint. If necessary, obtain a read-only `vmmap -summary PID` measurement for the verified AE process. Do not describe its swapped-out accounting as equivalent to system disk swap.
- Separate current swap occupancy from cumulative VM event counters. Current swap usage can shrink after recovery, as it did in this run. A recent reboot can conceal an earlier resource problem; a normal post-reboot reading is not retrospective evidence.
- Swap and Adobe disk caches compete for startup-disk space. Measure actual free space, cache allocation, configured cache maximum and output destinations separately.
- A disk-write diagnostic with `Action taken: none` is not proof of an OS termination. Preserve evidence without inventing a memory leak or crash cause.

## Recover between completed renders

When preview frames accumulate, the owning task can save, wait for rendering to finish, and use Adobe's native **image/frame cache purge**. Discover the current operation schema before using it; IMAGE cache is distinct from ALL caches, undo history and disk cache. Recheck pressure afterward. Do not purge during a render or issue competing controls from another task.

During recovery, render one queue item at a time and compare resources during and after each item. Purging image caches between completed items can recover memory but costs later preview regeneration and does not bound memory growth within a long item. If pressure recurs, trial shorter exact frame ranges with purges and resource checks between them. If pressure persists, stop through normal app controls where responsive, save, and reduce the workload. Do not force-quit unsaved work merely because a connector timed out.

In one observed 64 GiB Mac session, AE reached roughly 45 GB physical footprint with sustained warning pressure. Following completion and a native IMAGE purge, AE reported about 1.3 GB in use and the system returned to normal pressure. These process-footprint and AE-reported values use different accounting. A subsequent single 95-second clip reached warning pressure despite a fresh cache, then recovered after another purge. Three individually enabled sections of approximately 10 seconds each, with purges between them, retained normal pressure throughout their recorded samples. This supports cache accumulation as a contributor and shorter ranges as a useful trial for that workload; it is not a universal diagnosis or guaranteed fix.

The subsequent video-only assembly passed exact frame count, zero-origin presentation timestamps for every frame, and decoded YUV-byte equality with the ordered native segments. Separate final audio/mux checks subsequently passed exact length and tail coverage with zero measured lag in distributed audio windows. Do not equate normal pressure or pixel-identical assembly with a fully validated delivery: verify audio continuity and synchronization separately. Disk free space also continued to fall while memory pressure stayed normal, so an IMAGE purge does not resolve disk-cache capacity.

Once native work is complete, save and quit AE normally if the shared application is no longer needed, independently verify it has stopped, and take a final resource snapshot before offline delivery checks. In the observed run, pressure remained normal after quitting despite residual swap; remaining swap alone is not evidence that memory pressure persists. Recheck disk headroom independently.

## Persistent settings are a separate decision

Inspect existing values before recommending changes. Follow the current connector's requirements for user-requested application preference changes. Coordinate with the owner of the shared Adobe session. Document actual changes separately from suggestions.

Adobe shares its memory pool across several applications. Reserve enough RAM for the OS, browser and other work. CPU reservation is not a memory limit. Multi-Frame Rendering and idle preview caching can add work; change one relevant variable at a time and verify a representative render.

For a disk-cache warning, reducing a limit alone may leave old cache files consuming space. Use Adobe's native disk-cache control while idle to clear rebuildable cache when authorized; preserve source recordings, projects and exports. Check free space afterward. Consider cache size plus export/temp growth and swap needs, rather than treating an arbitrary free-space percentage as a guarantee.

An example trial for the observed 64 GiB machine was 20 GiB reserved for other apps, a 32 GB disk-cache cap instead of 92 GB, and disabling idle frame caching during automation. These were **proposals, not validated defaults**. Select settings from the current hardware and workload.

## References

- [Adobe memory and storage](https://helpx.adobe.com/after-effects/desktop/memory-storage-performance/memory-and-storage/memory-storage1.html)
- [Adobe Multi-Frame Rendering](https://helpx.adobe.com/after-effects/desktop/render-and-export/multi-frame-rendering/multi-frame-rendering.html)
- [Apple memory usage in Activity Monitor](https://support.apple.com/guide/activity-monitor/view-memory-usage-actmntr1004/mac)
