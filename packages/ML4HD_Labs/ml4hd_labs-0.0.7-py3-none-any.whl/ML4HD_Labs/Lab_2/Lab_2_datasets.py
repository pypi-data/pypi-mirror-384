import numpy as np
import cv2
import os
import tensorflow as tf
import h5py
import requests
from tqdm import tqdm

def load_signs_dataset():
    train_dataset = h5py.File('../Datasets/Lab_2/train_signs.h5', "r")
    train_set_x_orig = np.array(train_dataset["train_set_x"][:]) # your train set features
    train_set_y_orig = np.array(train_dataset["train_set_y"][:]) # your train set labels
    
    test_dataset = h5py.File('../Datasets/Lab_2/test_signs.h5', "r")
    test_set_x_orig = np.array(test_dataset["test_set_x"][:]) # your test set features
    test_set_y_orig = np.array(test_dataset["test_set_y"][:]) # your test set labels

    classes = np.array(test_dataset["list_classes"][:]) # the list of classes
    
    train_set_y_orig = train_set_y_orig.reshape((1, train_set_y_orig.shape[0]))
    test_set_y_orig = test_set_y_orig.reshape((1, test_set_y_orig.shape[0]))
    
    return train_set_x_orig, train_set_y_orig, test_set_x_orig, test_set_y_orig, classes

def load_malaria_dataset(zip_path = '/content/cell_images.zip'):

    url = "https://data.lhncbc.nlm.nih.gov/public/Malaria/cell_images.zip"

    print("Downloading Malaria Dataset...")
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Get the total file size
    total_size = int(response.headers.get('content-length', 0))

    # Create a progress bar using tqdm. From tqdm documentation
    # "Tqdm is a Ptyhon library that wraps any iterable with a smart progress meter..."
    progress_bar = tqdm(
        total=total_size,
        unit='iB',
        unit_scale=True,
        desc="Downloading"
    )

    # Write the file content is binary mode
    with open(zip_path, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            progress_bar.update(len(data))
            file.write(data)

    progress_bar.close()


def load_malaria_filenames(load_data_dir, labels, tot_images):
    X = []
    Y = []

    for l_idx, label in enumerate(labels):
        image_names = os.listdir(os.path.join(load_data_dir, label))

        for i, image_name in enumerate(image_names[:tot_images]):
            if not image_name.endswith('.png'):
                continue
            img_name = os.path.join(load_data_dir, label, image_name)
            X.append(img_name)
            Y.append(l_idx)

    print('Loading filenames completed.')

    return X, Y

def load_malaria_image(img_name):
    num_row = 100
    num_col = 100

    if isinstance(img_name, bytes):
        img_name = img_name.decode()

    # Load the image in color (loads as BGR by default)
    img = cv2.imread(img_name, cv2.IMREAD_COLOR)

    # Check if image loaded successfully
    if img is None:
        print(f"Warning: Could not load image {img_name}")
        return None # Or raise an error

    # Convert the color space from BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Resize the image
    img = cv2.resize(img, (num_row, num_col))

    # Convert to a float32 NumPy array
    img = np.array(img, dtype='float32')

    return img



def normalize_img(image):
    return tf.cast(image, tf.float32) / 255.