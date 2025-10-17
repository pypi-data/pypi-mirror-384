import pathlib
import setuptools

setuptools.setup(
    name="torchOpticsY",
    version="0.8.1",
    description="PyTorch-based optics caculation",
    long_description=pathlib.Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    author="YuningYe",
    author_email="1956860113@qq.com",
    license="MIT",
    packages=setuptools.find_packages(),
    install_requires=["torch", "opencv-python", "matplotlib"],
    include_package_data=True,
)
