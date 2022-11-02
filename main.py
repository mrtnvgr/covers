#!/usr/bin/env python

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


from io import BytesIO
import mutagen
import argparse
import os

import download


class Main:
    def __init__(self):

        self.curf = 1
        self.lenf = 0

        self.statistics = {
            "skipped_count": 0,
            "converted_count": 0,
            "new_count": 0,
            "not_found_list": [],
            "downloaded_list": [],
        }

        self.checkedfuse = []

        self.getArguments()
        self.checkFolders()

    def getArguments(self):
        # Get folder from arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--folder", required=True, help="folder path")
        parser.add_argument(
            "--force",
            help="always overwrite file covers and agree on covers from internet",
            action="store_true",
        )
        parser.add_argument("-s", "--size", type=int, default=1000, help="cover size")
        parser.add_argument(
            "--keep-size", action="store_true", help="do not resize covers"
        )
        parser.add_argument(
            "--format",
            default="jpeg",
            choices=("jpeg", "png"),
            help="cover image format",
        )
        parser.add_argument("--local", action="store_true", help="do not use internet")
        parser.add_argument(
            "--no-stat", action="store_true", help="do not print statistics"
        )
        parser.add_argument("--verbose", action="store_true", help="verbose output")
        self.args = parser.parse_args()

    def checkFolders(self):

        # Check if argument is folder and exists
        if os.path.exists(self.args.folder) and os.path.isdir(self.args.folder):

            audiopaths = []

            # Get paths with audio

            # Iterate through folders
            for currentpath, _, files in os.walk(self.args.folder):

                # Iterate through files
                for file in files:

                    # Check if file extension is ext
                    if self.checkAudio(file):
                        self.lenf += 1

                        if currentpath != None:
                            audiopaths.append(currentpath)
                            currentpath = None

            # Iterate through folders
            for path in audiopaths:
                self.cover(path)

        print()

        # Check if statistics is not blocked
        if not self.args.no_stat:

            # Print statistics
            print()
            print("Covers statistics:")
            print(f"  -  Skipped: {self.statistics['skipped_count']}")
            print(f"  -  Converted: {self.statistics['converted_count']}")
            print(f"  -  New: {self.statistics['new_count']}")
            print(f"  -  Downloaded: {len(self.statistics['downloaded_list'])}")
            print(f"  -  Not Found: {len(self.statistics['not_found_list'])}")
            print()

            # Check if not_found list contains any folders

            if self.statistics["not_found_list"] != []:

                # Print paths where covers were not found
                print("Covers were not found in:")

                for folder in self.statistics["not_found_list"]:
                    print(f"  -  {folder}")

                print()

            # Check if downloaded list contains any folders

            if self.statistics["downloaded_list"] != []:

                # Print paths
                print("Downloaded covers:")

                for folder in self.statistics["downloaded_list"]:
                    print(f"  -  {folder}")

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
                cover, _ = self.getCover(cover_path)

                # Stop iterating if cover found
                if cover:
                    break

        for file in files:

            if self.checkAudio(file):
                file_path = os.path.join(path, file)

                response = self.addCover(cover, file_path)
                if response != None:
                    cover = response

                self.print(f"[{self.curf}/{self.lenf}] {file_path}")

                self.curf += 1

    def getCover(self, cover_path):

        resized = False

        cover = Image.open(cover_path).convert("RGB")

        # Check if resizing is allowed
        if not self.args.keep_size:

            shape = self.getShape(cover.size)

            # Check if cover is square
            if shape == "square":

                size = (self.args.size, self.args.size)

            elif shape == "rectangle":

                # Get size factor
                factor = max(cover.size) / min(cover.size)

                # Get normalized size
                size = [self.args.size, self.args.size]

                # Get max value index
                index = cover.size.index(max(cover.size))

                # Multiply value by factor, index = max value from cover size
                size[index] = int(size[index] * factor)

            else:

                # Unexpected behaviour
                print(f"err: {shape}")
                exit(1)

            # Check if size and cover argument size differ
            if cover.size != size:
                cover = cover.resize(
                    size,
                    Image.Resampling.BICUBIC,
                )
                resized = True

        output = BytesIO()
        cover.save(output, format=self.args.format.capitalize())

        return output.getvalue(), resized

    def addCover(self, cover, file_path):
        if os.path.isfile(file_path):

            audio = mutagen.File(file_path)
            if audio == None:
                return

            if not self.getPictures(audio):

                if cover != None:

                    # File has not pictures
                    pic = self.createPicture(cover, audio.mime)
                    result = self.addPicture(
                        audio, file_path, pic, clear=True, save=True
                    )
                    if result:
                        # Update statistics
                        self.statistics["new_count"] += 1
                        return

            # File has pictures
            else:

                # Check picture size
                newPictures = []
                resized_fuse = False

                for picture in self.getPictures(audio):

                    picdata = self.getPictureData(picture)
                    picsize = self.getPictureSize(picture)
                    # Check picture size
                    if not self.isPictureEqual(picsize) or self.args.force:

                        # Resize picture
                        picdata, resized = self.getCover(BytesIO(picdata))

                        # Burn resized fuse
                        if resized:
                            resized_fuse = True

                    newPicture = self.createPicture(picdata, audio.mime)
                    newPictures.append(newPicture)

                # Check if any pictures were resized
                if resized_fuse:
                    result = self.addPicture(
                        audio, file_path, newPictures, clear=True, save=True
                    )

                    if result:
                        # Update statistics
                        self.statistics["converted_count"] += 1
                        return

                else:

                    # Update statistics
                    self.statistics["skipped_count"] += 1

                artist = (audio.get("artist") or audio.get("performer")) or None
                album = audio["album"][0] if audio.get("album") else None
                if (
                    not self.args.local
                    and self.getPictures(audio) == []
                    and self.checkedfuse != album
                    and artist
                    and album
                ):

                    # Get cover from internet
                    result = download.getCover(artist, album, self.args.size)

                    if result:

                        # Move cursor to line start
                        print("\r\r", end="")

                        # Get bytes from result
                        result_data = result["bytes"]

                        # Update statistics

                        # Append folder to downloaded
                        folder = os.path.basename(os.path.dirname(file_path))
                        if folder not in self.statistics["downloaded_list"]:
                            self.statistics["downloaded_list"].append(folder)

                        self.statistics["new_count"] += 1

                        # Resize cover
                        result_data, _ = self.getCover(BytesIO(result_data))

                        # Get picture from data
                        picture = self.createPicture(result_data, audio.mime)

                        # Add picture and save file
                        self.addPicture(audio, file_path, picture, save=True)

                        return result_data

                    # Update checked fuse
                    self.checkedfuse = album

                if self.getPictures(audio) == []:

                    # Check if path is not in not_found list
                    folder_path = os.path.dirname(file_path)
                    if folder_path not in self.statistics["not_found_list"]:
                        self.statistics["not_found_list"].append(folder_path)

    def addPicture(self, audio, file_path, covers, clear=False, save=False):
        if covers != None:

            if type(covers) is not list:
                covers = [covers]

            if "audio/flac" in audio.mime:

                if clear:
                    audio.clear_pictures()

                for pic in covers:
                    audio.add_picture(pic)

            elif "audio/mp3" in audio.mime:

                if clear:
                    audio.tags.delall("APIC")

                for pic in covers:
                    audio.tags.add(pic)

            elif "audio/mp4" in audio.mime:

                if clear:
                    if "covr" in audio.tags:
                        audio.tags.pop("covr")

                audio["covr"] = covers

            if save:
                audio.save(file_path)

            return audio

    def getPictures(self, audio):
        if "audio/flac" in audio.mime:
            return audio.pictures

        elif "audio/mp3" in audio.mime:
            if audio.tags != None:
                return audio.tags.getall("APIC")

        elif "audio/mp4" in audio.mime:
            return audio.tags.get("covr")

        return []

    def getPictureData(self, picture):
        # FLAC and MP3
        if type(picture) is mutagen.flac.Picture or type(picture) is mutagen.id3.APIC:
            if hasattr(picture, "data"):

                return picture.data
        # M4A
        elif type(picture) is mutagen.mp4.MP4Cover:
            return bytes(picture)

    def getPictureSize(self, picture):
        # FLAC
        if hasattr(picture, "width") and hasattr(picture, "height"):
            return (picture.width, picture.height)

        # MP3 and M4A
        else:
            picinfo = Image.open(BytesIO(self.getPictureData(picture)))
            return (picinfo.width, picinfo.height)

    def createPicture(self, picdata, mime):
        if "audio/flac" in mime:
            return self.createFLACPicture(picdata)

        elif "audio/mp3" in mime:
            return self.createMP3Picture(picdata)

        elif "audio/mp4" in mime:
            return self.createMP4Picture(picdata)

    def createFLACPicture(self, data):
        pic = mutagen.flac.Picture()

        pic.data = data

        pic.type = mutagen.id3.PictureType.COVER_FRONT
        pic.mime = f"image/{self.args.format}"
        pic.width = self.args.size
        pic.height = self.args.size
        pic.depth = 16

        return pic

    def createMP3Picture(self, data):
        pic = mutagen.id3.APIC()

        pic.data = data

        pic.type = mutagen.id3.PictureType.COVER_FRONT
        pic.mime = f"image/{self.args.format}"
        pic.width = self.args.size
        pic.height = self.args.size
        pic.depth = 16

        return pic

    def createMP4Picture(self, data):

        if self.args.format == "jpeg":
            pictype = mutagen.mp4.MP4Cover.FORMAT_JPEG
        elif self.args.format == "png":
            pictype = mutagen.mp4.MP4Cover.FORMAT_PNG
        else:
            raise Exception(f"Unexpected image format: {self.args.format}")

        return mutagen.mp4.MP4Cover(data, pictype)

    def isPictureEqual(self, picsize):
        """Check if picture is equal to self.args.size with allowable errors"""
        allowable_error = max(picsize) - min(picsize)

        answer = (
            abs(self.args.size - picsize[0]) <= allowable_error
            or abs(self.args.size - picsize[1]) <= allowable_error
        )
        return answer

    @staticmethod
    def getShape(size):
        allowable_size_error = size[0] // 20
        size_error = max(size) - min(size)
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
        # NOTE: until all types are supported
        # exts = ("flac", "mp3", "wav", "m4a")
        exts = ("flac", "mp3", "m4a")
        if file.lower().split(".")[-1] in exts:
            return True
        return False

    def print(self, text, func=print):

        if self.args.verbose:
            return func(text)
        else:

            if func == print:
                return func(f"\033[K{text}", end="\r")
            else:
                return func(f"\033[K{text}")


if __name__ == "__main__":
    Main()
