# print current working dir
import os

print(os.getcwd())

from resources.video.face_database import *
from profiling import *
import string
import random


def recognize(imgfp=None, databasefp="/home/blabs/Companion-Core/dynamic-system/core/databases/face_profiles.pkl",
              extractKnown=False, camera=False, array=False):
    if array:
        img = imgfp
        uituple = userinput(array=imgfp)
    else:
        uituple = userinput(camera=camera, image_directory=imgfp)
    if uituple[0] is None:
        return None
    dtb = Database(databasefp)
    finaldets = {}
    for x, i in zip(uituple[0], uituple[1]):
        name = dtb.query(i)
        newX = [float(y) for y in x]
        finaldets[name] = list(newX)
    if extractKnown:
        knownFaceNames = list(set(list(finaldets.keys())))
        # knownFaceNames.remove("Unknown")
        for i in knownFaceNames:
            random_filename = str(i) + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
            # use coordinates x1,y1,x2,y2 to extract face from image
            dtb.extract_face_and_update_profile(imgfp, finaldets[i],
                                                savedir="knownFaceExtracts/" + random_filename,
                                                name=i)  # allows the algorithm to learn from the already known faces
    return finaldets
