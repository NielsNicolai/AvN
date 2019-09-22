## Loading data from a matlab file : Helper functions
# Load these functions before trying to extract data from a .mat file
def mat_to_py(dat_list):
    py_date = []
    for i in range(len(dat_list)):
        # Get the date from the integer part of the matlab time
        py_date.append(datetime.datetime.fromordinal(int(dat_list[i])))
        # Get the hour from decimal part and subtract a year because matlab starts at 0 AD
        # not 1 AD like python time
        py_date[i] += datetime.timedelta(days=dat_list[i]%1) - datetime.timedelta(days = 366)
    return py_date

def look_deeper(array):
    if isinstance(array, np.ndarray) or isinstance(array, list):
        return look_deeper(array[0])
    else:
        return array
    
def df_from_mat_var(filename, var_name):
    struct = scipy.io.loadmat(filename)[var_name][0]
    for i in range(len(struct)):
        matlab_data = {}
        param_from_channel = look_deeper(struct[i][0][0])
        param_name = var_name + ' ' + param_from_channel.split(']')[0] + ']'
        matlab_data['time'] = mat_to_py(struct[i][1][:,0])
        matlab_data[param_name] = struct[i][1][:,1]
        df_new = pd.DataFrame.from_dict(matlab_data)
        df_new.set_index('time', inplace=True)
        if i == 0:
            df_tot = df_new
        else:
            df_tot = df_tot.join(df_new, how='outer')
    return df_tot

def get_mat_variables(filename, varnames):
    df_array = []
    for i in range(len(varnames)):
        df_array.append(df_from_mat_var(filename, varnames[i]))
        if i==0:
            df = df_array[0]
        else:
            df = df.join(df_array[i], how='outer')
    return df


# ## Loading data from a matlab file : Script
#filename = 'data/ANAPRO1.mat'
#names = ['ANAPRO1', 'copilote_august', 'pilote_august']
#df_mat = get_mat_variables(filename, names)
