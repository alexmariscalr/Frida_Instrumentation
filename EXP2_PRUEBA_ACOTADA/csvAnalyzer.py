from collections import Counter
import openpyxl
import csv
import os

# App;Tool;Method;Third_Parties;Loc_Addr;Serv_Addr;URL;Error
path_mitm = 'mitm_connections.csv'

# method;trace;source
path_frida_apps = './frida_apps'

ruta_excel_sdks = 'sdk_index.xlsx'
hoja_sdks = 'Hoja1'
workbook = openpyxl.load_workbook(ruta_excel_sdks)
sheet = workbook[hoja_sdks]
sdks = []


for cell in sheet['G4':'G' + str(sheet.max_row)]:
    sdks.append(cell[0].value)


def get_third_parties(line):
    third_parties = []
    for sdk in sdks:
        if sdk in line:
            third_parties.append(sdk)
    return third_parties


def get_order(third_party, app, trace):
    if third_party in trace:
        if app in trace:
            if trace.index(third_party) < trace.index(app):
                "App antes que third party"
            else:
                "App despues que third party"
        else:
            "Solo third party"
    elif app in trace:
        "Solo app"


# Analizamos el csv de MITM
n_con_dist_mitm = set()
n_con_dist_mitm_request = set()
n_con_dist_mitm_response = set()
n_con_dist_mitm_error = set()

n_con_mitm = 0
n_con_mitm_request = 0
n_con_mitm_response = 0
n_con_mitm_error = 0

sources_mitm_request = Counter()
sources_mitm_response = Counter()
sources_mitm_error = Counter()
sources_mitm = Counter()

destinations_mitm = Counter()
destinations_mitm_request = Counter()
destinations_mitm_response = Counter()
destinations_mitm_error = Counter()

n_con_https = 0
n_con_dist_https = set()
n_con_http = 0
n_con_dist_http = set()

connection_with_known_servers = set()


with open(path_mitm, 'r') as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:

        n_con_mitm += 1
        sources_mitm[row[4]] += 1
        destinations_mitm[row[6]] += 1
        # Acortar url a dominio

        if row[6].startswith("https://"):
            row[6] = row[6].split("//")[0] + "//" + \
                row[6].split("//")[1].split("/")[0]
            n_con_https += 1
            n_con_dist_https.add(tuple(row))
        elif row[6].startswith("http://"):
            row[6] = row[6].split("//")[0] + "//" + \
                row[6].split("//")[1].split("/")[0]
            n_con_http += 1
            n_con_dist_http.add(tuple(row))
        if row[2] == "Request":
            n_con_dist_mitm_request.add(tuple(row))
            n_con_dist_mitm.add(tuple(row))
            n_con_mitm_request += 1
            sources_mitm_request[row[4]] += 1
            destinations_mitm_request[row[6]] += 1
        elif row[2] == "Response":
            n_con_dist_mitm.add(tuple(row))
            n_con_dist_mitm_response.add(tuple(row))
            n_con_mitm_response += 1
            sources_mitm_response[row[4]] += 1
            destinations_mitm_response[row[6]] += 1
        elif row[2] == "Error":
            n_con_dist_mitm.add(tuple(row))
            n_con_dist_mitm_error.add(tuple(row))
            n_con_mitm_error += 1
            sources_mitm_error[row[4]] += 1
            destinations_mitm_error[row[6]] += 1

error_mssg_counter = Counter()
for error in n_con_dist_mitm_error:
    error_mssg_counter[error[7]] += 1


# Analizamos los csvs del path_frida_apps
n_con_frida = 0
n_con_dist_frida = set()
sources_frida = Counter()
third_parties_frida = Counter()
rows_with_third_parties = set()

sources_frida_connect = Counter()
n_con_frida_connect = 0
n_con_dist_frida_connect = set()
third_parties_frida_connect = Counter()

sources_frida_getOutputStream = Counter()
n_con_frida_getOutputStream = 0
n_con_dist_frida_getOutputStream = set()
third_parties_frida_getOutputStream = Counter()

order_trace = Counter()

# CSV: app;method;trace;source
with open('frida_apps/todas_las_conexiones.csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        if len(row) > 0:
            app = row[0]
            method = row[1]
            trace = row[2]
            source = row[3]
            n_con_dist_frida.add(tuple(row))
            n_con_frida += 1
            sources_frida[source] += 1
            third_parties = get_third_parties(trace)

            if method == "java.net.Socket.connect":
                n_con_dist_frida_connect.add(tuple(row))
                sources_frida_connect[source] += 1

            elif method == "java.net.Socket.getOutputStream":
                n_con_dist_frida_getOutputStream.add(tuple(row))
                sources_frida_getOutputStream[source] += 1

            for third_party in third_parties:
                rows_with_third_parties.add(tuple(row))
                third_parties_frida[third_party] += 1

            for sdk in sdks:
                order = get_order(sdk, app, trace)
                order_trace[order] += 1

sources_only_frida = Counter()
sources_only_mitm = Counter()
sources_mitm_and_frida = Counter()
for source in sources_frida:
    if source not in sources_mitm:
        sources_only_frida[source] = sources_frida[source]
    else:
        sources_mitm_and_frida[source] = sources_frida[source]
for source in sources_mitm:
    if source not in sources_frida:
        sources_only_mitm[source] = sources_mitm[source]

sources_frida_and_mitmerror = Counter()
for source in sources_mitm_error:
    if source in sources_frida:
        sources_frida_and_mitmerror[source] = sources_mitm_error[source]

apps_only_frida = Counter()
for source in sources_only_frida:
    for row in n_con_dist_frida:
        if row[3] == source:
            apps_only_frida[row[0]] += 1

res_err_source = 0
req_err_source = 0
res_req_err_source = 0
for errorSource in sources_mitm_error:
    if errorSource in sources_mitm_request:
        if errorSource in sources_mitm_response:
            res_req_err_source += 1
        else:
            req_err_source += 1
    elif errorSource in sources_mitm_response:
        res_err_source += 1


print(" ERR-REQ " + str(req_err_source))
print(" ERR-RES " + str(res_err_source))
print(" ERR-RES-REQ " + str(res_req_err_source))


print("APPS ONLY FRIDA" + str(apps_only_frida))

# NÚMERO DE CONEXTIONES
print("Número de conexiones MITM: " + str(n_con_mitm))
print("Número de conexiones Frida: " + str(n_con_frida))
print("Número de sources MITM: " + str(len(sources_mitm)))
print("Número de sources Frida: " + str(len(sources_frida)))
print("Número de sources MITM & Frida: " + str(len(sources_mitm_and_frida)))
print("Número de sources MITM & !Frida: " + str(len(sources_only_mitm)))
print("Número de sources !MITM & Frida: " +
      str(len(sources_only_frida)) + "\n")

print("Número de sources de MITM error: " + str(len(sources_mitm_error)))
print("Número de sources de MITM error & Frida: " +
      str(len(sources_frida_and_mitmerror)))
print("Sources en error que no estan en requests: " +
      str(len(sources_mitm_error - sources_mitm_request)))
