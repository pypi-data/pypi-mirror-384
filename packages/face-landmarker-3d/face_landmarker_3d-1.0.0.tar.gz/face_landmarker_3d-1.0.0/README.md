# MVMP: 3D Multi-View MediaPipe

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Framework](https://img.shields.io/badge/Framework-Python_3.11-yellow)](https://www.python.org/downloads/release/python-3110/) [![Face Landmarker](https://img.shields.io/badge/Model-MediaPipe_Face_Landmarker-red)](https://developers.google.com/mediapipe/solutions/vision/face_landmarker)

## Description

MVMP (Multi-View MediaPipe) is a lightweight software designed for the 3D localization of facial landmarks starting from a static textured mesh. It generates multiple orthographic projections of the face mesh, estimates 2D landmarks using MediaPipe, and backprojects them into 3D space through a consensus-based method. The result is a robust prediction of 478 facial landmarks directly aligned with the 3D mesh geometry.

This method enables landmark estimation even without original scanning data or active vision systems, offering an efficient and flexible approach for 3D face modeling, recognition, and analysis.

<!--![alt text](./img/pipelineOverview.png)-->
<img src="./img/pipelineOverview.png">

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Installation

To install and set up the project, follow these steps:

1. Ensure you have Python 3.11 installed.

2. Create and activate a virtual environment (optional but recommended):

   ```bash
   python3.11 -m venv myenv
   source myenv/bin/activate   # On Linux/macOS
   myenv\Scripts\activate      # On Windows
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Download the MediaPipe Face Landmarker model:

   ```bash
   wget https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
   ```

## Usage

The main entry point for the program is `predict.py`.

You can run it with:

```bash
python predict.py --help
```

It accepts the following optional arguments:

```
optional arguments:
  -h, --help            Show this help message and exit.
  -f, --folder          Indicates that the input path is a root folder that will be accessed recursively to find .obj files.
  -p PROJECTIONS_NUMBER, --projections-number PROJECTIONS_NUMBER
                        Number of projections to be calculated. Default is 500.
  -o OUTPUT_PATH, --output-path OUTPUT_PATH
                        Optional. If set, results will be saved to this path. Otherwise, they will be saved inside the .obj file folder.
  -r, --render          If set, renders the results in an external window.
```

### Output

For each processed mesh, a `<mesh>_landmarks.json` file will be generated inside the corresponding mesh's folder (or the specified output folder if `--output-path` is used).

The JSON file contains:
- The normalized coordinates of the estimated 478 landmarks.
- The index of the closest mesh vertex for each landmark.

### Results
<!--![alt text](./img/results.png)-->
<img src="results.png">

## Contributing

We welcome contributions! To contribute:

1. Fork the repository and create a feature branch.
2. Make your changes with clear and descriptive commit messages.
3. Push the branch to your fork.
4. Open a pull request describing your changes.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

If you have any questions or suggestions, feel free to get in touch!
