import connect_datEAUbase

#Load data from datEAUbase
def extract_AvN_from_db(start, end):
    cursor, conn = connect_datEAUbase.create_connection()
    Start = connect_datEAUbase.date_to_epoch(start)
    End = connect_datEAUbase.date_to_epoch(end)

    #Define the requested parameters
    Project = 'pilEAUte'
    Location = ['Primary settling tank effluent','Pilote effluent','Pilote effluent', 'Pilote reactor 4', 'Pilote reactor 5', 'Pilote reactor 4', 'Copilote effluent','Copilote effluent', 'Copilote reactor 4', 'Pilote reactor 5', 'Copilote reactor 4']
    param_list = ['NH4-N','NH4-N','NO3-N', 'DO', 'DO', 'Flowrate (Gas)', 'NH4-N','NO3-N', 'DO', 'DO', 'Flowrate (Gas)']
    equip_list = ['Ammo_005','Varion_002', 'Varion_002', 'AIT-241', 'AIT-251', 'FIT-420', 'Varion_001', 'Varion_001', 'AIT-341', 'AIT-351', 'FIT-450']

    #Extract the specified parameters from the datEAUbase
    extract_list={}
    for i in range(len(param_list)):
        extract_list[i] = {
            'Start':Start,
            'End':End,
            'Project':Project,
            'Location':Location[i],
            'Parameter':param_list[i],
            'Equipment':equip_list[i]
        }

    #Extract the data
    df_db = connect_datEAUbase.extract_data(conn, extract_list)

    df_db.columns = [Location[i]+' '+param_list[i] for i in range(len(Location))]

    # Adjust the values with regards to the units
    df_db = df_db*1000
    
    return df_db