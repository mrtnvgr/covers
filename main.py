#!/usr/bin/env python

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


from io import BytesIO
import mutagen
import argparse
import os


class Main:
    def __init__(self):

        self.curf = 1
        self.lenf = 0

        self.checkFolders()

    def checkFolders(self):
        # Get folder from arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--folder", required=True, help="folder path")
        parser.add_argument(
            "--force", help="always overwrite file covers", action="store_true"
        )
        parser.add_argument("-s", "--size", type=int, default=1000, help="cover size")
        parser.add_argument(
            "--format",
            default="jpeg",
            choices=("jpeg", "png"),
            help="cover image format",
        )
        parser.add_argument("--verbose", action="store_true", help="verbose output")
        self.args = parser.parse_args()

        # Check if folder exists
        if os.path.exists(self.args.folder):

            audiopaths = []

            # Get paths with audio

            # Iterate through folders
            for currentpath, folders, files in os.walk(self.args.folder):

                # Iterate through files
                for file in files:

                    # Check if file extension is ext
                    if self.checkAudio(file):
                        self.lenf += 1

                        if currentpath != None:
                            audiopaths.append(currentpath)
                            currentpath = None

            for path in audiopaths:
                self.cover(path)
        print()

    def cover(self, path):

        cover = None
        files = os.listdir(path)

        # List of cover names (from most to least possible)
        names = ("cover", "folder", "front", ".png", ".jpg")

        # Iterate through possible names
        for name in names:

            # Check if file is in path
            cover_path = self.fileExists(path, name)
            if cover_path != None:

                # Get cover image
                cover = self.getCover(cover_path)

                # Stop iterating if cover found
                if cover:
                    break

        if cover:

            for file in files:

                if self.checkAudio(file):
                    file_path = os.path.join(path, file)
                    self.addCover(cover, file_path)

                    self.print(f"[{self.curf}/{self.lenf}] {file_path}")

                    self.curf += 1

    def getCover(self, cover_path):

        try:
            cover = Image.open(cover_path).convert("RGB")
        except:
            return

        # Check if cover is square
        if self.getShape(cover.size) == "square":

            # Check if picture size and cover size differ
            if cover.size != (self.args.size, self.args.size):
                cover = cover.resize(
                    (self.args.size, self.args.size),
                    Image.Resampling.BICUBIC,
                )

        output = BytesIO()
        cover.save(output, format=self.args.format.capitalize())

        return output.getvalue()

    def addCover(self, cover, file_path):
        if os.path.isfile(file_path):

            audio = mutagen.File(file_path)
            if audio != None and hasattr(audio, "pictures"):

                # File has not pictures
                if audio.pictures == []:

                    pic = self.createPicture(cover)

                    audio.clear_pictures()

                    audio.add_picture(pic)

                    audio.save(file_path)

                # File has pictures
                else:

                    # Check picture size
                    newPictures = []
                    for picture in audio.pictures:

                        picdata = picture.data

                        # Check picture size
                        if (
                            picture.width != self.args.size
                            and picture.height != self.args.size
                        ) or self.args.force:

                            # Check if picture is square
                            size = (picture.width, picture.height)
                            if self.getShape(size) == "square":

                                # Resize picture
                                picdata = self.getCover(BytesIO(picdata))

                        newPicture = self.createPicture(picdata)

                        newPictures.append(newPicture)

                    # Check for new pictures
                    if newPictures != []:
                        audio.clear_pictures()

                        for picture in newPictures:

                            audio.add_picture(picture)

                        audio.save(file_path)

    def createPicture(self, data):
        pic = mutagen.flac.Picture()

        pic.data = data

        pic.type = mutagen.id3.PictureType.COVER_FRONT
        pic.mime = "image/" + self.args.format
        pic.width = self.args.size
        pic.height = self.args.size
        pic.depth = 16

        return pic

    @staticmethod
    def getShape(size):
        allowable_size_error = size[0] // 10
        size_error = abs(size[0] - size[1])
        if size_error <= allowable_size_error:
            return "square"
        else:
            return "rectangle"

    @staticmethod
    def fileExists(path, name):
        for file in os.listdir(path):
            if name in file.lower() and (
                file.lower().endswith(".jpg") or file.lower().endswith(".png")
            ):
                path = os.path.join(path, file)
                return path

    @staticmethod
    def checkAudio(file):
        exts = (".flac", ".mp3", ".wav", ".m4a")
        for ext in exts:

            if file.lower().endswith(ext):
                return True
        return False

    def print(self, text):

        if self.args.verbose:
            print(text)
        else:
            print(f"\033[K{text}", end="\r")


if __name__ == "__main__":
    Main()
