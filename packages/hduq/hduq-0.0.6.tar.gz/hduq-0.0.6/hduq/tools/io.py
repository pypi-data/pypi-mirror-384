import numpy as np
import pandas as pd
from PIL import Image
import cv2
import json

import os
import inspect
import platform
import subprocess


__all__ = [
    'code',
    'finder',
    'load',
    'save'
]



def code(input_):
    if inspect.isfunction(input_) or inspect.ismodule(input_) or inspect.isclass(input_):
        file_path = inspect.getfile(input_)
    else:
        file_path = os.path.expanduser(input_)

    if platform.system() == 'Darwin':
        subprocess.run(['code', file_path], check=True)
    elif platform.system() == 'Windows':
        subprocess.run(['powershell.exe', '-Command', f'code {file_path}'], check=True)
    else:
        raise NotImplementedError('This function is supported on Windows and macOS only.')



def finder(path):
    path = os.path.expanduser(path)
    if platform.system() == 'Darwin':
        subprocess.run(['open', path], check=True)
    elif platform.system() == 'Windows':
        subprocess.run(['start', '', path], shell=True, check=True)
    else:
        raise NotImplementedError('This function is supported on Windows and macOS only.')
    
    return os.path.abspath(path)



class _FileReader:
    def __init__(self, path, dtype):
        self.path = os.path.expanduser(path)
        self.dtype = dtype
    
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'{path} does not exists')
        
        self.path = path
        self.ext = os.path.splitext(path)[-1].lower()[1:]
        self.name = os.path.basename(path)
        self.stem = os.path.splitext(self.name)[0]


    def _img(self):
        img = Image.open(self.path)
        try:
            n_frames = img.n_frames
        except AttributeError:
            n_frames = 1
        arr = []
        for i in range(n_frames):
            if n_frames > 1:
                img.seek(i)
            arr.append(np.array(img))

        arr = np.array(arr).astype(self.dtype)
        if arr.shape[0] == 1:
            return arr[0]
        return arr



    def _avi(self):
        avi = cv2.VideoCapture(self.path)
        arr = []
        while True:
            ret, frame = avi.read()
            if not ret:
                break
            arr.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        avi.release()
        return np.array(arr).astype(self.dtype)


    def _json(self):
        with open(self.path, 'r') as f:
            dic = json.load(f)
        return dic


    def _csv(self):
        return np.array(pd.read_csv(self.path, header=None))


    def _npy(self):
        return np.load(self.path).astype(self.dtype)


    def _npz(self):
        dic = dict(np.load(self.path))
        for key in dic.keys():
            dic[key] = dic[key].astype(self.dtype)
        return dic


    def _other(self):
        msg = f"No implemented method for '.{self.ext}', nothing to return."
        if os.path.exists(self.path):
            msg += f"The file '{self.name}' exists, you may use finder() to open it."
        print(msg)
        return None


    def load(self):
        if self.ext == 'npz':
            data = self._npz()

        elif self.ext == 'npy':
            data = self._npy()

        elif self.ext == 'avi':
            data = self._avi()

        elif self.ext in ['bmp', 'tif', 'tiff']:
            data = self._img()

        elif self.ext == 'csv':
            data = self._csv()

        elif self.ext == 'json':
            data = self._json()

        else:
            data = self._other()

        return data



class _FileWriter:
    def __init__(self, path, data, dtype=float):
        self.path = os.path.abspath(os.path.expanduser(path))
        self.data = data
        self.dtype = dtype

        self.ext = os.path.splitext(self.path)[-1].lower()[1:]
        self.name = os.path.basename(self.path)
        self.stem = os.path.splitext(self.name)[0]


    def _json(self):
        if isinstance(self.data, dict):
            with open(self.path, 'w') as f:
                json.dump(self.data, f, indent=2)
        else:
            raise TypeError("'.json' format requires a dict of arrays")


    def _csv(self):
        arr = np.array(self.data).astype(self.dtype)
        pd.DataFrame(arr).to_csv(self.path, index=False, header=False)


    def _npy(self):
        np.save(self.path, np.array(self.data).astype(self.dtype))


    def _npz(self):
        if isinstance(self.data, dict):
            np.savez_compressed(self.path, **{k: np.array(v).astype(self.dtype) for k, v in self.data.items()})
            return self.path
        else:
            raise TypeError("'.npz format requires a dict of arrays")


    def _other(self):
        msg = f"No implemented saver for '.{self.ext}', nothing saved."
        print(msg)


    def save(self):
        if self.ext == 'npz':
            self._npz()
        
        elif self.ext == 'npy':
            self._npy()
        
        elif self.ext == 'csv':
            self._csv()
        
        elif self.ext == 'json':
            self._json()
        
        else:
            self._other()



def load(path, dtype=float):
    target = _FileReader(path, dtype)
    return target.load()



def save(path, data, dtype=float):
    target = _FileWriter(path, data, dtype)
    target.save()
    return target.path

