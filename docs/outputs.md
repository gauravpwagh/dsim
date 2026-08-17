# Output layer — charting, extraction, and generated files

## `chart_logic3.py`

Matplotlib-based generator for the classic railway **time–distance ("string") chart** —
time on the x-axis, cumulative distance-along-line on the y-axis, one line per train.

- `compute_dynamic_figsize(order, start_win, end_win)` — scales the figure size to the
  time window length and number of stations, with sane minimums.
- `_find_best_label_position(...)` — picks the point along a train's path (within the
  visible window) farthest from every already-placed label, to reduce label overlap.
- `_place_label(...)` — draws a train's ID label with a leader line, alternating
  placement to further reduce clutter.
- `plot_railway_chart(order, segs, schedules, chart_date, filename, start_win=None,
  end_win=None)` — the entry point. Builds cumulative station distances from `order`
  (station list) + `segs` (segment-distance dict — exactly what
  `wat_block_section_distances.py` provides per corridor), plots each train's stop
  times/positions as a colored path (green for passenger, red for goods) with direction
  arrows, adds hour/10-minute gridlines, and saves a PDF.
  `matplotlib.rcParams['pdf.fonttype'] = 42` keeps chart text as real, editable text in
  the PDF rather than outlined vector paths.

Called from `final_sim_sj_4aug.py` via `master_time_distance_chart(...)`, which windows
the simulated schedule and hands it to `plot_railway_chart`.

## `data_extract.py`

Reshaping/windowing helpers that sit between the simulator's wide-format output and the
chart:

- `filter_df_by_date_window(df_simulated, start_date_str, window_hours=23.5)` — validates
  the requested start date is within the simulated data's range, then per train blanks
  out any station stop whose arrival/departure both fall outside the window, dropping
  trains with nothing left in-window.
- `get_formatted_data_from_df(df, start_dt, end_dt)` — reshapes each surviving row into
  `{train_id: {'stops': [(timestamp, station), ...] sorted by time, 'type': 'p'|'g'}}`,
  handling the arr==dep (pass-through, no halt) case.

Both are imported directly by `final_sim_sj_4aug.py` and feed straight into
`plot_railway_chart`.

## The animator JSON (generated inline in `final_sim_sj_4aug.py`)

`total_schedule_to_json(total_schedule, output_filename)` (near the bottom of
`final_sim_sj_4aug.py`) converts the simulator's internal `total_schedule` structure into:

```json
{
  "simulation": {"start_time": "...", "end_time": "..."},
  "trains": [
    {
      "train_id": "...",
      "train_type": "p" or "g",
      "route": [
        {"station": "...", "line": "...", "platform": ..., "arr": "...", "dep": "...", "next_block": "..."}
      ]
    }
  ]
}
```

This is written to the `*_animator.json` output — presumably input to a separate
train-movement animation front-end (not included in this repository).

## `output_files_7aug/` and `output_files_9aug/`

Two dated snapshots of simulation run outputs, one per corridor
(`p_g_krdl_ktv_2days`, `p_g_ktv_psa_2days`, `p_g_network_2days`, `p_g_sprd_vzm_2days`):

- **`output_files_7aug/`** — only the `.xlsx` schedule/report files; no chart PDFs or
  animator JSON yet, suggesting those two output types were added to the pipeline after
  Aug 7.
- **`output_files_9aug/`** — the current/complete set per corridor: the `.xlsx` report
  (3-sheet workbook, see [simulation-engine.md](simulation-engine.md)), a
  `*_animator.json`, and a `*_time_distance_chart.pdf`.

## `animator_input_files/`

Currently empty — presumably a planned/future location for animator-tool *inputs*, as
distinct from the `*_animator.json` outputs currently written into `output_files_*`.
