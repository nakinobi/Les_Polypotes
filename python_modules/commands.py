import pandas as pd
import folium
import json
from IPython.display import HTML
import base64
import ast
import threading
import numpy as np

#display functions
def center_widget(widget_list):
    """ This was working fine
#         align_horiz = w.Layout(display='flex',
#                 flex_flow='column',
#                 align_items='center',
#                 width='100%')


#         box_list = [self.screen_title, self.username_entry, self.userpw_entry, self.connect_button]

#         sub_box_list = [self.create_account_but, self.reset_pw]
#         sub_box = w.HBox(children=sub_box_list)
#         box_list.append(sub_box)

#         boxes = w.HBox(children=box_list,layout=box_layout)
"""
    import ipywidgets as w
    align_horiz = w.Layout(display='flex',
                           flex_flow='column',
                           align_items='center',
                           width='100%')
    align_verti = w.Layout(display='flex',
                           flex_flow='row',
                           align_items='center',
                           width='100%')



    box = []
    for row in widget_list:
        if type(row) == type([]):
            box.append(w.HBox(children=row))
        else:
            box.append(row)

    boxes = w.HBox(children=box, layout=align_horiz)
    #boxes = w.VBox(children=[boxes], layout=align_verti)

    return boxes

def display_table(df, title):
    html = "<h2 style='padding-top: 30px'>"+title+"</h2>"

    html += "<table>"
    html+= "<thead><tr>"
    for col in df.columns:
        html += "<th><h3>%s</h3><th>" % (col)
    html+= "</tr></thead>"

    html+="<tbody>"
    for row in df.index:
        html += "<tr>"
        for col in df.columns:
            field = df.loc[row, col]
            html += "<td><h5>%s</h5><td>"%(field)
        html += "</tr>"
    html+="</tbody>"
    html += "</table>"
    return HTML(html)

def table_filter(bdd, filtre):
    tmp = pd.DataFrame(columns = bdd.columns)
    for col in bdd.columns:
        if not col in ['IS_POLYTECH', 'LAT', 'LONG', "IS_BANNED", "USER_PW", "TOKEN"]:
            tmp = tmp.append(bdd[bdd[col] == filtre])
            #tmp = tmp.append(bdd.query( str(col) + " == '"+ str(filtre) + "'" ))

    return tmp



# Action on external devices
def send_token_email(receiver, root, config, content_id):
    def generate_token():
        from random import choice
        from string import hexdigits

        token = [choice(hexdigits) for i in range(config['token_length'])]
        token = "".join(token)
        return token

    def send_mail(receiver, root, config, content_id, token):
        import smtplib, ssl
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText


        # Get the default mail message
        if content_id == 'reset':
            filepath = root+config["def_content_reset_pw_path"]
        elif content_id == 'create':
            filepath = root+config["def_content_create_account_path"]
        else:
            print("argument for function 'send_token_email' is incorrect")
            return 0
        f = open(filepath, 'r', encoding='utf-8')
        content = f.read()
        content = content.replace("#token#", str(token))
        f.close()

        # get info.polypotes@gmail.com id and pw
        filepath = root+config["def_content_mail_id_path"]
        f = open(filepath, 'r')
        ids = f.read()
        ids = ids.split('\n')
        f.close()

        sender, passwd = ids[0], ids[1]
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = receiver
        if content_id == 'reset':
            message["Subject"] = "Réinitialisation de mot de passe Les Polypotes"
        if content_id == 'create':
            message["Subject"] = "Création de compte Les Polypotes"

        message.attach(MIMEText(content, "plain"))
        message = message.as_string()

        # Log in to server using secure context and send email
        context = ssl.create_default_context()
        vu = None
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, passwd)
            vu = server.sendmail(sender, receiver, message)

    token = generate_token()

    x = threading.Thread(target=send_mail, args=(receiver, root, config, content_id, token,))
    x.start()

    bdd = refresh(root)
    bdd.loc[receiver, "TOKEN"] = token
    filepath = root+config["def_bdd_path"]
    bdd.to_json(filepath)


    return token

def refresh(root, arg=None):
    if type(arg) == type(pd.DataFrame()):
        filepath = '\\'.join([root, 'data', 'BDD.json'])
        arg.to_json(filepath)
        return
    if arg == None:
        bdd_filepath = '\\'.join([root, 'data', 'BDD.json'])
        bdd = pd.read_json(bdd_filepath)
        if not "@gmail" in 'tampon'+str(bdd.index.values[0]):
            bdd = bdd.set_index("USER_MAIL") # Load the DB before
        return bdd

def read_logs(path):
    logs_filepath = '\\'.join([path, 'data', 'BDD.json'])
    logs = pd.read_json(logs_filepath)
    return logs

def add_log(root, update_dic, timestp):
    filepath = root + "\\data\\Server_logs.json"
    log = pd.read_json(filepath)
    if not "/" in 'tampon' + str(log.index.names[0]):
        log = log.set_index("TIMESTAMP")  # Load the DB before
    error_count = 0
    for key in update_dic.keys():
        if key in log.columns:
            tmp_df = pd.DataFrame(index=[timestp], columns=log.columns, data=update_dic)
            if len(tmp_df.index.names) < 5:
                tmp_df.index.names = ["TIMESTAMP"]
            log = log.append(tmp_df)
        else:
            print(key, ',not found in log.columns')
            error_count += 1
    return error_count




def add_user(bdd, user_info):
    df = pd.DataFrame(index=[user_info['ID']], columns=bdd.columns, data=user_info)
    bdd = bdd.append(df)
    return bdd

def update_user(bdd, user_info, usr_id):
    for key_col in user_info.keys():
        bdd.loc[usr_id, key_col] = user_info[key_col]

    return bdd,0




# Read External infos
def read_tuto_screen(root):
    filepath = '\\'.join([root, 'data', 'default', "tuto_screen.txt"])
    f = open(filepath, 'r', encoding='utf-8')
    content = f.read()
    tuto = ast.literal_eval(content)
    return tuto

def read_config(root):
    filepath = '\\'.join([root, 'data', 'default', 'config.dic'])
    f = open(filepath, 'r')
    content = f.read()
    f.close()
    config = ast.literal_eval(content)
    return config

def read_questions(root):
    filepath = '\\'.join([root, 'data', 'default', 'questions.txt'])
    f = open(filepath, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    questions = {}
    def eval_q(string):
        q = line.split('<')
        q = q[1].split('>')
        return q[0]

    for line in content.split('\n'):
        if '#question1' in line:
            questions.update({'q1' : eval_q(line)})
        if '#question2' in line:
            questions.update({'q2' : eval_q(line)})
        if '#question3' in line:
            questions.update({'q3' : eval_q(line)})

    return questions

def read_inscr_form(root):
    filepath = '\\'.join([root, 'data', 'default', 'inscription_form_opt.txt'])
    f = open(filepath, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    out = ast.literal_eval(content)
    return out

def read_communes(root):
    filepath = '\\'.join([root, 'data', 'geographie', 'france', "liste_communes.csv"])
    df = pd.read_csv(filepath, sep=";", encoding='utf-8')
    #df[["codes_postaux", "latitude", "longitude"]] = df[["codes_postaux", "latitude", "longitude"]].apply(pd.to_numeric) used to force numeric values but doesnt recognize - in front of a negative number
    df = df.set_index("codes_postaux")
    return df

def read_liste_pays_monde(root):
    filepath = '\\'.join([root, 'data', 'geographie', "liste_pays_monde.csv"])
    df = pd.read_csv(filepath, sep=";", encoding='utf-8')
    df = df.filter(like='oui', axis=0)
    return df



# Functions for pages
def check_mail_domain(mail, config):
    for mail_domain in config['allowed_mail_domain']:
        if mail_domain in mail and len(mail) > len(mail_domain):
            return True
    return False

def check_answers(answers):
    check = {}
    if 'jaja' in answers['a1'].lower():
        check.update({'a1':True})
    else:
        check.update({'a1': False})

    if 'make' in answers['a2'].lower() and 'move' in answers['a2']:
        check.update({'a2':True})
    else:
        check.update({'a2': False})

    if 'tigresse' in answers['a3'].lower():
        check.update({'a3':True})
    else:
        check.update({'a3': False})

    return check

def find_latlong(df, code_postal):
    code_postal = int(code_postal)

    if code_postal in df.index:
        lat  = df.loc[code_postal, "latitude"]
        lat = lat.astype('float64')
        long = df.loc[code_postal, 'longitude']
        long = long.astype('float64')
        ret = True
    else:
        code_postal = int(int(code_postal/100) * 100)
        if code_postal in df["codes_postaux"]:
            lat = df.loc[code_postal, "latitude"]
            lat = lat.astype('float64')
            long = df.loc[code_postal, 'longitude']
            long = long.astype('float64')
            ret = True
        else:
            lat, long = 0,0
            ret = False

    if ret:
        if type(lat) == type(pd.Series()):
            lat = lat.mean(axis=0)
            long = long.mean(axis=0)


    return lat, long, ret

def is_empty(field):
    try:
        if len(str(field)) > 2:
            return False
        else:
            return True
    except:
        return True


# Main page functions
def create_coord_table(bdd):
    # Drops columns we don't want people to see
    bdd_disp = bdd.drop(columns=["IS_BANNED", "USER_PW", "TOKEN", "IS_POLYTECH", "LAT", "LONG"])

    # change columns names
    rename_dic = {
        "USER_ID": "POLYPOTES",
        "PSEUDO_FB": "PSEUDO FB",
    }
    bdd_disp = bdd_disp.rename(columns=rename_dic)

    # Convert the Date from timestamp
    bdd_disp['INSCRIPTION'] = pd.to_datetime(bdd_disp['INSCRIPTION'], unit='ms')
    bdd_disp['INSCRIPTION'] = bdd_disp['INSCRIPTION'].dt.strftime('%d/%m/%Y')

    # Convert Years to int number
    bdd_disp['PROMO'] = bdd_disp['PROMO'].astype(np.int)

    # Shorten the Ville and Description
    columns_to_cut = ['VILLE', 'COMMENTAIRE']
    for col in columns_to_cut:
        for ind in bdd_disp.index:
            if len('a' + str(bdd_disp.loc[ind, col])) > 25:
                bdd_disp.loc[ind, col] = ''.join(list(bdd_disp.loc[ind, col])[:26]) + '...'

    # self.coord_table = w.HTML(tabulate.tabulate(bdd_disp, headers=bdd_disp.columns, tablefmt="html"))
    out = display_table(bdd_disp, "Coordonnées")

    return out

def create_map(bdd, Map):
    polytech_list = ["Polytech Lille",
                     "Polytech Sorbonne",
                     "Polytech Paris-Saclay",
                     "Polytech Nancy",
                     "Polytech Orléans",
                     "Polytech Tours",
                     "Polytech Angers",
                     "Polytech Nantes",
                     "Polytech Annecy-Chambéry",
                     "Polytech Lyon",
                     "Polytech Clermont-Ferrand",
                     "Polytech Grenoble",
                     "Polytech Nice",
                     "Polytech Marseille",
                     "Polytech Montpellier"]
    polytech_color = ["red",
                      "blue",
                      "green",
                      "purple",
                      "orange",
                      "darkred",
                      "lightred",
                      "beige",
                      "darkblue",
                      "darkgreen",
                      "cadetblue",
                      "darkpurple",
                      "white",
                      "pink",
                      "lightblue",
                      "dark"]

    # MARKER
    for ind in bdd.index:
        if (bdd.loc[ind, 'ECOLE']):
            Indcolor = polytech_color[int(polytech_list.index(bdd.loc[ind, 'ECOLE']))]
        else:
            Indcolor = "dark"

        text = str(bdd.loc[ind, 'USER_ID']) + '<br> Promo: ' + str(bdd.loc[ind, 'PROMO']) + '<br>' + str(
            bdd.loc[ind, 'ECOLE']) + '<br>' + str(bdd.loc[ind, 'COMMENTAIRE'])
        test = folium.Html((text), script=True)
        popupind = folium.Popup(test, max_width=2650)

        try:
            tmp = folium.Marker(location=[bdd.loc[ind, 'LAT'], bdd.loc[ind, 'LONG']],
                          popup=popupind,
                          tooltip='<strong>' + str(bdd.loc[ind, 'USER_ID']) + '</strong>',
                          # popup=bdd.loc[ind, 'USER_ID'],
                          icon=folium.Icon(color='cadetblue', icon_color=Indcolor, icon="fa-male", prefix='fa'))
            tmp.add_to(Map)
        except:
            continue

    # CIRCLE
    bdd_Grp = bdd['VILLE'].value_counts()
    for grp in bdd_Grp.index:
        Latgrp = bdd.loc[lambda bdd: bdd['VILLE'] == str(grp), 'LAT']
        longgrp = bdd.loc[lambda bdd: bdd['VILLE'] == str(grp), 'LONG']

        texttooltip = '<strong>Ville: </strong>' + str(grp) + '<br><strong>Nb de Polypotes: </strong>' + str(
            bdd_Grp.loc[grp])
        text = texttooltip
        gens = bdd.loc[lambda bdd: bdd['VILLE'] == str(grp), 'USER_ID']

        for ind in gens:
            text = text + '<br>' + '  - ' + str(ind)
        test = folium.Html((text), script=True)
        popupind = folium.Popup(test, max_width=500, width=700)

        try:
            tmp2 = folium.vector_layers.Circle(location=[Latgrp[:1], longgrp[:1]],
                                        radius=int(bdd_Grp.loc[grp]) * 1000,
                                        tooltip=texttooltip,
                                        fill=True,
                                        popup=popupind)
            tmp2.add_to(Map)
        except:
            continue

    return Map



# Other
def create_download_link(password=""):
    if password != "BNP":
        print("INCORECT PASSWORD - Contact administratore")
        return
    with open('polypote.json', 'rb') as outfile:
            global_result = json.load(outfile)
    max_length = max([len(global_result[x]) for x in global_result.keys()])
    for k in global_result.keys():
        if len(global_result[k]) != max_length:
            global_result[k] += [""]*(max_length- len(global_result[k]))

    df = pd.DataFrame.from_dict(global_result)
    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    title = "Download polypote file"
    filename = "data.csv"
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    html = html.format(payload=payload,title=title,filename=filename)
    return HTML(html)

def add_pote(city="L'ARBRESLE", coord="45.8333,4.6167", name="alex"):
    with open('polypote.json', 'r') as outfile:
            global_result = json.load(outfile)
    key = city+"|"+coord.replace(" ","")
    if key in global_result:
        global_result[key] += [name]
    else:
        global_result[key] = [name]
    with open('polypote.json', 'w') as outfile:
        json.dump(global_result, outfile, indent=4)
    return "polypote added - please refresh page"

def display_map():
    with open('polypote.json', 'r') as outfile:
            global_result = json.load(outfile)
    folium_map = folium.Map(location = [48.856578,2.351828],
                            zoom_start = 6,
                            tiles='CartoDB dark_matter')
    for key in global_result:
        city = key.split("|")[0]
        latitude = float(key.split("|")[1].split(",")[0])
        logitude = float(key.split("|")[1].split(",")[1])
        text = city + " " + str(len(global_result[key])) + " polypote(s) : " + ", ".join(global_result[key])
        folium.Marker([latitude, logitude], popup = text).add_to(folium_map)
    return folium_map
















