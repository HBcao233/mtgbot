import os.path
import cv2
import time 
import numpy as np
from .log import logger
from .file import getCache


def videoInfo(path):
  cap = cv2.VideoCapture(path)
  rate = cap.get(5)
  frame_count = cap.get(7)
  duration = frame_count / rate
  width = cap.get(3)
  height = cap.get(4)
  cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
  ret, img = cap.read()
  cap.release()
  img = getPhotoThumbnail(img)
  thumbnail = img2bytes(img, 'jpg')
  return open(path, 'rb'), duration, width, height, thumbnail


def img2bytes(img, ext):
  if '.' not in ext:
    ext = '.' + ext
  return cv2.imencode(ext, img)[1].tobytes()
  
  
def getPhotoThumbnail(path, saveas=None) -> cv2.Mat:
  return resizePhoto(path, 320, saveas=saveas)
  
  
def resizePhoto(path, maxSize=2560, size=None, saveas=None) -> cv2.Mat:
  if isinstance(path, str):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
  else:
    img = path
  h, w, channels = img.shape
  if size is None:
    if w > maxSize or h > maxSize:
      if w >= h:
        size = (maxSize, int(maxSize * h / w))
      elif h > w:
        size = (int(maxSize * w / h), maxSize)
  if size is not None: 
    img = cv2.resize(img, size)
  if channels == 4:
    white = np.zeros(img.shape, dtype='uint8') 
    img = cv2.add(img, white)
  if saveas is not None:
    cv2.imwrite(saveas, img)
  return img
  