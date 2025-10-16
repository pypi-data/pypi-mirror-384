from setuptools import setup, find_packages

# setup(
#     name="ml-trainer-sdk",
#     version="0.2.0",
#     description="A modular SDK for training ML models (image, tabular, timeseries, etc.)",
#     author="Hypnotic",
#     packages=find_packages(include=["ml_trainer", "ml_trainer.*"]),
#     install_requires=[
#         "torch",
#         "numpy",
#         "pandas",
#         "scikit-learn",
#         "matplotlib",
#         "requests",
#         "tensorboard",
#         "clearml",
#     ],
#     python_requires=">=3.7",
#     include_package_data=True,
# )


setup(
    name="ml-trainer-sdk",
    version="0.2.1",
    description="A modular SDK for training ML models (image, tabular, timeseries, etc.)",
    author="Hypnotic",
    packages=find_packages(include=["ml_trainer", "ml_trainer.*"]),
    install_requires=[
        # Core ML and Data Science
        "torch==2.5.1",
        "torchvision==0.20.1",
        "numpy==1.26.4",
        "pandas==2.2.3",
        "scikit-learn==1.5.2",
        "matplotlib==3.10.1",
        "tensorboard==2.19.0",
        "Cython==3.1.1",

        # LLM finetuning
        "datasets==4.1.1",
        "unsloth==2025.10.1",
        "unsloth_zoo==2025.10.1",
        "torchao==0.12.0",

        # Other tasks
        "patool==4.0.1",
        "reformer-pytorch==1.4.4",
        "sktime==0.39.0",
        "PyWavelets==1.8.0",
        "timm==1.0.20",
    ],
    python_requires=">=3.10",
    include_package_data=True,
)