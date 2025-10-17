
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='aimodelshare', #TODO:update
    version='0.1.45',        #TODO:update
    author="Michael Parrott",
    author_email="mikedparrott@modelshare.org",
    description="Deploy locally saved machine learning models to a live rest API and web-dashboard.  Share it with the world via modelshare.org",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.modelshare.org",
    packages=setuptools.find_packages(),
    install_requires=[
        "boto3==1.34.69",
        "botocore==1.34.69",
        "scikit-learn==1.6.0",
        "onnx==1.14.1",
        "onnxconverter-common==1.14.0",
        "regex",
        "keras2onnx==1.7.0",
        "tensorflow==2.18.0",
        "tf2onnx==1.16.1",
        "skl2onnx==1.18.0",
        "onnxruntime==1.17.1",
        "torch==2.6.0",
        "pydot==1.4.2",
        "importlib-resources==6.1.1",
        "onnxmltools==1.11.0",
        "Pympler==1.0.1",
        "docker==6.1.3",
        "wget==3.2",
        "PyJWT==2.8.0",
        "seaborn==0.13.2",
        "astunparse==1.6.3",
        "shortuuid==1.0.11",
        "psutil==5.9.5",
        "pathlib",  # standard in Python 3.11
        "protobuf==3.20.3",
        "dill==0.3.7",
        "scikeras==0.11.0"]


      ,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    include_package_data=True)
  