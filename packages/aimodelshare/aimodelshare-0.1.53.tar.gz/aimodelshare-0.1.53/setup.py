
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='aimodelshare', #TODO:update
    version='0.1.53',        #TODO:update
    author="Michael Parrott",
    author_email="mikedparrott@modelshare.org",
    description="Deploy locally saved machine learning models to a live rest API and web-dashboard.  Share it with the world via modelshare.org",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.modelshare.org",
    packages=setuptools.find_packages(),
install_requires=[
        "boto3==1.40.53",
        "botocore==1.40.53",
        "scikit-learn==1.6.0",
        "onnx==1.19.1",
        "regex",
        "keras2onnx==1.7.0",
        "tensorflow",
        "tf2onnx",
        "skl2onnx==1.19.1",
        "onnxruntime==1.23.1",
        "torch==2.6.0",
        "pydot==1.4.2",
        "importlib-resources==6.1.1",
        "onnxmltools==1.14.0",
        "Pympler==1.1",
        "docker==6.1.3",
        "wget==3.2",
        "PyJWT==2.8.0",
        "seaborn==0.13.2",
        "astunparse==1.6.3",
        "shortuuid==1.0.13",
        "psutil==5.9.5",
        "protobuf",
        "dill==0.3.7",
        "scikeras==0.13.0",
        "coloredlogs==15.0.1",
        "flatbuffers",
        "jmespath==1.0.1",
        "s3transfer==0.14.0",
        ]


      ,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    include_package_data=True)
  