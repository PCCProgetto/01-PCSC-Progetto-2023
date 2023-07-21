from io import BytesIO
from pathlib import Path
import face_recognition
import pickle
from collections import Counter
from PIL import Image, ImageDraw
from google.cloud import storage


class FaceRecognition():
    """
    Face recognition class
    """

    def __init__(self):
        """
            - Initialize the class with the default values
            - Check if the folders exist, if not create them
        """

        # super variabiles
        self.DEFAULT_ENCODINGS_PATH = Path("face-recognizer\output")
        self.BOUNDING_BOX_COLOR = (0, 0, 255)  # blue
        self.TEXT_COLOR = (255, 255, 255)  # white

        # input variabiles
        self.image_filepath = None
        self.input_image = None
        self.validation_path = None
        self.validation_images = list()
        self.name_encodings = None
        self.model = None

        # check lists
        self.checkListWrite = list()
        self.checkListRead = list()

        # results
        self.recognition_results = list()

        # Cloud variables
        self.cs_client = storage.Client.from_service_account_json(
            'facerecognition2023-84f934357826.json')

        Path("face-recognizer/training").mkdir(exist_ok=True)
        Path("face-recognizer/output").mkdir(exist_ok=True)
        Path("face-recognizer/validation").mkdir(exist_ok=True)

    def set_parameters(self, input_image=None):
        self.input_image = input_image
        pass

    def encode_known_faces(self, model: str = "cnn"):
        """
        Encodes the known faces and saves them to a file (pickle)
        Args:
            model (str, optional): _description_. Defaults to "cnn".
            encodings_location (Path, optional): _description_. Defaults to DEFAULT_ENCODINGS_PATH.
        """
        print("Encoding known faces...", '\n')
        names = []
        encodings = []
        encodings_location = self.DEFAULT_ENCODINGS_PATH.joinpath('encodings.pkl')
        # Cloud file
        bucket = self.cs_client.bucket('face_db')
        blobs = bucket.list_blobs(prefix="training/")
        for filepath in blobs:
            if filepath.name == "training/":
                continue

            print("Filepath: ", filepath)
            self.validation_path = filepath.name.split(" .")[0].split("/")[1]
            # print the path
            print("Encoding: ", self.validation_path)
            # append the path to the list
            self.validation_images.append(filepath)

            # load the image
            # Local file
            # image = face_recognition.load_image_file(filepath)
            # Cloud file
            image = face_recognition.load_image_file(
                BytesIO(filepath.download_as_bytes()))
            print("image: ", image)
            # found the patches of the face
            face_locations = face_recognition.face_locations(image,
                                                             model=model)
            # encode the face
            face_encodings = face_recognition.face_encodings(image,
                                                             face_locations)

            for encoding in face_encodings:
                names.append(self.validation_path)
                encodings.append(encoding)

        # save the encodings
        self.name_encodings = {"names": names, "encodings": encodings}
        print("Saving encodings to disk...")
        # TODO: save the encodings to the cloud
        with encodings_location.open("wb") as f:
            pickle.dump(self.name_encodings, f)

        # save the list of images
        print("Saving encodings list")
        self.backup_images_encoded(names)

        print("Encoding completed!")

    # private recognition function
    def _recognize_face(self, unknown_encoding, loaded_encodings):
        """
        Private function to recogni

        Args:
            unknown_encoding (pkl): new encoding to compare
            loaded_encodings (pkl): encodings to compare

        Returns:
            name: the name of the person which is recognized as the most similar with the most votes
        """
        boolean_matches = face_recognition.compare_faces(loaded_encodings["encodings"],
                                                         unknown_encoding)
        votes = Counter(name for match, name in
                        zip(boolean_matches, loaded_encodings["names"]) if match)
        # if a set of votes is created, return the most voted name
        if votes:
            print("Votes: ", votes)
            return votes.most_common(1)[0][0]

    # private function to draw the squares around the faces

    def _display_face(self, draw, bounding_box, name):
        """
        Private function to draw the squares around the faces

        Args:
            draw (PIL.Image): pillow image
            bounding_box (tuple): box that sourround a face
            name (string): name of the person
        """
        top, right, bottom, left = bounding_box

        draw.rectangle(((left, top), (right, bottom)),
                       outline=self.BOUNDING_BOX_COLOR)

        text_left, text_top, text_right, text_bottom = draw.textbbox((left, bottom),
                                                                     name, align="center")
        draw.rectangle(
            ((text_left, text_top), (text_right, text_bottom)),
            fill="black",
            outline="black",
        )
        draw.text(
            (text_left, text_top),
            name,
            fill="white",
        )

    def recognize_faces(self,
                        model: str = "cnn"):
        """
            Public function to recognize the faces in the image

        Args:
            image_location (str): _description_
            model (str, optional): _description_. Defaults to "cnn".
        """
        print("Locating faces...", '\n')
        # set the encodings location
        encodings_location = self.DEFAULT_ENCODINGS_PATH.joinpath(
            'encodings.pkl')
        with encodings_location.open(mode="rb") as f:
            loaded_encodings = pickle.load(f)

        print("Loading the image...")

        # Cloud file
        bucket = self.cs_client.bucket('door_bell')
        # load only the last image
        blobs = bucket.list_blobs()
        for filepath in blobs:
            # pick only the last image
            self.image_filepath = filepath
            self.validation_path = filepath.name
        # print the path
        print("Looking for: ", self.validation_path)
        # append the path to the list
        self.validation_images.append(self.image_filepath)

        # Cloud file
        # download the image from the cloud so that's readable by face_recognition
        self.input_image = face_recognition.load_image_file(
            BytesIO(filepath.download_as_bytes()))

        print("Immagine trovata. Inizio riconoscimento... ")
        # find the faces in the image file
        input_face_locations = face_recognition.face_locations(
            self.input_image, model=model
        )
        # find the encodings of the faces
        input_face_encodings = face_recognition.face_encodings(
            self.input_image, input_face_locations
        )
        
        # generate the pillow image
        pillow_image = Image.fromarray(self.input_image)
        # create the draw object
        draw = ImageDraw.Draw(pillow_image)

        print("Recognizing faces...")
        for bounding_box, unknown_encoding in zip(
                input_face_locations, input_face_encodings):
            name = self._recognize_face(unknown_encoding, loaded_encodings)
            if not name:
                print("Volto non riconosciuto")
                name = "Sconoisciuto"
                self.recognition_results.append("Sconosciuto")
            else:
                print("Riconosciuto", name)
                self.recognition_results.append(name)

            # set the bounding box and the name
            self._display_face(draw, bounding_box, name)
        # print("Volto non trovato")
        if not self.recognition_results:
            self.recognition_results.append("Volto_non_trovato")
        # delete the draw object
        del draw
        # show the image
        pillow_image.show()
        # convert the image to png without saving locally
        pillow_image = pillow_image.convert("RGB")
        # Buffer to gather the image
        bs = BytesIO()
        pillow_image.save(bs, 'png')
        self.recognition_results.append(bs.getvalue())
        print("Recognition ended!")

        return self.recognition_results

    def validate(self, model: str = "hog"):
        for filepath in Path("face_recognizer/validation").rglob("*"):
            if filepath.is_file():
                self.recognize_faces(image_location=str(filepath.absolute()),
                                     model=model)

    def backup_images_encoded(self, names):
        # # look at all images in the training folder and put em in a list
        # with open("face-recognizer/check_encoded.txt", "w") as f:
        #     for name in names:
        #         f.write(name+'-')
        print("Backup completed")

    # def check_backup_encoded(self):
    #     print("Checking backup...")
    #     try:
    #         with open("face-recognizer/check_encoded.txt", "r") as f:

    #             # put everything in a list
    #             self.checkListRead = list()
    #             for line in f:
    #                 names = line.split('-')
    #                 for name in names:
    #                     if name != '':
    #                         self.checkListRead.append(name)

    #             # self.checkListWrite is the list of images in the training folder
    #             self.checkListWrite = list()
    #             client = storage.Client.from_service_account_json(
    #                 'facerecognition2023-84f934357826.json')
    #             bucket = client.bucket('face_db')
    #             blobs = bucket.list_blobs(prefix="training/")
    #             for filepath in blobs:
    #                 if filepath.name == "training/":
    #                     continue
    #             # for filepath in Path("face-recognizer/training").rglob("*.png"):
    #                 self.checkListWrite.append(
    #                     filepath.name.split(" .")[0].split("/")[1])

    #             # sort the lists alphabetically
    #             self.checkListRead.sort()
    #             self.checkListWrite.sort()

    #             # if checkListRead has the same elements as checkListWrite, then everything is ok
    #             if self.checkListRead == self.checkListWrite:
    #                 print("Backup checked - Encode not needed")
    #             else:
    #                 print("Backup checked - Encode needed")
    #                 self.encode_known_faces()
    #     except:
    #         print("No backup file found")
    #         print("Backup checked - Encode needed")
    #         self.encode_known_faces()
