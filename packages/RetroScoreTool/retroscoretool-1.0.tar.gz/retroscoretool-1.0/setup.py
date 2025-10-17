from setuptools import setup, find_packages

setup(
    name='RetroScoreTool',
    version='1.0',
    packages=find_packages(include=["RetroScore", "RetroScore.*"]),
    install_requires=[
        "rxnmapper==0.4.2",
        "numpy",
        "pandas",
        "rdkit",
        "torch",
        "torchaudio",
        "torchvision",
        "tqdm",
        "joblib"
    ],
    # package_dir={"": "RetroScore"},
    # packages=find_packages("RetroScore"),
    package_data={
        "RetroScore": [
            "data/multi_step/retro_data/dataset/origin_dict.csv",
            "data/multi_step/retro_data/saved_models/best_epoch_final_4.pt",
            "experiments/uspto_full/epoch_65.pt"
        ],
    },
    include_package_data=True,   # 同时接受 MANIFEST.in
    description='RetroScoreTools',
    author='SnowGao',
    author_email='892381602@qq.com',
)

