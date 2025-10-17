from setuptools import setup, find_namespace_packages, find_packages
from pathlib import Path

current_dir = Path(__file__).parent
long_description = (current_dir / "README.md").read_text(encoding="utf-8")

version = "1.0.4"

setup(
    name="jaw-tracking-system",
    version=version,
    description="Modular and flexible jaw motion analysis framework (motion capture, calibration, registration, "
                "and analysis)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Paul-Otto Müller",
    author_email="pmueller@sim.tu-darmstadt.de",
    url="https://github.com/paulotto/jaw_tracking_system",
    download_url=f"https://github.com/paulotto/jaw_tracking_system/tarball/{version}",
    license="CC BY-NC-SA 4.0",
    packages=["jts"], # find_namespace_packages(),
    include_package_data=True,
    install_requires=[
        "h5py",
        "numpy",
        "scipy",
        "pandas",
        "scikit-learn",
        "matplotlib"
    ],
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        # "Topic :: Scientific/Engineering :: Medical Science Apps",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    keywords="motion-capture jaw-analysis jaw-tracking biomechanics calibration registration",
    entry_points={
        "console_scripts": [
            "jts-analysis = jts.core:main"
        ],
    },
    package_data={
        # Include config files, if needed
        # "jts": ["README.md", "LICENSE", "requirements.txt"]
    },
    # data_files=[("jts/config", ["config/config.json", "config/README.md"]),
    #             ("jts/models", ["models/JTS_Models.FCStd", "models/JTS_Calibration_Tool.stl",
    #                         "models/JTS_Head_Marker.stl", "models/JTS_Mouth_Marker.stl",
    #                         "models/JTS_Teeth_Attachment.stl"])],
    project_urls={
        "Source": "https://github.com/paulotto/jaw_tracking_system",
        "Bug Tracker": "https://github.com/paulotto/jaw_tracking_system/issues",
        "License": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    },
)
