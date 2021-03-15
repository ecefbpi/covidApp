# -*- coding: UTF-8 -*-
import os
import ezodf
import pandas as pd
import datetime
import requests
import json
import sys
import clock

# === GLOBAL VARIABLES ===

CCAA_DICT = {'AN': 'Andalucía', 'AR': 'Aragón', 'AS': 'Principado de Asturias', 'CN': 'Canarias',
              'CB': 'Cantabria',
              'CM': 'Castilla-La Mancha', 'CL': 'Castilla y León', 'CT': 'Cataluña', 'EX': 'Extremadura',
              'GA': 'Galicia', 'IB': 'Islas Baleares', 'RI': 'La Rioja', 'MD': 'Comunidad de Madrid',
              'MC': 'Región de Murcia', 'NC': 'Comunidad Foral de Navarra', 'PV': 'País Vasco',
              'VC': 'Comunidad Valenciana', 'CE': 'Ciudad Autónoma de Ceuta', 'ML': 'Ciudad Autónoma de Melilla'}

CCAA_PROV_DICT = {'AN': ['AL', 'CA', 'CO', 'GR', 'H', 'J', 'MA', 'SE'],'AR': ['HU', 'TE', 'Z'],'AS': ['O'],
                          'CN': ['GC', 'TF'],'CB': ['S'],'CM': ['AB', 'CR', 'CU', 'GU','TO'],
                          'CL': ['AV', 'BU', 'LE', 'P', 'SA', 'SG', 'SO', 'VA', 'ZA'],'CT':['B', 'GI', 'L', 'T'],
                          'EX': ['BA', 'CC'],'GA': ['C', 'LU', 'OR','PO'],'IB': ['PM'],'RI': ['LO'],'MD': ['M'],
                          'MC': ['MU'],'NC': ['NA'],'PV': ['BI', 'SS', 'VI'],'VC': ['V'],'CE': ['CE'],'ML': ['ME']}

CCAA_TO_STANDARD = {'Andalucía': 'AN', 'Aragón': 'AR', 'Asturias': 'AS', 'Baleares': 'IB', 'Canarias': 'CN',
                    'Cantabria': 'CB', 'Castilla y Leon': 'CL', 'Castilla La Mancha': 'CM', 'Cataluña': 'CT',
                    'C. Valenciana': 'VC', 'Extremadura': 'EX', 'Galicia': 'GA', 'La Rioja': 'RI', 'Madrid': 'MD',
                    'Murcia': 'MC', 'Navarra': 'NC', 'País Vasco': 'PV', 'Ceuta': 'CE', 'Melilla': 'ML', }

def check_path():
    TMPDIR = None
    DATADIR = None
    pwd = os.getcwd()

    if sys.platform.startswith('linux'):
        if pwd.split('/')[-1] == 'tasks':
            pwd = pwd.rstrip('tasks')
            files = os.listdir('..')
        else:
            files = os.listdir('.')
    elif sys.platform.startswith('win'):
        if pwd.split('\\')[-1] == 'tasks':
            pwd = pwd.strip('tasks')
            files = os.listdir('..')
        else:
            files = os.listdir('.')

    if pwd == '/home/ecefbpi' and 'app.py' not in files:
        TMPDIR = '/home/ecefbpi/mysite/tmp/'
        DATADIR = '/home/ecefbpi/mysite/data/'
        return True, TMPDIR, DATADIR
    elif 'app.py' in files and 'layout.py' in files:
        if 'data' in files and 'tmp' in files:
            TMPDIR = pwd + '/tmp/'
            DATADIR = pwd + '/data/'
            return True, TMPDIR, DATADIR
        else:
            return False, TMPDIR, DATADIR
    else:
        return False, TMPDIR, DATADIR


def download_csv():
    for file in os.listdir(DATADIR):
        if os.path.isfile(DATADIR + file):
            if file != 'poblacion_ccaa_2020.csv':
                os.remove(DATADIR + file)

    url1 = 'https://cnecovid.isciii.es/covid19/resources/casos_tecnica_ccaa.csv'
    url2 = 'https://cnecovid.isciii.es/covid19/resources/casos_hosp_uci_def_sexo_edad_provres.csv'
    url3 = 'https://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/vacunaCovid19.htm'

    r1 = requests.get(url1)
    r2 = requests.get(url2)
    r3 = requests.get(url3)

    fecha = r3.text.split('.ods')[1].split('Informe_GIV_Comunicacion_')[1]
    vacunas_file_name = 'Informe_GIV_Comunicacion_' + fecha + '.ods'
    url4 = 'https://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/documentos/' + vacunas_file_name
    r4 = requests.get(url4)

    open(DATADIR + 'casos_tecnica_ccaa.csv', 'wb').write(r1.content)
    open(DATADIR + 'casos_hosp_uci_def_sexo_edad_provres.csv', 'wb').write(r2.content)
    open(DATADIR + vacunas_file_name, 'wb').write(r4.content)

    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    if os.path.isfile(DATADIR + 'last_downloaded_data.txt'):
        os.remove(DATADIR + 'last_downloaded_data.txt')
    with open(DATADIR + 'last_downloaded_data.txt', 'w') as fout:
        fout.write(now_str)


def convert_to_int(str_total):
    return int(str_total.replace('.',''))

def read_ods_vacunas():
    vacunas_file = False
    vacunas_file_name = None

    for file in os.listdir(DATADIR):
        if '.' in file:
            file_name = file.split('.')[0]
            file_extension = file.split('.')[1]
            if file_extension == 'ods':
                if 'Informe_Comunicacion' in file_name:
                    vacunas_file_name = file
                    vacunas_file = True

    if vacunas_file:
        doc = ezodf.opendoc(DATADIR + vacunas_file_name)
        sheet = doc.sheets[0]
        data = dict()
        for i, row in enumerate(sheet.rows()):
            if i != 0:
                data[i] = list()
                for j, cell in enumerate(row):
                    if j == 0:
                        if cell.value is not None:
                            if cell.value.rstrip() in CCAA_TO_STANDARD.keys():
                                cell_value = CCAA_TO_STANDARD[cell.value.rstrip()]
                    else:
                        try:
                            cell_value = float(cell.value)
                        except:
                            cell_value = cell.value
                    data[i].append(cell_value)

        df = pd.DataFrame.from_dict(data, orient='index')
        df_tmp = df[[0, 1, 2, 3, 4, 5, 6, 7]].copy()
        df_tmp.rename(columns={0: 'ccaa', 1: 'entregado_Pfizer', 2: 'entregado_Moderna', 3: 'entregado_AstraZeneca',
                               4: 'entregado_total', 5: 'administrado',6: 'porct_sobre_entregado',
                               7: 'personas_vacunadas_dos_dosis'},
                      inplace=True)
        df_vacunas = df_tmp.dropna(how='any', axis=0)

        df_pob = pd.read_csv(DATADIR + "poblacion_ccaa_2020.csv", sep=';', converters={'total': convert_to_int})
        df_pob.rename(columns={'total': 'poblacion'}, inplace=True)

        df_final_vacunas = pd.merge(df_vacunas, df_pob, how='outer')
        return df_final_vacunas
    else:
        return None


def read_csv_to_df_in_disk():

    if not os.path.isdir(TMPDIR):
        os.mkdir(TMPDIR)
    else:
        files = os.listdir(path=TMPDIR)
        if len(files) != 0:
            for file in files:
                os.remove(TMPDIR + file)

    # df
    df_ccaa = pd.read_csv(DATADIR + "casos_tecnica_ccaa.csv", dtype={'ccaa_iso': 'category'})

    df_ccaa['num_casos_prueba_otras'] = df_ccaa['num_casos_prueba_test_ac'] + df_ccaa['num_casos_prueba_ag'] + \
                                        df_ccaa['num_casos_prueba_elisa'] + df_ccaa['num_casos_prueba_desconocida']

    df = df_ccaa[['ccaa_iso', 'fecha', 'num_casos', 'num_casos_prueba_pcr', 'num_casos_prueba_otras']].copy()
    df.rename(columns={'ccaa_iso': 'ccaa'}, inplace=True)

    #df_hosp
    df_hosp = pd.read_csv(DATADIR + "casos_hosp_uci_def_sexo_edad_provres.csv", dtype={'ccaa_iso': 'category'})

    #df_muertes
    df_muertes = df_hosp[['fecha', 'provincia_iso', 'num_def']].copy()
    df_muertes.rename(columns={'provincia_iso': 'prov', 'num_def': 'muertes'}, inplace=True)

    #df_vacunas
    df_vacunas = read_ods_vacunas()

    #ccaa options
    ccaas = df['ccaa'].unique().tolist()
    dictionary_options = [
        {'label': CCAA_DICT[i].rstrip(),
         'value': i
         } for i in ccaas if i is not None
    ]
    dictionary_options.insert(0, {'label': 'ALL', 'value': 'ALL'})

    with open(TMPDIR + 'df.txt', 'w') as df_out:
        json.dump(df.to_dict(), df_out)

    with open(TMPDIR + 'df_muertes.txt', 'w') as df_muertes_out:
        json.dump(df_muertes.to_dict(), df_muertes_out)

    with open(TMPDIR + 'df_hosp.txt', 'w') as df_hosp_out:
        json.dump(df_hosp.to_dict(), df_hosp_out)

    with open(TMPDIR + 'df_vacunas.txt', 'w') as df_vacc_out:
        json.dump(df_vacunas.to_dict(), df_vacc_out)

    with open(TMPDIR + 'ccaa_options.txt', 'w') as ccaa_options_out:
        json.dump(dictionary_options, ccaa_options_out)

    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    with open(TMPDIR + 'last_loaded_data.txt', 'w') as f_loaded_out:
        f_loaded_out.write(now_str)

if __name__ == "__main__":
    result, TMPDIR, DATADIR = check_path()
    start = clock.now()
    if result:
        download_csv()
        read_csv_to_df_in_disk()
        print("Executed in " + str(clock.now() - start) + " seconds")
    else:
        timestamp_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('download_error_' + timestamp_str + '.txt', 'w') as f_error_out:
            f_error_out.write("Problems to download info: " + timestamp_str)