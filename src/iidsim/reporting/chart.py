import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
from datetime import datetime, timedelta

matplotlib.rcParams['pdf.fonttype'] = 42


def compute_dynamic_figsize(order, start_win, end_win):
    WIDTH_PER_HOUR     = 2      # wider chart
    HEIGHT_PER_STATION = 1      # taller chart
    MIN_WIDTH          = 30
    MIN_HEIGHT         = 14 

    total_hours = (end_win - start_win).total_seconds() / 3600 
    n_stations  = len(order)

    fig_width  = max(MIN_WIDTH,  total_hours * WIDTH_PER_HOUR)
    fig_height = max(MIN_HEIGHT, n_stations  * HEIGHT_PER_STATION)

    return fig_width, fig_height


def _find_best_label_position(times, y_vals, placed_labels, start_win, end_win):
    """
    Find the point on the train path that is:
    1. Within the visible time window
    2. Furthest from all already placed labels
    Returns (best_time, best_y)
    """
    best_time = None
    best_y    = None
    best_dist = -1

    for t, y in zip(times, y_vals):
        if not (start_win <= t <= end_win):
            continue

        if not placed_labels:
            return t, y  # first label -- return first valid point

        min_dist = float('inf')
        for px, py, _ in placed_labels:
            dt_sec   = abs((t - px).total_seconds())
            dy       = abs(y - py)
            dist     = (dt_sec / 60) + dy * 10  # combined distance metric
            min_dist = min(min_dist, dist)

        if min_dist > best_dist:
            best_dist = min_dist
            best_time = t
            best_y    = y

    return best_time, best_y


def _place_label(ax, x, y, text, color, placed_labels,
                 fontsize=6.5, start_win=None, end_win=None,
                 total_dist=None, label_index=0):
    """
    Place label above or below alternately.
    Left or right based on time position in window.
    """
    # count nearby labels for additional offset
    X_WINDOW_SECONDS = 600
    Y_BUCKET         = 2.0
    nearby = [p for p in placed_labels
              if abs((x - p[0]).total_seconds()) < X_WINDOW_SECONDS
              and abs(y - p[1]) < Y_BUCKET]
    n = len(nearby)

    # alternate above/below by train index
    go_below = (label_index % 2 == 0)

    # left/right based on time position
    x_mid   = start_win + (end_win - start_win) / 2
    go_left = x > x_mid

    y_offset     = -(2.5 + n * 3.0) if go_below else (2.5 + n * 3.0)
    x_offset_min = -(6 + n * 4)     if go_left  else (1 + n * 3)

    label_x = x + timedelta(minutes=x_offset_min)
    label_y = y + y_offset

    va = 'top'   if go_below else 'bottom'
    ha = 'right' if go_left  else 'left'

    ax.annotate(
        text,
        xy=(x, y),
        xytext=(label_x, label_y),
        xycoords='data',
        textcoords='data',
        fontsize=fontsize,
        color=color,
        fontweight='normal',       # thin -- not bold
        va=va,
        ha=ha,
        annotation_clip=False,
        arrowprops=dict(
            arrowstyle='-',        # simple line no arrowhead
            color=color,
            lw=0.6,                # thin connector line
            connectionstyle='arc3,rad=0.0'
        ),
    )

    placed_labels.append((x, y, text))


def plot_railway_chart(order, segs, schedules, chart_date,
                       filename="master_chart.pdf",
                       start_win=None, end_win=None):

    # 1. Cumulative distances
    station_dist_map = {order[0]: 0.0}
    current_dist = 0.0
    for i in range(len(order) - 1):
        pair = (order[i], order[i + 1])
        current_dist += segs.get(pair, 10.0)
        station_dist_map[order[i + 1]] = current_dist

    # 2. Collect all timestamps
    all_dt = []
    for tid, data in schedules.items():
        for t, stn in data['stops']:
            all_dt.append(t)

    if not all_dt:
        print("No data to plot")
        return

    # 3. Time window
    if start_win is None:
        start_win = min(all_dt)
    if end_win is None:
        end_win = max(all_dt)

    total_dist = max(station_dist_map.values())

    fig_w, fig_h = compute_dynamic_figsize(order, start_win, end_win)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    ax.set_ylim(-8, total_dist + 8)
    ax.set_xlim(start_win, end_win)  # set BEFORE label placement

    # 4. Plot trains
    placed_labels = []
    for train_idx, (tid, data) in enumerate(schedules.items()):

        stops      = data['stops']
        train_type = data['type']

        times  = [t for t, s in stops]
        y_vals = [
            station_dist_map[s] if not isinstance(s, int)
            else station_dist_map[order[s]]
            for t, s in stops
        ]

        color = 'green' if train_type == 'p' else '#FF6B6B'

        # draw train line -- thin
        ax.plot(times, y_vals,
                lw=0.5,
                marker='.',
                markersize=1.5,
                color=color,
                alpha=0.85)

        # find best uncrowded point on the line for label
        best_t, best_y = _find_best_label_position(
            times, y_vals, placed_labels, start_win, end_win
        )

        if best_t is not None:
            _place_label(
                ax,
                best_t,
                best_y,
                tid,               # just train id -- no "Tr " prefix to save space
                color,
                placed_labels,
                fontsize=6.5,
                start_win=start_win,
                end_win=end_win,
                total_dist=total_dist,
                label_index=train_idx,
            )

        # direction arrow at last visible point
        if len(times) > 1:
            visible = [(t, y) for t, y in zip(times, y_vals)
                       if start_win <= t <= end_win]
            if len(visible) >= 2:
                ax.annotate(
                    '',
                    xy=(visible[-1][0], visible[-1][1]),
                    xytext=(visible[-1][0] - timedelta(minutes=3), visible[-1][1]),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.0)
                )

    # 5. Axes formatting
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))

    ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[10, 20, 30, 40, 50]))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%M'))

    ax.tick_params(axis='x', which='major', colors='green', labelsize=14, pad=15)
    ax.tick_params(axis='x', which='minor', colors='black', labelsize=9)

    ax.set_yticks(list(station_dist_map.values()))
    ax.set_yticklabels([s.upper() for s in order],
                       fontweight='normal', fontsize=11)


    # to increase the thickness of this lines change the values here 
    ax.grid(True, which='major', ls=':', alpha=0.7, lw=0.8)
    ax.grid(True, which='minor', ls=':', alpha=0.4, lw=0.5)

    # 6. Title
    title = (
        f"Timetable Chart  |  "
        f"SECTION: {order[0].upper()} - {order[-1].upper()}  |  "
        f"DATE: {chart_date}  |  "
        f"WINDOW: {start_win.strftime('%H:%M')} TO {end_win.strftime('%H:%M')}"
    )

    plt.title(title, fontsize=14, pad=15, fontweight='normal')
    plt.tight_layout()
    plt.savefig(filename, format='pdf', bbox_inches='tight', dpi=150)
    plt.close(fig)