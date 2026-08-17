import pandas as pd

def filter_df_by_date_window(df_simulated, start_date_str, window_hours=23.5):
    """
    Clips each train's journey to the time window.
    - If a train has ANY stations within the window → include only those stations
    - Stations outside the window are blanked out
    - If no stations fall in window → train excluded entirely
    """
    start_dt = pd.Timestamp(start_date_str)
    end_dt   = start_dt + pd.Timedelta(hours=window_hours)

     # ── check if date is within data range ────────────────────────────────
    all_arr    = pd.to_datetime(df_simulated['Arr1'], errors='coerce').dropna()
    data_start = all_arr.min()
    data_end   = all_arr.max()

    if start_dt < data_start or start_dt > data_end:
        print(f'Date {start_dt} not in data — available range: {data_start} → {data_end}')
        return pd.DataFrame()

    print(f'Window: {start_dt} → {end_dt}')

    stn_cols  = [c for c in df_simulated.columns if c.startswith('Stn')]
    arr_cols  = [c for c in df_simulated.columns if c.startswith('Arr')]
    dept_cols = [c for c in df_simulated.columns if c.startswith('Dept')]

    clipped_rows = []

    for _, row in df_simulated.iterrows():
        new_row = row.copy()
        has_any = False

        for stn_col, arr_col, dept_col in zip(stn_cols, arr_cols, dept_cols):
            stn  = row[stn_col]
            arr  = pd.to_datetime(row[arr_col],  errors='coerce')
            dept = pd.to_datetime(row[dept_col], errors='coerce')

            if pd.isna(stn) or stn == '':
                continue

            arr_in  = pd.notna(arr)  and (start_dt <= arr  <= end_dt)
            dept_in = pd.notna(dept) and (start_dt <= dept <= end_dt)

            if arr_in or dept_in:
                has_any = True
            else:
                new_row[stn_col]  = ''
                new_row[arr_col]  = pd.NaT
                new_row[dept_col] = pd.NaT

        if has_any:
            clipped_rows.append(new_row)

    df_filtered = pd.DataFrame(clipped_rows).reset_index(drop=True)
    print(f'Total trains with stops in window: {len(df_filtered)}')
    return df_filtered


def get_formatted_data_from_df(df, start_dt, end_dt):

    formatted_schedules = {}
    chart_date = start_dt.strftime("%d-%m-%Y")

    for _, row in df.iterrows():

        tid = str(row['Train_ID'])
        t_type = row['Train_Type'].lower()

        stop_list = []

        i = 1
        while f'Stn{i}' in df.columns:

            stn = row.get(f'Stn{i}')
            arr = row.get(f'Arr{i}')
            dep = row.get(f'Dept{i}')

            if pd.isna(stn):
                i += 1
                continue

            stn = stn.lower()

            # 🔥 FIX: convert to datetime
            if pd.notna(arr):
                arr = pd.to_datetime(arr)

            if pd.notna(dep):
                dep = pd.to_datetime(dep)

            # handle arr = dep
            if pd.notna(arr) and pd.notna(dep) and arr == dep:
                if start_dt <= arr <= end_dt:
                    stop_list.append((arr, stn))
            else:
                if pd.notna(arr) and start_dt <= arr <= end_dt:
                    stop_list.append((arr, stn))

                if pd.notna(dep) and start_dt <= dep <= end_dt:
                    stop_list.append((dep, stn))

            i += 1

        if len(stop_list) < 2:
            continue

        stop_list = sorted(stop_list, key=lambda x: x[0])

        formatted_schedules[tid] = {
            'stops': stop_list,
            'type': t_type
        }

    return formatted_schedules, chart_date