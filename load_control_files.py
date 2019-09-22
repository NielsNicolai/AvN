# Read data from the control files: Helper function
def get_ctrl_data(files):
    ctrl_df = None
    for file in files:
        temp_df = pd.read_csv(file)
        list_of_cols = list(temp_df.columns)
        list_of_cols[0] = 'time'
        temp_df.columns = list_of_cols
        temp_df.set_index('time', inplace=True)
        if ctrl_df is None:
            ctrl_df = temp_df
        else:
            ctrl_df = pd.concat([ctrl_df, temp_df], sort=True)
    return ctrl_df