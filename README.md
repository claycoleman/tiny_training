# TinyEngine Multilabel Training

This code is based on the [TinyEngine Tutorial](https://github.com/mit-han-lab/tinyengine/tree/main/tutorial/training) codebase.

This repo extends the TinyEngine tutorial to support multilabel training on various image datasets and using various underlying classifcation models.

## Codebase Structure

The additional codebase structure on top of TinyEngine has three additional folders:

1. `.model`, containing other model files beyond TinyEngine.
2. `dataset_scripts`, containing scripts for downloading and processing the datasets.
3. `uart_scripts`, containing scripts for listening to and sending data over UART, including training.

## Dataset Scripts

To run the code in the `dataset_scripts` folder, you need to `pip install -r dataset_scripts/requirements.txt` and then run any of the .py scripts to download the dataset. We support Tiny Imagenet, Coco, and Celeba.

## Datasets

From running the scripts above, the datasets will be stored in the `datasets` folder. You'll notice the directry structure corresponds to classes. Specifically, Tiny Imagenet has classes backpack, dining_table, keyboard, remote, and desk; Coco has classes person and without_person; Celeba has classes person_1, person_2, person_3, and person_4.

## UART Training

To run the code in the `uart_scripts` folder, you need to `pip install -r uart_scripts/requirements.txt` and then run the `automated_training.py` script to kick off training. The Arduino of course needs to be conected to the computer via USB before kicking off training.

### Command Line Arguments for automated_training.py

The script supports the following command line arguments:

- `-e, --epochs`: Number of training epochs (default: 3)
- `-m, --max-examples`: Maximum number of examples to use per class
- `-s, --seed`: Random seed for reproducibility
- `-c, --clean`: Clean the project before building
- `-sp, --split`: Dataset split method, either "sequential" or "random" (default: sequential)
- `-ec, --exclude-classes`: List of class numbers to exclude from training
- `-na, --no-align`: Skip asking for camera alignment
- `-d, --dataset`: Preselect dataset (e.g., "celeba", "imagenet", "coco")
- `-rn, --run-name`: Name for the metrics subdirectory (default: "run")

Example usage:
```bash
# Train for 5 epochs using CelebA dataset
python uart_scripts/automated_training.py -e 5 -d celeba

# Train with 50 examples per class, using random split
python uart_scripts/automated_training.py -m 50 -sp random

# Train excluding classes 0 and 2, with custom run name
python uart_scripts/automated_training.py -ec 0 2 -rn experiment1
```

Additionally, the `uart_scripts` folder contains the following scripts:

- `listen.py`: listens for incoming UART data that comes from calls to `printLog` in the microcontroller code. this functionally allows you to have a console for debugging from the microcontroller.
- `send_signal.py`: listens for your input and sends it to the microcontroller over UART. you can use this to send commands to the microcontroller.
