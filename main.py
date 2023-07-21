import base64
import json
from io import BytesIO
from tabulate import tabulate
from datetime import datetime, timedelta

from flask import Flask, request, redirect, url_for, render_template
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from secret import secret_key

from google.cloud import storage
from google.cloud import firestore

from FaceRecognition import FaceRecognition
from User import User

# requires pyopenssl


app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
login = LoginManager(app)
login.login_view = '/static/login.html'
# initialize face recognition class
frec = FaceRecognition()


# palceholder for real face recognition funtion
def fecerec():
    return "wellcome"


@login.user_loader
def load_user(username):
    db = firestore.Client.from_service_account_json(
        'facerecognition2023-58824e4fb3cc.json')
    user = db.collection('user_db').document(username).get()
    if user.exists:
        return User(username)
    return None


@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('/main'))
    username = request.values['u']
    password = request.values['p']

    db = firestore.Client.from_service_account_json(
        'facerecognition2023-58824e4fb3cc.json')
    user = db.collection('user_db').document(username).get()
    if user.exists and user.to_dict()['password'] == password:
        login_user(User(username))
        next_page = request.values['next']
        if not next_page:
            next_page = '/dashboard'
        return redirect(next_page)
    return redirect('/static/login.html')


# doorbell
@app.route('/', methods=['GET'])
@app.route('/main', methods=['GET', 'POST'])
def main():
    return render_template('index.html')


# @app.route('/test', methods=['GET'])
# def test():
#     return redirect(url_for('static', filename='test.html'))


def list_bucket_files():
    # Create a GCS client
    client = storage.Client.from_service_account_json(
        'facerecognition2023-84f934357826.json')
    bucket_name = 'door_bell'

    # Retrieve the bucket
    bucket = client.get_bucket(bucket_name)

    # List the files in the bucket
    files = [blob.name for blob in bucket.list_blobs()]
    # list of the links to the files
    expires = datetime.now() + timedelta(seconds=86400)
    links = [blob.generate_signed_url(expiration=expires)
             for blob in bucket.list_blobs()]

    return files, links


@app.route('/dashboard', methods=['GET'])
@login_required
def load_dashboard():
    # Call the function to fetch the list of files from the GCS bucket
    files, links = list_bucket_files()
    filesProcessed = list()
    for i in range(len(files)):
        # each foto has a name with '<->' as separator
        # the first part is the access time, the second is the name of the person
        foto_split = files[i].split('<->')
        # convert the access time to a datetime object
        accessTime = datetime.strptime(foto_split[0], '%Y_%m_%d__%H_%M_%S')
        # For the name we want to look at permessi.json
        # Create a GCS client
        client = storage.Client.from_service_account_json(
            'facerecognition2023-84f934357826.json')
        bucket_name = 'face_db'
        # Retrieve the bucket
        bucket = client.get_bucket(bucket_name)
        # in the bucket there is a file called permessi.json
        blob = bucket.blob('Permessi.json')
        perm = json.load(BytesIO(blob.download_as_string()))

        for person in perm.keys():
            if person == foto_split[1].replace('.png', ''):
                accessName = perm[person].replace('_', ' ')
                break
            else:
                accessName = foto_split[1].replace('.png', '')
        filesProcessed.append([accessName, accessTime])

    tabulated = tabulate(filesProcessed, tablefmt="html",
                         headers=["Name", "Access Time"])
    # print(tabulated)
    # # iterate over the td elements and add the link to the image
    tabulated_rows = tabulated.split("<tr>")
    for row in range(2, len(tabulated_rows)):
        tabulated_cols = tabulated_rows[row].split("<td>")
        tabulated_cols[1] = f"<a href='{links[row - 2]}'>{tabulated_cols[1]}"
        # rejoin cols
        tabulated_rows[row] = "<td>".join(tabulated_cols)

    # rejoin rows
    tabulated = "<tr>".join(tabulated_rows)

    tabulated = tabulated.replace('<table>', '<table id="accessTable">')

    return render_template('dashboard.html', listaFoto=tabulated)
    # return redirect(url_for('static', filename='dashboard.html'))


@app.route('/dashboard/gest_perm', methods=['GET'])
@login_required
def gest_perm():
    client = storage.Client.from_service_account_json(
        'facerecognition2023-84f934357826.json')
    bucket = client.bucket('face_db')
    blob = bucket.blob('Permessi.json')

    perm = json.load(BytesIO(blob.download_as_string()))

    return render_template('gest_perm_tmp.html', perm=perm)


# per ora l'ho fatto così ma possimo valutare di farlo in un altro modo ad esempio come un pop up
@app.route('/dashboard/gest_perm/add_perm', methods=['GET', 'POST'])
@login_required
def add_perm():
    # se il metodo è get allora carico la pagina
    if request.method == 'GET':
        return render_template('add_perm_tmp.html', nome=json.dumps(""), cognome=json.dumps(""),
                               p=json.dumps(""), image=json.dumps(""))
    # se il metodo è post allora salvo i dati nel db su cloud storage
    else:
        client = storage.Client.from_service_account_json(
            'facerecognition2023-84f934357826.json')
        bucket = client.bucket('face_db')
        blob = bucket.blob('Permessi.json')
        perm = json.load(BytesIO(blob.download_as_string()))
        keys = list(perm.keys())
        # prendo i dati dal form
        nome = request.form['nome']
        cognome = request.form['cognome']
        n_c = nome + "__" + cognome.replace(" ", "_")
        image = request.files.get('image')
        # identificativo prende il nome e le prime TRE lettere del cognome
        identificativo = nome + '_' + cognome.replace(" ", "")[:3]
        # se ci sono più persone con lo stesso nome e cognome aggiungo un numero
        if identificativo in keys:
            identificativo = identificativo + "_" + str(len(cognome))
        while identificativo in keys:
            identificativo = identificativo[:-1] + \
                             str(int(identificativo.split("_")[2]) + 1)
        # se tutti i campi sono stati riempiti
        if nome and image and cognome:
            perm[identificativo] = n_c
            blob.upload_from_string(json.dumps(perm))
            blob = bucket.blob('training/' + identificativo + '.png')
            blob.upload_from_string(
                image.read(), content_type=image.content_type)
            # inizia il processo di encoding del nuovo set di volti
            frec = FaceRecognition()
            frec.encode_known_faces()
            return "saved_add"
        else:
            return "error_add"


@app.route('/dashboard/gest_perm/delete/<p>', methods=['POST'])
@login_required
def delete(p):
    client = storage.Client.from_service_account_json(
        'facerecognition2023-84f934357826.json')
    bucket = client.bucket('face_db')
    blob = bucket.blob('Permessi.json')
    perm = json.load(BytesIO(blob.download_as_string()))
    # cancella la persona dal json
    del perm[p]
    # ricarica il json
    blob.upload_from_string(json.dumps(perm))
    # elimina la foto dal training folder per l'encoding
    blob = bucket.blob('training/' + p + '.png')
    blob.delete()
    return "deleted"


@app.route('/image/<p>')
def get_image(p):
    # get the image data from your database or wherever it is stored
    client = storage.Client.from_service_account_json('facerecognition2023-84f934357826.json')
    bucket = client.bucket('face_db')
    blob = bucket.blob('training/' + p + '.png')
    image_data = blob.download_as_string()
    # convert the image data to base64 encoding
    encoded_image = base64.b64encode(image_data).decode('utf-8')
    # return the encoded image as a JSON response
    return {'image': encoded_image}


@app.route('/dashboard/gest_perm/change/<p>', methods=['GET', 'POST'])
@login_required
def change(p):
    if request.method == 'GET':
        client = storage.Client.from_service_account_json('facerecognition2023-84f934357826.json')
        bucket = client.bucket('face_db')
        blob = bucket.blob('Permessi.json')
        perm = json.load(BytesIO(blob.download_as_string()))
        n_c = perm[p]
        nome = n_c.split("__")[0]
        cognome = n_c.split("__")[1].replace("_", " ")

        return render_template('add_perm_tmp.html', nome=nome, cognome=cognome, p=json.dumps(p))
    # se il metodo è post allora salvo i dati nel db su cloud storage
    else:
        print("ciao")
        client = storage.Client.from_service_account_json('facerecognition2023-84f934357826.json')
        bucket = client.bucket('face_db')
        blob = bucket.blob('Permessi.json')
        perm = json.load(BytesIO(blob.download_as_string()))
        identificativo = p
        # prendo i dati dal form
        nome = request.form['nome']
        cognome = request.form['cognome']
        n_c = nome + "__" + cognome.replace(" ", "_")
        image = request.files.get('image')
        # se tutti i campi sono stati riempiti
        if nome and cognome:
            perm[identificativo] = n_c
            blob.upload_from_string(json.dumps(perm))
            if image:
                blob = bucket.blob('training/' + identificativo + '.png')
                blob.upload_from_string(image.read(), content_type=image.content_type)
                # inizia il processo di encoding del nuovo set di volti
                frec = FaceRecognition()
                frec.encode_known_faces()
            else:
                print("no image changed")
            return "saved_change"
        else:
            return "error_change"


@app.route('/upload', methods=['POST'])
def upload():
    # check if the post request has the file part
    if request.method == 'POST':
        file = request.files['file']
        # get the current time
        now = datetime.now()
        print("Accesso alle: ", now)
        # formatto i nomi delle immagini come anno_mese_giorno__ora_minuti_secondi.png
        # Option 1 - Server side
        current_time = now.strftime("%Y_%m_%d__%H_%M_%S")
        fname = f'{current_time}.png'

        # Save the acces photo to the cloud
        client = storage.Client.from_service_account_json(
            'facerecognition2023-84f934357826.json')
        bucket = client.bucket('door_bell')
        source_file_name = fname
        destination_blob_name = source_file_name
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(file.read(), content_type=file.content_type)

        # Face recognition
        frec.set_parameters(fname)
        # recognition_results should have only one element
        recognition_result = frec.recognize_faces()

        # first delete the image from the bucket of the doorbell
        blob.delete()
        # then save the image in the bucket of the doorbell
        # source_file_name = fname

        source_file_name = fname.split(".")[0] + '<->' + recognition_result[0]
        destination_blob_name = source_file_name
        blob = bucket.blob(destination_blob_name)
        result_file = recognition_result[1]
        blob.upload_from_string(result_file, content_type="image/png")

        if recognition_result == 'Sconosciuto':
            return 'Utente non riconosciuto'
        else:
            return 'Benvenuto ' + recognition_result[0].split('.p')[0]


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3003, debug=True)
