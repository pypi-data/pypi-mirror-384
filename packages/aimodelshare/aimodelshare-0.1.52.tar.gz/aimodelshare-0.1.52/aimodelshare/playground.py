# import packages
import os
import contextlib
import boto3
from aimodelshare.api import get_api_json
import tempfile

try:
    import torch
except:
    pass
import onnx
from aimodelshare.utils import HiddenPrints
import signal
from aimodelshare.aimsonnx import model_to_onnx, model_to_onnx_timed
from aimodelshare.tools import extract_varnames_fromtrainingdata, _get_extension_from_filepath
import time
import numpy as np
import json
import pandas
import requests
from aimodelshare.aws import get_aws_token


class ModelPlayground:
    """
    Parameters:
    ----------
    `model_type` : ``string``
          values - [ 'text' , 'image' , 'tabular' , 'video', 'audio','timeseries' ]
          type of model data
    `classification`:    ``bool, default=True``
        True [DEFAULT] if model is of Classification type with categorical target variables
        False if model is of Regression type with continuous target variables
    `private` :   ``bool, default = False``
        True if model and its corresponding data is not public
        False [DEFAULT] if model and its corresponding data is public
    `email_list`: ``list of string values``
                values - list including all emails of users who have access the private playground.
                list should contain same emails that were used by users to sign up for modelshare.ai account.
                [OPTIONAL] set by the playground owner for private playgrounds.  Can also be updated by editing deployed
                playground page at www.modelshare.ai.
    """

    def __init__(self, input_type=None, task_type=None, private=None, playground_url=None, email_list=None):
        # confirm correct args are provided
        if playground_url == None and any([input_type == None, task_type == None, private == None]):
            raise ValueError(
                "To instantiate a ModelPlayground instance, please provide either a playground_url or \n the input_type, task_type, and private arguments.")

        self.model_type = input_type

        if task_type == None:
            post_dict = {"return_task_type": "TRUE"}
            headers = { 'Content-Type':'application/json', 'authorizationToken': os.environ.get("AWS_TOKEN"),} 
            playground_url_eval=playground_url[:-1]+"eval"
            response = requests.post(playground_url_eval,headers=headers,data=json.dumps(post_dict))
            task_type = json.loads(response.text)['task_type']
        
        if task_type == "classification":
            self.categorical = True
        elif task_type == "regression":
            self.categorical = False
        else:
            raise ValueError('Please set task_type argument to "classification" or "regression".')

        self.private = private
        self.playground_url = playground_url
        self.model_page = None

        if email_list is None:
            self.email_list = []
        else:
            self.email_list = email_list

        def codestring(self):
            if self.playground_url == None:
                return "ModelPlayground(model_type=" + "'" + str(self.model_type) + "'" + ",classification=" + str(
                    self.categorical) + ",private=" + str(self.private) + ",playground_url=" + str(
                    self.playground_url) + ",email_list=" + str(self.email_list) + ")"
            else:
                return "ModelPlayground(model_type=" + "'" + str(self.model_type) + "'" + ",classification=" + str(
                    self.categorical) + ",private=" + str(self.private) + ",playground_url=" + "'" + str(
                    self.playground_url) + "'" + ",email_list=" + str(self.email_list) + ")"

        self.class_string = codestring(self)

    def __str__(self):
        return f"ModelPlayground(self.model_type,self.categorical,self.private = private,self.playground_url,self.email_list)"

    def activate(self, model_filepath=None, preprocessor_filepath=None, y_train=None, example_data=None,
                 custom_libraries="FALSE", image="", reproducibility_env_filepath=None, memory=None, timeout=None,
                 onnx_timeout=60, pyspark_support=False, model_input=None, input_dict=None, playground_id=False):

        """
        Launches a live model playground to the www.modelshare.ai website. The playground can optionally include a live prediction REST API for deploying ML models using model parameters and user credentials, provided by the user.
        Inputs : 7
        Output : model launched to an API
                detailed API info printed out
        Parameters:
        ----------
        `model_filepath` :  ``string`` ends with '.onnx'
              value - Absolute path to model file
              .onnx is the only accepted model file extension
              "example_model.onnx" filename for file in directory.
              "/User/xyz/model/example_model.onnx" absolute path to model file from local directory
              if no value is set the playground will be launched with only a placeholder prediction API.
        `preprocessor_filepath`:  ``string``
            value - absolute path to preprocessor file
            "./preprocessor.zip"
            searches for an exported zip preprocessor file in the current directory
            file is generated using export_preprocessor function from the AI Modelshare library
            if no value is set the playground will be launched with only a placeholder prediction API.
        `y_train` : training labels for classification models.
            expects pandas dataframe of one hot encoded y train data
            if no value is set ... #TODO
        `example_data`: ``Example of X data that will be shown on the online Playground page.
            if no example data is submitted, certain functionalities may be limited, including the deployment of live prediction APIs.
            Example data can be updated at a later stage, using the update_example_data() method.``
        `custom_libraries`: ``string``
            "TRUE" if user wants to load custom Python libraries to their prediction runtime
            "FALSE" if user wishes to use AI Model Share base libraries including latest versions of most common ML libs.
        `reproducibility_env_filepath`: ``TODO``
        `memory`: ``TODO``
        `timeout`: ``TODO``
        `onnx_timeout`: ``int``
            Time in seconds after which ONNX conversion should be interrupted.
            Set to False if you want to force ONNX conversion.
        `pyspark_support`: ``TODO``
        `model_input`: ``array_like``
            Required only when framework="pytorch"
            One example of X training data in correct format.

        Returns:
        --------
        print_api_info : prints statements with generated model playground page and live prediction API details
                        also prints steps to update the model submissions by the user/team
        """

        # test whether playground is already active
        if self.playground_url:
            print(self.playground_url)

            def ask_user():
                print("Playground is already active. Would you like to overwrite?")
                response = ''
                while response not in {"yes", "no"}:
                    response = input("Please enter yes or no: ").lower()
                return response != "yes"

            r = ask_user()

            if r:
                return

        # convert model to onnx
        if onnx_timeout == False:
            force_onnx = True
        else:
            force_onnx = False
        model_filepath = model_to_onnx_timed(model_filepath, timeout=onnx_timeout,
                                             force_onnx=force_onnx, model_input=model_input)

        # keep track of submitted artifacts
        if isinstance(y_train, pandas.Series):
            y_train_bool = True
        else:
            y_train_bool = bool(y_train)

        if isinstance(example_data, (pandas.Series, pandas.DataFrame, str)):
            example_data_bool = True
        else:
            example_data_bool = False

        track_artifacts = {"model_filepath": bool(model_filepath),
                           "preprocessor_filepath": bool(preprocessor_filepath),
                           "y_train": y_train_bool,
                           "example_data": example_data_bool,
                           "custom_libraries": bool(custom_libraries),
                           "image": bool(image),
                           "reproducibility_env_filepath": bool(reproducibility_env_filepath),
                           "memory": bool(memory),
                           "timeout": bool(timeout),
                           "pyspark_support": bool(pyspark_support)
                           }

        import pkg_resources

        # insert placeholders into empty arguments
        if model_filepath == None:
            model_filepath = pkg_resources.resource_filename(__name__, "placeholders/model.onnx")

        if preprocessor_filepath == None:
            preprocessor_filepath = pkg_resources.resource_filename(__name__, "placeholders/preprocessor.zip")

        if y_train_bool == False:
            y_train = []

        if example_data_bool == False and self.model_type == "tabular":
            example_data = pandas.DataFrame()

        import json, tempfile
        tfile = tempfile.NamedTemporaryFile(mode="w+")
        json.dump(track_artifacts, tfile)
        tfile.flush()

        if input_dict == None:
            input_dict = {"requirements": "",
                          "model_name": "Default Model Playground",
                          "model_description": "",
                          "tags": ""}
            playground_id = True
        else:
            playground_id = False

        from aimodelshare.generatemodelapi import model_to_api
        self.playground_url = model_to_api(model_filepath=model_filepath,
                                           model_type=self.model_type,
                                           private=self.private,
                                           categorical=self.categorical,
                                           y_train=y_train,
                                           preprocessor_filepath=preprocessor_filepath,
                                           example_data=example_data,
                                           custom_libraries=custom_libraries,
                                           image=image,
                                           reproducibility_env_filepath=reproducibility_env_filepath,
                                           memory=memory,
                                           timeout=timeout,
                                           email_list=self.email_list,
                                           pyspark_support=pyspark_support,
                                           input_dict=input_dict,
                                           print_output=False,
                                           playground_id=playground_id
                                           )
        # remove extra quotes
        self.playground_url = self.playground_url[1:-1]

        # upload track artifacts
        from aimodelshare.aws import get_s3_iam_client
        s3, iam, region = get_s3_iam_client(os.environ.get("AWS_ACCESS_KEY_ID_AIMS"),
                                            os.environ.get("AWS_SECRET_ACCESS_KEY_AIMS"),
                                            os.environ.get("AWS_REGION_AIMS"))

        unique_model_id = self.playground_url.split(".")[0].split("//")[-1]

        try:
            s3["client"].upload_file(tfile.name, os.environ.get("BUCKET_NAME"),
                                     unique_model_id + "/track_artifacts.json")
        except:
            pass

    def deploy(self, model_filepath, preprocessor_filepath, y_train, example_data=None, custom_libraries="FALSE",
               image="", reproducibility_env_filepath=None, memory=None, timeout=None, onnx_timeout=60,
               pyspark_support=False,
               model_input=None, input_dict=None):

        """
        Launches a live prediction REST API for deploying ML models using model parameters and user credentials, provided by the user
        Inputs : 7
        Output : model launched to an API
                detailed API info printed out
        Parameters:
        ----------
        `model_filepath` :  ``string`` ends with '.onnx'
              value - Absolute path to model file
              [REQUIRED] to be set by the user
              .onnx is the only accepted model file extension
              "example_model.onnx" filename for file in directory.
              "/User/xyz/model/example_model.onnx" absolute path to model file from local directory
        `preprocessor_filepath`:  ``string``
            value - absolute path to preprocessor file
            [REQUIRED] to be set by the user
            "./preprocessor.zip"
            searches for an exported zip preprocessor file in the current directory
            file is generated using export_preprocessor function from the AI Modelshare library
        `y_train` : training labels for classification models.
              [REQUIRED] for classification type models
              expects pandas dataframe of one hot encoded y train data
        `example_data`: ``Example of X data that will be shown on the online Playground page.
            if no example data is submitted, certain functionalities may be limited, including the deployment of live prediction APIs.
            Example data can be updated at a later stage, using the update_example_data() method.``
        `custom_libraries`:   ``string``
            "TRUE" if user wants to load custom Python libraries to their prediction runtime
            "FALSE" if user wishes to use AI Model Share base libraries including latest versions of most common ML libs.
        `image`: ``TODO``
        `reproducibility_env_filepath`: ``TODO``
        `memory`: ``TODO``
        `timeout`: ``TODO``
        `onnx_timeout`: ``int``
            Time in seconds after which ONNX conversion should be interrupted.
            Set to False if you want to force ONNX conversion.
        `pyspark_support`: ``TODO``
        `model_input`: ``array_like``
            Required only when framework="pytorch"
            One example of X training data in correct format.
        `input_dict`:   ``dictionary``
             Use to bypass text input boxes Example: {"model_name": "My Model Playground",
                      "model_description": "My Model Description",
                      "tags": "model, classification, awesome"}

        Returns:
        --------
        print_api_info : prints statements with generated live prediction API details
                        also prints steps to update the model submissions by the user/team
        """

        # check whether playground url exists
        if self.playground_url:
            print(self.playground_url)
            print("Trying to deploy to active playground. Would you like to overwrite prediction API?")
            response = ''
            while response not in {"yes", "no"}:
                response = input("Please enter yes or no: ").lower()

            if response == "no":
                print("Please instantiate a new playground and try again.")
                return
        # model deployment files (plus ytrain object)

        # convert model to onnx
        if onnx_timeout == False:
            force_onnx = True
        else:
            force_onnx = False
        model_filepath = model_to_onnx_timed(model_filepath, timeout=onnx_timeout,
                                             force_onnx=force_onnx, model_input=model_input)

        import os
        if os.environ.get("cloud_location") is not None:
            cloudlocation = os.environ.get("cloud_location")
        else:
            cloudlocation = "not set"
        if "model_share" == cloudlocation:
            print("Creating your Model Playground...\nEst. completion: ~1 minute\n")

            def deployment_output_information():
                import os
                import sys

                sys.stdout.write(
                    "[===                                  ] Progress: 5% - Accessing cloud, uploading resources...")
                sys.stdout.flush()
                time.sleep(15)
                sys.stdout.write('\r')
                sys.stdout.write(
                    "[========                             ] Progress: 30% - Building serverless functions and updating permissions...")
                sys.stdout.flush()
                time.sleep(15)
                sys.stdout.write('\r')
                sys.stdout.write(
                    "[============                         ] Progress: 40% - Creating custom containers...                        ")
                sys.stdout.flush()
                time.sleep(15)
                sys.stdout.write('\r')
                sys.stdout.write(
                    "[==========================           ] Progress: 75% - Deploying prediction API...                          ")
                sys.stdout.flush()
                time.sleep(10)
                sys.stdout.write('\r')
                sys.stdout.write(
                    "[================================     ] Progress: 90% - Configuring prediction API...                          ")
                sys.stdout.flush()
                time.sleep(10)

            from threading import Thread
            import time

            thread_running = True
            t1 = Thread(target=deployment_output_information)
            t1.start()

            def run_deployment_code(model_filepath=model_filepath,
                                    model_type=self.model_type,
                                    private=self.private,
                                    categorical=self.categorical,
                                    y_train=y_train,
                                    preprocessor_filepath=preprocessor_filepath,
                                    example_data=example_data,
                                    custom_libraries=custom_libraries,
                                    image=image,
                                    reproducibility_env_filepath=reproducibility_env_filepath,
                                    memory=memory,
                                    timeout=timeout,
                                    email_list=self.email_list,
                                    pyspark_support=pyspark_support,
                                    input_dict=input_dict,
                                    print_output=False):

                def upload_playground_zipfile(model_filepath=None, preprocessor_filepath=None, y_train=None,
                                              example_data=None):
                    """
                  minimally requires model_filepath, preprocessor_filepath
                  """
                    import json
                    import os
                    import requests
                    import pandas as pd
                    wkingdir = os.getcwd()
                    if os.path.dirname(model_filepath) == '':
                        model_filepath = wkingdir + "/" + model_filepath
                    else:
                        pass

                    if os.path.dirname(preprocessor_filepath) == '':
                        preprocessor_filepath = wkingdir + "/" + preprocessor_filepath
                    else:
                        pass
                    zipfilelist = [model_filepath, preprocessor_filepath]

                    if any([isinstance(example_data, pd.DataFrame), isinstance(example_data, pd.Series),
                            example_data is None]):
                        pass
                    else:
                        if os.path.dirname(example_data) == '':
                            example_data = wkingdir + "/" + example_data
                        else:
                            pass
                        zipfilelist.append(example_data)

                    # need to save dict pkl file with arg name and filepaths to add to zipfile

                    apiurl = "https://djoehnv623.execute-api.us-east-2.amazonaws.com/prod/m"

                    apiurl_eval = apiurl[:-1] + "eval"

                    headers = {'Content-Type': 'application/json', 'authorizationToken': json.dumps(
                        {"token": os.environ.get("AWS_TOKEN"), "eval": "TEST"}), }
                    post_dict = {"return_zip": "True"}
                    zipfile = requests.post(apiurl_eval, headers=headers, data=json.dumps(post_dict))

                    zipfileputlistofdicts = json.loads(zipfile.text)['put']

                    zipfilename = list(zipfileputlistofdicts.keys())[0]

                    from zipfile import ZipFile
                    import os
                    from os.path import basename
                    import tempfile

                    wkingdir = os.getcwd()

                    tempdir = tempfile.gettempdir()

                    zipObj = ZipFile(tempdir + "/" + zipfilename, 'w')
                    # Add multiple files to the zip
                    for i in zipfilelist:
                        zipObj.write(i)

                    # add object to pkl file pathway here. (saving y label data)
                    import pickle

                    if y_train is None:
                        pass
                    else:
                        with open(tempdir + "/" + 'ytrain.pkl', 'wb') as f:
                            pickle.dump(y_train, f)

                        os.chdir(tempdir)
                        zipObj.write('ytrain.pkl')

                    if any([isinstance(example_data, pd.DataFrame), isinstance(example_data, pd.Series)]):
                        if isinstance(example_data, pd.Series):
                            example_data = example_data.to_frame()
                        else:
                            pass
                        with open(tempdir + "/" + 'exampledata.pkl', 'wb') as f:
                            pickle.dump(example_data, f)

                        os.chdir(tempdir)
                        zipObj.write('exampledata.pkl')
                    else:
                        pass

                    # close the Zip File
                    os.chdir(wkingdir)

                    zipObj.close()

                    import ast

                    finalzipdict = ast.literal_eval(zipfileputlistofdicts[zipfilename])

                    url = finalzipdict['url']
                    fields = finalzipdict['fields']

                    #### save files from model deploy to zipfile in tempdir before loading to s3

                    ### Load zipfile to s3
                    with open(tempdir + "/" + zipfilename, 'rb') as f:
                        files = {'file': (tempdir + "/" + zipfilename, f)}
                        http_response = requests.post(url, data=fields, files=files)
                    return zipfilename

                deployzipfilename = upload_playground_zipfile(model_filepath, preprocessor_filepath, y_train,
                                                              example_data)

                # if aws arg = false, do this, otherwise do aws code
                # create deploy code_string
                def nonecheck(objinput=""):
                    if isinstance(objinput, str):
                        if objinput is None:
                            objinput = "None"
                        else:
                            objinput = "'/tmp/" + objinput + "'"
                    else:
                        objinput = 'example_data'
                    return objinput

                deploystring = self.class_string.replace(",aws=False",
                                                         "") + "." + "deploy('/tmp/" + model_filepath + "','/tmp/" + preprocessor_filepath + "'," + 'y_train' + "," + nonecheck(
                    example_data) + ",input_dict=" + str(input_dict) + ')'
                import base64
                import requests
                import json

                api_url = "https://z4kvag4sxdnv2mvs2b6c4thzj40bxnuw.lambda-url.us-east-2.on.aws/"

                data = json.dumps({"code": """from aimodelshare import ModelPlayground;myplayground=""" + deploystring,
                                   "zipfilename": deployzipfilename, "username": os.environ.get("username"),
                                   "password": os.environ.get("password"),
                                   "token": os.environ.get("JWT_AUTHORIZATION_TOKEN"), "s3keyid": "xrjpv1i7xe"})

                headers = {"Content-Type": "application/json"}

                response = requests.request("POST", api_url, headers=headers, data=data)
                # Print response
                global successful_deployment_info340893124738241023

                result = json.loads(response.text)
                successful_deployment_info340893124738241023 = result

                modelplaygroundurlid = json.loads(result['body'])[-7].replace("Playground Url: ", "").strip()
                try:
                    self.playground_url = modelplaygroundurlid[1:-1]
                except:
                    import json
                    self.playground_url = json.loads(modelplaygroundurlid)
                    pass

            t2 = Thread(target=run_deployment_code(model_filepath=model_filepath,
                                                   model_type=self.model_type,
                                                   private=self.private,
                                                   categorical=self.categorical,
                                                   y_train=y_train,
                                                   preprocessor_filepath=preprocessor_filepath,
                                                   example_data=example_data,
                                                   custom_libraries=custom_libraries,
                                                   image=image,
                                                   reproducibility_env_filepath=reproducibility_env_filepath,
                                                   memory=memory,
                                                   timeout=timeout,
                                                   email_list=self.email_list,
                                                   pyspark_support=pyspark_support,
                                                   input_dict=input_dict,
                                                   print_output=False))

            t2.start()

            t2.join()  # interpreter will wait until your process get completed or terminated
            # clear last output
            import os
            import sys

            def cls():
                os.system('cls' if os.name == 'nt' else 'clear')

            # now, to clear the screen
            cls()
            from IPython.display import clear_output
            clear_output()
            sys.stdout.write('\r')
            sys.stdout.write(
                "[=====================================] Progress: 100% - Complete!                                            ")
            sys.stdout.flush()
            import json
            print("\n" + json.loads(successful_deployment_info340893124738241023['body'])[-8] + "\n")
            print(
                "View live playground now at:\n" + json.loads(successful_deployment_info340893124738241023['body'])[-1])

            print("\nConnect to your playground in Python:\n")
            print("myplayground=ModelPlayground(playground_url=" +
                  json.loads(successful_deployment_info340893124738241023['body'])[-7].replace("Playground Url: ",
                                                                                               "").strip() + ")")

            thread_running = False

        else:

            # aws pathway begins here
            from aimodelshare.generatemodelapi import model_to_api
            self.playground_url = model_to_api(model_filepath=model_filepath,
                                               model_type=self.model_type,
                                               private=self.private,
                                               categorical=self.categorical,
                                               y_train=y_train,
                                               preprocessor_filepath=preprocessor_filepath,
                                               example_data=example_data,
                                               custom_libraries=custom_libraries,
                                               image=image,
                                               reproducibility_env_filepath=reproducibility_env_filepath,
                                               memory=memory,
                                               timeout=timeout,
                                               email_list=self.email_list,
                                               pyspark_support=pyspark_support,
                                               input_dict=input_dict,
                                               print_output=False)
            # remove extra quotes
            self.playground_url = self.playground_url[1:-1]

    def get_apikey(self):
        import os
        import requests
        import json
        if all(["username" in os.environ,
                "password" in os.environ]):
            pass
        else:
            return print("'get_apikey()' unsuccessful. Please provide credentials with set_credentials().")

        post_dict = {"return_apikey": "True"}

        headers = {'Content-Type': 'application/json', 'authorizationToken': os.environ.get("AWS_TOKEN"), }

        apiurl_eval = self.playground_url[:-1] + "eval"

        api_json = requests.post(apiurl_eval, headers=headers, data=json.dumps(post_dict))

        return json.loads(api_json.text)['apikey']

    def create(self, eval_data=None, y_train=None, data_directory=None, eval_metric_filepath=None, email_list=None,
               public=True, public_private_split=0.5, model_input=None, timeout=None, example_data=None,
               custom_libraries="FALSE", image="", reproducibility_env_filepath=None, memory=None,
               pyspark_support=False,
               user_input=False):

        """
        Submits model/preprocessor to machine learning experiment leaderboard and model architecture database using live prediction API url generated by AI Modelshare library
        The submitted model gets evaluated and compared with all existing models and a leaderboard can be generated

        Parameters:
        -----------
        `eval_data` :  ``list`` of y values used to generate metrics from predicted values from predictions submitted via the submit_model() method
            [REQUIRED] to generate eval metrics in experiment leaderboard
        `y_train` :  ``list`` of y values for training data used to extract the set of class labels
            [REQUIRED] for image classification models
        `eval_metric_filepath`: [OPTIONAL] file path of zip file with custon evaluation functions
        `data_directory` : folder storing training data and test data (excluding Y test data)
        `email_list`: [OPTIONAL] list of comma separated emails for users who are allowed to submit models to experiment leaderboard.  Emails should be strings in a list.
        `public`: [REQUIRED] True/false. Defaults to False.  If True, experiment is public and ANY AIMODELSHARE USER CAN SUBMIT MODELS.  USE WITH CAUTION b/c one model and
            one preprocessor file will be be saved to your AWS S3 folder for each model submission.
        `public_private_split`: [REQUIRED] Float between 0 and 1. Defaults to 0. Porportion of test data that is allocated to private hold-out set.
        `model_input`: ``array_like``
            Required only when framework="pytorch"
            One example of X training data in correct format.
        `timeout`: ``TODO``
        `onnx_timeout`: ``int``
            Time in seconds after which ONNX conversion should be interrupted.
            Set to False if you want to force ONNX conversion.
        `example_data`: ``Example of X data that will be shown on the online Playground page.
            if no example data is submitted, certain functionalities may be limited, including the deployment of live prediction APIs.
            Example data can be updated at a later stage, using the update_example_data() method.``

        Returns:
        -------
        response:   Model version if the model is submitted sucessfully
                    error  if there is any error while submitting models
        """

        # use placeholder y_train labels if none are submitted
        if y_train == None:
            ytrain = []

        # use placeholder y_train labels if none are submitted
        if eval_data == None:
            eval_data = []

        if email_list == None:
            email_list = []

        # catch email list error
        if public == False and email_list == []:
            raise ValueError("Please submit valid email list for private competition/experiment.")

        # test whether playground is active, activate if that is not the case
        if not self.playground_url:

            if user_input:

                print("Submit Model Playground data.")
                model_name = input("Playground name: ")
                model_description = input("Playground description: ")
                requirements = input("Requirements: ")
                tags = input("Tags: ")
                print()

                input_dict = {"requirements": requirements,
                              "model_name": model_name,
                              "model_description": model_description,
                              "tags": tags}

                playground_id = False

            else:

                input_dict = {"requirements": "",
                              "model_name": "Default Model Playground",
                              "model_description": "",
                              "tags": ""}

                playground_id = True

            self.activate(None, None, example_data=example_data,
                          onnx_timeout=None, y_train=y_train, custom_libraries=custom_libraries,
                          image=image, reproducibility_env_filepath=reproducibility_env_filepath,
                          memory=memory, pyspark_support=pyspark_support, timeout=timeout, input_dict=input_dict,
                          playground_id=playground_id)
            print()

        # if playground is active, ask whether user wants to overwrite
        else:

            print(
                "The Model Playground is already active. Do you want to overwrite existing competitions and experiments?")
            response = ''
            while response not in {"yes", "no"}:
                response = input("Please enter yes or no: ").lower()

            if response == "no":
                print("Please instantiate a new playground and try again.")
                return

        # get model id from playground url
        unique_model_id = self.playground_url.split(".")[0].split("//")[-1]

        if user_input == False:

            competition_name = "Default Competition " + unique_model_id
            competition_description = ""
            data_description = ""
            data_license = ""

        else:

            print("Submit Model Competition data.")
            competition_name = input("Competition name: ")
            competition_description = input("Competition description: ")
            data_description = input("Competition data description: ")
            data_license = input("Cometition data license: ")

        comp_input_dict = {"competition_name": competition_name,
                           "competition_description": competition_description,
                           "data_description": data_description,
                           "data_license": data_license}

        with HiddenPrints():

            from aimodelshare.generatemodelapi import create_competition
            create_competition(apiurl=self.playground_url,
                               data_directory=data_directory,
                               y_test=eval_data,
                               eval_metric_filepath=eval_metric_filepath,
                               email_list=email_list,
                               public=public,
                               public_private_split=public_private_split,
                               input_dict=comp_input_dict,
                               print_output=False)

        if user_input == False:

            experiment_name = "Default Experiment " + unique_model_id
            experiment_description = ""
            data_description = ""
            data_license = ""

        else:
            print("Submit Model Experiment data.")
            experiment_name = input("Experiment name: ")
            experiment_description = input("Experiment description: ")
            data_description = input("Experiment data description: ")
            data_license = input("Experiment data license: ")

        exp_input_dict = {"experiment_name": experiment_name,
                          "experiment_description": experiment_description,
                          "data_description": data_description,
                          "data_license": data_license}

        with HiddenPrints():

            from aimodelshare.generatemodelapi import create_experiment
            create_experiment(apiurl=self.playground_url,
                              data_directory=data_directory,
                              y_test=eval_data,
                              eval_metric_filepath=eval_metric_filepath,
                              email_list=email_list,
                              public=public,
                              public_private_split=0, #set to 0 because its an experiment
                              input_dict=exp_input_dict,
                              print_output=False)

        print("Check out your Model Playground page for more.")

        try:
            temp.close()
        except:
            pass

        return

    def create_competition(self, data_directory, y_test, eval_metric_filepath=None, email_list=None, public=True,
                           public_private_split=0.5, input_dict=None):
        """
        Creates a model competition for a deployed prediction REST API
        Inputs : 4
        Output : Create ML model competition and allow authorized users to submit models to resulting leaderboard/competition

        Parameters:
        -----------
        `y_test` :  ``list`` of y values for test data used to generate metrics from predicted values from X test data submitted via the submit_model() function
            [REQUIRED] to generate eval metrics in competition leaderboard

        `data_directory` : folder storing training data and test data (excluding Y test data)
        `eval_metric_filepath`: [OPTIONAL] file path of zip file with custon evaluation functions
        `email_list`: [OPTIONAL] list of comma separated emails for users who are allowed to submit models to competition.  Emails should be strings in a list.
        `public`: [REQUIRED] True/false. Defaults to False.  If True, competition is public and ANY AIMODELSHARE USER CAN SUBMIT MODELS.  USE WITH CAUTION b/c one model and
            one preprocessor file will be be saved to your AWS S3 folder for each model submission.
        `public_private_split`: [REQUIRED] Float between 0 and 1. Defaults to 0.5. Porportion of test data that is allocated to private hold-out set.

        Returns:
        -----------
        finalmessage : Information such as how to submit models to competition

        """

        if email_list is None:
            email_list = []

        # catch email list error
        if public == False and email_list == []:
            raise ValueError("Please submit valid email list for private competition.")
        import os
        if os.environ.get("cloud_location") is not None:
            cloudlocation = os.environ.get("cloud_location")
        else:
            cloudlocation = "not set"
        if "model_share" == cloudlocation:
            print("Creating your Model Playground Competition...\nEst. completion: ~1 minute\n")
            if input_dict is None:
                print("\n--INPUT COMPETITION DETAILS--\n")

                aishare_competitionname = input("Enter competition name:")
                aishare_competitiondescription = input("Enter competition description:")

                print("\n--INPUT DATA DETAILS--\n")
                print(
                    "Note: (optional) Save an optional LICENSE.txt file in your competition data directory to make users aware of any restrictions on data sharing/usage.\n")

                aishare_datadescription = input(
                    "Enter data description (i.e.- filenames denoting training and test data, file types, and any subfolders where files are stored):")

                aishare_datalicense = input(
                    "Enter optional data license descriptive name (e.g.- 'MIT, Apache 2.0, CC0, Other, etc.'):")

                input_dict = {"competition_name": aishare_competitionname,
                              "competition_description": aishare_competitiondescription,
                              "data_description": aishare_datadescription, "data_license": aishare_datalicense}
            else:
                pass

            # model competition files
            def upload_comp_exp_zipfile(data_directory, y_test=None, eval_metric_filepath=None, email_list=[]):
                """
                minimally requires model_filepath, preprocessor_filepath
                """
                zipfilelist = [data_directory]

                import json
                import os
                import requests
                import pandas as pd
                if eval_metric_filepath == None:
                    pass
                else:
                    zipfilelist.append(eval_metric_filepath)

                # need to save dict pkl file with arg name and filepaths to add to zipfile

                apiurl = "https://djoehnv623.execute-api.us-east-2.amazonaws.com/prod/m"

                apiurl_eval = apiurl[:-1] + "eval"

                headers = {'Content-Type': 'application/json',
                           'authorizationToken': json.dumps({"token": os.environ.get("AWS_TOKEN"), "eval": "TEST"}), }
                post_dict = {"return_zip": "True"}
                zipfile = requests.post(apiurl_eval, headers=headers, data=json.dumps(post_dict))

                zipfileputlistofdicts = json.loads(zipfile.text)['put']

                zipfilename = list(zipfileputlistofdicts.keys())[0]

                from zipfile import ZipFile
                import os
                from os.path import basename
                import tempfile

                wkingdir = os.getcwd()

                tempdir = tempfile.gettempdir()

                zipObj = ZipFile(tempdir + "/" + zipfilename, 'w')
                # Add multiple files to the zip

                for i in zipfilelist:
                    for dirname, subdirs, files in os.walk(i):
                        zipObj.write(dirname)
                        for filename in files:
                            zipObj.write(os.path.join(dirname, filename))
                    # zipObj.write(i)

                # add object to pkl file pathway here. (saving y label data)
                import pickle

                if y_test is None:
                    pass
                else:
                    with open(tempdir + "/" + 'ytest.pkl', 'wb') as f:
                        pickle.dump(y_test, f)

                    os.chdir(tempdir)
                    zipObj.write('ytest.pkl')

                if isinstance(email_list, list):
                    with open(tempdir + "/" + 'emaillist.pkl', 'wb') as f:
                        pickle.dump(email_list, f)

                    os.chdir(tempdir)
                    zipObj.write('emaillist.pkl')
                else:
                    pass

                # close the Zip File
                os.chdir(wkingdir)

                zipObj.close()

                import ast

                finalzipdict = ast.literal_eval(zipfileputlistofdicts[zipfilename])

                url = finalzipdict['url']
                fields = finalzipdict['fields']

                #### save files from model deploy to zipfile in tempdir before loading to s3

                ### Load zipfile to s3
                with open(tempdir + "/" + zipfilename, 'rb') as f:
                    files = {'file': (tempdir + "/" + zipfilename, f)}
                    http_response = requests.post(url, data=fields, files=files)
                return zipfilename

            compzipfilename = upload_comp_exp_zipfile(data_directory, y_test, eval_metric_filepath, email_list)

            # if aws arg = false, do this, otherwise do aws code
            # create deploy code_string
            def nonecheck(objinput=""):
                if objinput is None:
                    objinput = "None"
                else:
                    objinput = "'/tmp/" + objinput + "'"
                return objinput

            playgroundurlcode = "playground_url='" + self.playground_url + "'"
            compstring = self.class_string.replace(",aws=False", "").replace("playground_url=None",
                                                                             playgroundurlcode) + "." + "create_competition('/tmp/" + data_directory + "'," + 'y_test' + "," + nonecheck(
                eval_metric_filepath) + "," + 'email_list' + ",input_dict=" + str(input_dict) + ')'

            import base64
            import requests
            import json

            api_url = "https://z4kvag4sxdnv2mvs2b6c4thzj40bxnuw.lambda-url.us-east-2.on.aws/"

            data = json.dumps({"code": """from aimodelshare import ModelPlayground;myplayground=""" + compstring,
                               "zipfilename": compzipfilename, "username": os.environ.get("username"),
                               "password": os.environ.get("password"),
                               "token": os.environ.get("JWT_AUTHORIZATION_TOKEN"), "s3keyid": "xrjpv1i7xe"})

            headers = {"Content-Type": "application/json"}

            response = requests.request("POST", api_url, headers=headers, data=data)
            result = json.loads(response.text)
            printoutlist = json.loads(result['body'])
            printoutlistfinal = printoutlist[2:len(printoutlist)]
            print("\n")
            for i in printoutlistfinal:
                print(i)

        else:

            from aimodelshare.generatemodelapi import create_competition

            competition = create_competition(self.playground_url,
                                             data_directory,
                                             y_test,
                                             eval_metric_filepath,
                                             email_list,
                                             public,
                                             public_private_split, input_dict=input_dict)
            return competition

    def create_experiment(self, data_directory, y_test, eval_metric_filepath=None, email_list=[], public=False,
                          public_private_split=0, input_dict=None):
        """
        Creates an experiment for a deployed prediction REST API
        Inputs : 4
        Output : Create ML model experiment and allows authorized users to submit models to resulting experiment tracking leaderboard

        Parameters:
        -----------
        `y_test` :  ``list`` of y values for test data used to generate metrics from predicted values from X test data submitted via the submit_model() function
            [REQUIRED] to generate eval metrics in experiment leaderboard

        `data_directory` : folder storing training data and test data (excluding Y test data)
        `eval_metric_filepath`: [OPTIONAL] file path of zip file with custon evaluation functions
        `email_list`: [OPTIONAL] list of comma separated emails for users who are allowed to submit models to experiment leaderboard.  Emails should be strings in a list.
        `public`: [REQUIRED] True/false. Defaults to False.  If True, experiment is public and ANY AIMODELSHARE USER CAN SUBMIT MODELS.  USE WITH CAUTION b/c one model and
            one preprocessor file will be be saved to your AWS S3 folder for each model submission.
        `public_private_split`: [REQUIRED] Float between 0 and 1. Defaults to 0. Porportion of test data that is allocated to private hold-out set.


        Returns:
        -----------
        finalmessage : Information such as how to submit models to experiment

        """

        # catch email list error
        if public == False and email_list == []:
            raise ValueError("Please submit valid email list for private experiment.")
        import os
        if os.environ.get("cloud_location") is not None:
            cloudlocation = os.environ.get("cloud_location")
        else:
            cloudlocation = "not set"
        if "model_share" == cloudlocation:
            print("Creating your Model Playground...\nEst. completion: ~1 minute\n")
            if input_dict is None:
                print("\n--INPUT Experiment DETAILS--\n")

                aishare_competitionname = input("Enter experiment name:")
                aishare_competitiondescription = input("Enter experiment description:")

                print("\n--INPUT DATA DETAILS--\n")
                print(
                    "Note: (optional) Save an optional LICENSE.txt file in your experiment data directory to make users aware of any restrictions on data sharing/usage.\n")

                aishare_datadescription = input(
                    "Enter data description (i.e.- filenames denoting training and test data, file types, and any subfolders where files are stored):")

                aishare_datalicense = input(
                    "Enter optional data license descriptive name (e.g.- 'MIT, Apache 2.0, CC0, Other, etc.'):")

                input_dict = {"competition_name": aishare_competitionname,
                              "competition_description": aishare_competitiondescription,
                              "data_description": aishare_datadescription, "data_license": aishare_datalicense}
            else:
                pass

            # model competition files
            def upload_comp_exp_zipfile(data_directory, y_test=None, eval_metric_filepath=None, email_list=[]):
                """
                minimally requires model_filepath, preprocessor_filepath
                """
                zipfilelist = [data_directory]

                import json
                import os
                import requests
                import pandas as pd
                if eval_metric_filepath == None:
                    pass
                else:
                    zipfilelist.append(eval_metric_filepath)

                # need to save dict pkl file with arg name and filepaths to add to zipfile

                apiurl = "https://djoehnv623.execute-api.us-east-2.amazonaws.com/prod/m"

                apiurl_eval = apiurl[:-1] + "eval"

                headers = {'Content-Type': 'application/json',
                           'authorizationToken': json.dumps({"token": os.environ.get("AWS_TOKEN"), "eval": "TEST"}), }
                post_dict = {"return_zip": "True"}
                zipfile = requests.post(apiurl_eval, headers=headers, data=json.dumps(post_dict))

                zipfileputlistofdicts = json.loads(zipfile.text)['put']

                zipfilename = list(zipfileputlistofdicts.keys())[0]

                from zipfile import ZipFile
                import os
                from os.path import basename
                import tempfile

                wkingdir = os.getcwd()

                tempdir = tempfile.gettempdir()

                zipObj = ZipFile(tempdir + "/" + zipfilename, 'w')
                # Add multiple files to the zip

                for i in zipfilelist:
                    for dirname, subdirs, files in os.walk(i):
                        zipObj.write(dirname)
                        for filename in files:
                            zipObj.write(os.path.join(dirname, filename))
                    # zipObj.write(i)

                # add object to pkl file pathway here. (saving y label data)
                import pickle

                if y_test is None:
                    pass
                else:
                    with open(tempdir + "/" + 'ytest.pkl', 'wb') as f:
                        pickle.dump(y_test, f)

                    os.chdir(tempdir)
                    zipObj.write('ytest.pkl')

                if isinstance(email_list, list):
                    with open(tempdir + "/" + 'emaillist.pkl', 'wb') as f:
                        pickle.dump(email_list, f)

                    os.chdir(tempdir)
                    zipObj.write('emaillist.pkl')
                else:
                    pass

                # close the Zip File
                os.chdir(wkingdir)

                zipObj.close()

                import ast

                finalzipdict = ast.literal_eval(zipfileputlistofdicts[zipfilename])

                url = finalzipdict['url']
                fields = finalzipdict['fields']

                #### save files from model deploy to zipfile in tempdir before loading to s3

                ### Load zipfile to s3
                with open(tempdir + "/" + zipfilename, 'rb') as f:
                    files = {'file': (tempdir + "/" + zipfilename, f)}
                    http_response = requests.post(url, data=fields, files=files)
                return zipfilename

            compzipfilename = upload_comp_exp_zipfile(data_directory, y_test, eval_metric_filepath, email_list)

            # if aws arg = false, do this, otherwise do aws code
            # create deploy code_string
            def nonecheck(objinput=""):
                if objinput == None:
                    objinput = "None"
                else:
                    objinput = "'/tmp/" + objinput + "'"
                return objinput

            playgroundurlcode = "playground_url='" + self.playground_url + "'"
            compstring = self.class_string.replace(",aws=False", "").replace("playground_url=None",
                                                                             playgroundurlcode) + "." + "create_experiment('/tmp/" + data_directory + "'," + 'y_test' + "," + nonecheck(
                eval_metric_filepath) + "," + 'email_list' + ",input_dict=" + str(input_dict) + ')'
            print(compstring)
            import base64
            import requests
            import json

            api_url = "https://z4kvag4sxdnv2mvs2b6c4thzj40bxnuw.lambda-url.us-east-2.on.aws/"

            data = json.dumps({"code": """from aimodelshare import ModelPlayground;myplayground=""" + compstring,
                               "zipfilename": compzipfilename, "username": os.environ.get("username"),
                               "password": os.environ.get("password"),
                               "token": os.environ.get("JWT_AUTHORIZATION_TOKEN"), "s3keyid": "xrjpv1i7xe"})

            headers = {"Content-Type": "application/json"}

            response = requests.request("POST", api_url, headers=headers, data=data)
            print(response.text)

            return (response.text)
        else:

            from aimodelshare.generatemodelapi import create_experiment

            experiment = create_experiment(self.playground_url,
                                           data_directory,
                                           y_test,
                                           eval_metric_filepath,
                                           email_list,
                                           public,
                                           public_private_split, input_dict=None)
            return experiment

    def submit_model(self, model, preprocessor, prediction_submission, submission_type="experiment",
                     sample_data=None, reproducibility_env_filepath=None, custom_metadata=None, input_dict=None,
                     onnx_timeout=60, model_input=None):
        """
        Submits model/preprocessor to machine learning competition using live prediction API url generated by AI Modelshare library
        The submitted model gets evaluated and compared with all existing models and a leaderboard can be generated

        Parameters:
        -----------
        `model`:  model object (sklearn, keras, pytorch, onnx) or onnx model file path
        `prediction_submission`:   one hot encoded y_pred
            value - predictions for test data
            [REQUIRED] for evaluation metrics of the submitted model
        `preprocessor`: preprocessor function object

        Returns:
        --------
        response:   Model version if the model is submitted sucessfully
        """

        if not self.playground_url:
            raise Exception(
                "Please instantiate ModelPlayground with playground_url or use create() method to setup Model Playground Page before submitting your model.")

        from aimodelshare.model import submit_model

        # convert model to onnx
        if onnx_timeout == False:
            force_onnx = True
        else:
            force_onnx = False
        model = model_to_onnx_timed(model, timeout=onnx_timeout,
                                    force_onnx=force_onnx, model_input=model_input)

        # create input dict
        if not input_dict:
            input_dict = {}
            input_dict["tags"] = input("Insert search tags to help users find your model (optional): ")
            input_dict["description"] = input("Provide any useful notes about your model (optional): ")

        if submission_type == "competition" or submission_type == "all":
            with HiddenPrints():
                competition = Competition(self.playground_url)

                version_comp, model_page = competition.submit_model(model=model,
                                                                    prediction_submission=prediction_submission,
                                                                    preprocessor=preprocessor,
                                                                    reproducibility_env_filepath=reproducibility_env_filepath,
                                                                    custom_metadata=custom_metadata,
                                                                    input_dict=input_dict,
                                                                    print_output=False)

            print(f"Your model has been submitted to competition as model version {version_comp}.")

        if submission_type == "experiment" or submission_type == "all":
            with HiddenPrints():
                experiment = Experiment(self.playground_url)

                version_exp, model_page = experiment.submit_model(model=model,
                                                                  prediction_submission=prediction_submission,
                                                                  preprocessor=preprocessor,
                                                                  reproducibility_env_filepath=reproducibility_env_filepath,
                                                                  custom_metadata=custom_metadata,
                                                                  input_dict=input_dict,
                                                                  print_output=False)

            print(f"Your model has been submitted to experiment as model version {version_exp}.")

        self.model_page = model_page

        print(f"\nVisit your Model Playground Page for more.")
        print(model_page)
        return

    def deploy_model(self, model_version, example_data, y_train, submission_type="experiment"):
        """
        Updates the prediction API behind the Model Playground with a new model from the leaderboard and verifies Model Playground performance metrics.
        Parameters:
        -----------
        `model_version`: ``int`` model version number from competition leaderboard
        `example_data`: ``Example of X data that will be shown on the online Playground page``
        `y_train`: ``training labels for classification models. Expects pandas dataframe of one hot encoded y train data``
        """

        with HiddenPrints():
            self.update_example_data(example_data)

            self.update_labels(y_train)

        self.update_runtime_model(model_version, submission_type)

        return

    def update_runtime_model(self, model_version, submission_type="experiment"):
        """
        Updates the prediction API behind the Model Playground with a new model from the leaderboard and verifies Model Playground performance metrics.
        Parameters:
        -----------
        `model_version`: ``int``
            model version number from competition leaderboard
        Returns:
        --------
        response:   success message when the model and preprocessor are updated successfully
        """
        from aimodelshare.model import update_runtime_model as update
        update = update(apiurl=self.playground_url, model_version=model_version, submission_type=submission_type)

        print(f"\nVisit your Model Playground Page for more.")
        if self.model_page:
            print(self.model_page)

        return update

    def instantiate_model(self, version=None, trained=False, reproduce=False, submission_type="experiment"):
        """
        Import a model previously submitted to a leaderboard to use in your session
        Parameters:
        -----------
        `version`: ``int``
            Model version number from competition or experiment leaderboard
        `trained`: ``bool, default=False``
            if True, a trained model is instantiated, if False, the untrained model is instantiated
        Returns:
        --------
        model: model chosen from leaderboard
        """
        raise AssertionError(
            "You are trying to Instantiate model with ModelPlayground Object, Please use the competition object to Instantiate model")
        from aimodelshare.aimsonnx import instantiate_model
        model = instantiate_model(apiurl=self.playground_url, trained=trained, version=version, reproduce=reproduce,
                                  submission_type=submission_type)
        return model

    def replicate_model(self, version=None, submission_type="experiment"):
        """
        Instantiate an untrained model with reproducibility environment setup.

        Parameters:
        -----------
        `version`: ``int``
            Model version number from competition or experiment leaderboard

        Returns:
        --------
        model:  model chosen from leaderboard
        """

        model = self.instantiate_model(version=version, trained=False, reproduce=True, submission_type=submission_type)

        return model

    def delete_deployment(self, playground_url=None, confirmation=True):
        """
        Delete all components of a Model Playground, including: AWS s3 bucket & contents,
        attached competitions, prediction REST API, and interactive Model Playground web dashboard.
        Parameters:
        -----------
        `playground_url`: ``string`` of API URL the user wishes to delete
        WARNING: User must supply high-level credentials in order to delete an API.
        Returns:
        --------
        Success message when deployment is deleted.
        """
        from aimodelshare.api import delete_deployment
        if playground_url == None:
            playground_url = self.playground_url
        deletion = delete_deployment(apiurl=playground_url, confirmation=confirmation)
        return deletion

    def import_reproducibility_env(self):
        from aimodelshare.reproducibility import import_reproducibility_env_from_model
        import_reproducibility_env_from_model(apiurl=self.playground_url)

    def update_access_list(self, email_list=[], update_type="Replace_list"):
        """
        Updates list of authenticated participants who can submit new models to a competition.
        Parameters:
        -----------
        `apiurl`: string
                URL of deployed prediction API

        `email_list`: [REQUIRED] list of comma separated emails for users who are allowed to submit models to competition.  Emails should be strings in a list.
        `update_type`:[REQUIRED] options, ``string``: 'Add', 'Remove', 'Replace_list','Get. Add appends user emails to original list, Remove deletes users from list,
                  'Replace_list' overwrites the original list with the new list provided, and Get returns the current list.
        Returns:
        --------
        response:   "Success" upon successful request
        """
        from aimodelshare.generatemodelapi import update_access_list as update_list
        update = update_list(apiurl=self.playground_url, email_list=email_list, update_type=update_type)
        return update

    def update_example_data(self, example_data):

        """
        Updates example data associated with a model playground prediction API.

        Parameters:
        -----------

        `example_data`: ``Example of X data that will be shown on the online Playground page``
        If no example data is submitted, certain functionalities may be limited, including the deployment of live prediction APIs.

        Returns:
        --------
        response:   "Success" upon successful request
        """

        from aimodelshare.generatemodelapi import _create_exampledata_json

        _create_exampledata_json(self.model_type, example_data)

        temp_dir = tempfile.gettempdir()
        exampledata_json_filepath = temp_dir + "/exampledata.json"

        from aimodelshare.aws import get_s3_iam_client
        s3, iam, region = get_s3_iam_client(os.environ.get("AWS_ACCESS_KEY_ID_AIMS"),
                                            os.environ.get("AWS_SECRET_ACCESS_KEY_AIMS"),
                                            os.environ.get("AWS_REGION_AIMS"))

        unique_model_id = self.playground_url.split(".")[0].split("//")[-1]

        s3["client"].upload_file(exampledata_json_filepath, os.environ.get("BUCKET_NAME"),
                                 unique_model_id + "/exampledata.json")

        variablename_and_type_data = extract_varnames_fromtrainingdata(example_data)

        bodydata = {"apiurl": self.playground_url,
                    "apideveloper": os.environ.get("username"),
                    "versionupdateput": "TRUE",
                    "input_feature_dtypes": variablename_and_type_data[0],
                    "input_feature_names": variablename_and_type_data[1],
                    "exampledata": "TRUE"}

        headers_with_authentication = {'Content-Type': 'application/json',
                                       'authorizationToken': os.environ.get("JWT_AUTHORIZATION_TOKEN"),
                                       'Access-Control-Allow-Headers':
                                           'Content-Type,X-Amz-Date,authorizationToken,Access-Control-Allow-Origin,X-Api-Key,X-Amz-Security-Token,Authorization',
                                       'Access-Control-Allow-Origin': '*'}
        response = requests.post("https://bhrdesksak.execute-api.us-east-1.amazonaws.com/dev/modeldata",
                                 json=bodydata, headers=headers_with_authentication)

        print("Your evaluation data has been updated.")

        print(f"\nVisit your Model Playground Page for more.")
        if self.model_page:
            print(self.model_page)

        return

    def update_labels(self, y_train):

        """
        Updates class labels associated with a model playground prediction API.
        Class labels are automatically extracted from y_train data

        Parameters:
        -----------

        `y_train`: ``training labels for classification models. Expects pandas dataframe of one hot encoded y train data``
        If no example data is submitted, certain functionalities may be limited, including the deployment of live prediction APIs.

        Returns:
        --------
        response:   "Success" upon successful request
        """

        # create labels json

        try:
            labels = y_train.columns.tolist()
        except:
            # labels = list(set(y_train.to_frame()['tags'].tolist()))
            labels = list(set(y_train))

        # labels_json = json.dumps(labels)

        temp_dir = tempfile.gettempdir()
        labels_json_filepath = temp_dir + "/labels.json"

        import json
        with open(labels_json_filepath, 'w', encoding='utf-8') as f:
            json.dump(labels, f)

        from aimodelshare.aws import get_s3_iam_client
        s3, iam, region = get_s3_iam_client(os.environ.get("AWS_ACCESS_KEY_ID_AIMS"),
                                            os.environ.get("AWS_SECRET_ACCESS_KEY_AIMS"),
                                            os.environ.get("AWS_REGION_AIMS"))

        unique_model_id = self.playground_url.split(".")[0].split("//")[-1]

        s3["client"].upload_file(labels_json_filepath, os.environ.get("BUCKET_NAME"), unique_model_id + "/labels.json")

        return

    def update_eval_data(self, eval_data):
        """
        Updates evaluation data associated with a model playground prediction API.

        Parameters:
        -----------

        `eval_data` :  ``list`` of y values used to generate metrics from predicted values from predictions submitted via the submit_model() method
            [REQUIRED] to generate eval metrics in experiment leaderboard
        """

        # create temporary folder
        temp_dir = tempfile.gettempdir()

        from aimodelshare.aws import get_s3_iam_client, run_function_on_lambda
        s3, iam, region = get_s3_iam_client(os.environ.get("AWS_ACCESS_KEY_ID_AIMS"),
                                            os.environ.get("AWS_SECRET_ACCESS_KEY_AIMS"),
                                            os.environ.get("AWS_REGION_AIMS"))

        # Get bucket and model_id subfolder for user based on apiurl {{{
        response, error = run_function_on_lambda(
            self.playground_url, **{"delete": "FALSE", "versionupdateget": "TRUE"}
        )
        if error is not None:
            raise error

        _, api_bucket, model_id = json.loads(response.content.decode("utf-8"))
        # }}}

        # upload eval_data data:
        eval_data_path = os.path.join(temp_dir, "ytest.pkl")
        import pickle
        # ytest data to load to s3

        if eval_data is not None:
            if type(eval_data) is not list:
                eval_data = eval_data.tolist()

            if all(isinstance(x, (np.float64)) for x in eval_data):
                eval_data = [float(i) for i in eval_data]

        pickle.dump(eval_data, open(eval_data_path, "wb"))
        s3["client"].upload_file(eval_data_path, os.environ.get("BUCKET_NAME"), model_id + "/experiment/ytest.pkl")
        s3["client"].upload_file(eval_data_path, os.environ.get("BUCKET_NAME"), model_id + "/competition/ytest.pkl")

        print("Your evaluation data has been updated.")

        print(f"\nVisit your Model Playground Page for more.")
        if self.model_page:
            print(self.model_page)

    def get_leaderboard(self, verbose=3, columns=None, submission_type="experiment"):
        """
        Get current competition leaderboard to rank all submitted models.
        Use in conjuction with stylize_leaderboard to visualize data.

        Parameters:
        -----------
        `verbose` : optional, ``int``
            controls the verbosity: the higher, the more detail
        `columns` : optional, ``list of strings``
            list of specific column names to include in the leaderboard, all else will be excluded
            performance metrics will always be displayed

        Returns:
        --------
        dictionary of leaderboard data
        """
        from aimodelshare.leaderboard import get_leaderboard
        data = get_leaderboard(verbose=verbose,
                               columns=columns,
                               apiurl=self.playground_url,
                               submission_type=submission_type)
        return data

    def stylize_leaderboard(self, leaderboard, naming_convention="keras"):
        """
        Stylizes data received from get_leaderbord.
        Parameters:
        -----------
        `leaderboard` : data dictionary object returned from get_leaderboard
        Returns:
        --------
        Formatted competition leaderboard
        """
        from aimodelshare.leaderboard import stylize_leaderboard as stylize_lead
        stylized_leaderboard = stylize_lead(leaderboard=leaderboard, naming_convention=naming_convention)
        return stylized_leaderboard

    def compare_models(self, version_list="None", by_model_type=None, best_model=None, verbose=1,
                       naming_convention=None, submission_type="experiment"):
        """
        Compare the structure of two or more models submitted to a competition leaderboard.
        Use in conjunction with stylize_compare to visualize data.

        Parameters:
        -----------
        `version_list` = ``list of int``
            list of model version numbers to compare (previously submitted to competition leaderboard)
        `verbose` = ``int``
            controls the verbosity: the higher, the more detail

        Returns:
        --------
        data : dictionary of model comparison information
        """
        from aimodelshare.aimsonnx import compare_models as compare
        data = compare(apiurl=self.playground_url,
                       version_list=version_list,
                       by_model_type=by_model_type,
                       best_model=best_model,
                       verbose=verbose,
                       naming_convention=naming_convention,
                       submission_type=submission_type)
        return data

    def stylize_compare(self, compare_dict, naming_convention="keras"):
        """
        Stylizes data received from compare_models to highlight similarities & differences.
        Parameters:
        -----------
        `compare_dict` = dictionary of model data from compare_models

        Returns:
        --------
        formatted table of model comparisons
        """
        from aimodelshare.aimsonnx import stylize_model_comparison
        stylized_compare = stylize_model_comparison(comp_dict_out=compare_dict, naming_convention=naming_convention)
        return (stylized_compare)

    def instantiate_model(self, version=None, trained=False, reproduce=False, submission_type="experiment"):
        """
        Import a model previously submitted to the competition leaderboard to use in your session
        Parameters:
        -----------
        `version`: ``int``
            Model version number from competition leaderboard
        `trained`: ``bool, default=False``
            if True, a trained model is instantiated, if False, the untrained model is instantiated

        Returns:
        --------
        model: model chosen from leaderboard
        """
        from aimodelshare.aimsonnx import instantiate_model
        model = instantiate_model(apiurl=self.playground_url, trained=trained, version=version,
                                  reproduce=reproduce, submission_type=submission_type)
        return model

    def inspect_eval_data(self, submission_type="experiment"):
        """
        Examines structure of evaluation data to hep users understand how to submit models to the competition leaderboad.
        Parameters:
        ------------
        None

        Returns:
        --------
        dictionary of a competition's y-test metadata
        """
        from aimodelshare.aimsonnx import inspect_y_test
        data = inspect_y_test(apiurl=self.playground_url, submission_type=submission_type)
        return data


class Competition:
    """
    Parameters:
    ----------
    `playground_url`: playground_url attribute of ModelPlayground class or ``string``
        of existing ModelPlayground URL
    """

    submission_type = "competition"

    def __init__(self, playground_url):
        self.playground_url = playground_url

    def __str__(self):
        return f"Competition class instance for playground: {self.playground_url}"

    def submit_model(self, model, preprocessor, prediction_submission,
                     sample_data=None, reproducibility_env_filepath=None, custom_metadata=None, input_dict=None,
                     print_output=True, onnx_timeout=60, model_input=None):
        """
        Submits model/preprocessor to machine learning competition using live prediction API url generated by AI Modelshare library
        The submitted model gets evaluated and compared with all existing models and a leaderboard can be generated

        Parameters:
        -----------
        `model_filepath`:  ``string`` ends with '.onnx'
            value - Absolute path to model file [REQUIRED] to be set by the user
            .onnx is the only accepted model file extension
            "example_model.onnx" filename for file in directory.
            "/User/xyz/model/example_model.onnx" absolute path to model file from local directory
        `prediction_submission`:   one hot encoded y_pred
            value - predictions for test data
            [REQUIRED] for evaluation metrics of the submitted model
        `preprocessor_filepath`:   ``string``, default=None
            value - absolute path to preprocessor file
            [REQUIRED] to be set by the user
            "./preprocessor.zip"
            searches for an exported zip preprocessor file in the current directory
            file is generated from preprocessor module using export_preprocessor function from the AI Modelshare library

        Returns:
        --------
        response:   Model version if the model is submitted sucessfully
        """

        # convert model to onnx
        if onnx_timeout == False:
            force_onnx = True
        else:
            force_onnx = False

        with HiddenPrints():
            model = model_to_onnx_timed(model, timeout=onnx_timeout,
                                        force_onnx=force_onnx, model_input=model_input)

        from aimodelshare.model import submit_model
        submission = submit_model(model_filepath=model,
                                  apiurl=self.playground_url,
                                  prediction_submission=prediction_submission,
                                  preprocessor=preprocessor,
                                  reproducibility_env_filepath=reproducibility_env_filepath,
                                  custom_metadata=custom_metadata,
                                  submission_type=self.submission_type,
                                  input_dict=input_dict,
                                  print_output=print_output)

        return submission

    def instantiate_model(self, version=None, trained=False, reproduce=False):
        """
        Import a model previously submitted to the competition leaderboard to use in your session
        Parameters:
        -----------
        `version`: ``int``
            Model version number from competition leaderboard
        `trained`: ``bool, default=False``
            if True, a trained model is instantiated, if False, the untrained model is instantiated

        Returns:
        --------
        model: model chosen from leaderboard
        """
        from aimodelshare.aimsonnx import instantiate_model
        model = instantiate_model(apiurl=self.playground_url, trained=trained, version=version,
                                  reproduce=reproduce, submission_type=self.submission_type)
        return model

    def replicate_model(self, version=None):
        """
        Instantiate an untrained model previously submitted to the competition leaderboard with its reproducibility environment setup.

        Parameters:
        -----------
        `version`: ``int``
            Model version number from competition or experiment leaderboard

        Returns:
        --------
        model:  model chosen from leaderboard
        """

        model = self.instantiate_model(version=version, trained=False, reproduce=True)
        return model

    def set_model_reproducibility_env(self, version=None):
        """
        Set the reproducibility environment prior to instantiating an untrained model previously submitted to the competition leaderboard.

        Parameters:
        -----------
        `version`: ``int``
            Model version number from competition or experiment leaderboard

        Returns:
        --------
        Sets environment according to reproducibility.json from model if present.
        """
        from aimodelshare.reproducibility import import_reproducibility_env_from_competition_model
        import_reproducibility_env_from_competition_model(apiurl=self.playground_url, version=version,
                                                          submission_type=self.submission_type)

    def inspect_model(self, version=None, naming_convention=None):
        """
        Examine structure of model submitted to a competition leaderboard
        Parameters:
        ----------
        `version` : ``int``
            Model version number from competition leaderboard

        Returns:
        --------
        inspect_pd : dictionary of model summary & metadata
        """
        from aimodelshare.aimsonnx import inspect_model

        inspect_pd = inspect_model(apiurl=self.playground_url, version=version,
                                   naming_convention=naming_convention, submission_type=self.submission_type)

        return inspect_pd

    def compare_models(self, version_list="None", by_model_type=None, best_model=None, verbose=1,
                       naming_convention=None):
        """
        Compare the structure of two or more models submitted to a competition leaderboard.
        Use in conjuction with stylize_compare to visualize data.

        Parameters:
        -----------
        `version_list` = ``list of int``
            list of model version numbers to compare (previously submitted to competition leaderboard)
        `verbose` = ``int``
            controls the verbosity: the higher, the more detail

        Returns:
        --------
        data : dictionary of model comparison information
        """
        from aimodelshare.aimsonnx import compare_models as compare
        data = compare(apiurl=self.playground_url,
                       version_list=version_list,
                       by_model_type=by_model_type,
                       best_model=best_model,
                       verbose=verbose,
                       naming_convention=naming_convention,
                       submission_type=self.submission_type)
        return data

    def stylize_compare(self, compare_dict, naming_convention="keras"):
        """
        Stylizes data received from compare_models to highlight similarities & differences.
        Parameters:
        -----------
        `compare_dict` = dictionary of model data from compare_models

        Returns:
        --------
        formatted table of model comparisons
        """
        from aimodelshare.aimsonnx import stylize_model_comparison
        stylized_compare = stylize_model_comparison(comp_dict_out=compare_dict, naming_convention=naming_convention)
        return (stylized_compare)

    def inspect_y_test(self):
        """
        Examines structure of y-test data to hep users understand how to submit models to the competition leaderboad.
        Parameters:
        ------------
        None

        Returns:
        --------
        dictionary of a competition's y-test metadata
        """
        from aimodelshare.aimsonnx import inspect_y_test
        data = inspect_y_test(apiurl=self.playground_url, submission_type=self.submission_type)
        return data

    def get_leaderboard(self, verbose=3, columns=None):
        """
        Get current competition leaderboard to rank all submitted models.
        Use in conjuction with stylize_leaderboard to visualize data.

        Parameters:
        -----------
        `verbose` : optional, ``int``
            controls the verbosity: the higher, the more detail
        `columns` : optional, ``list of strings``
            list of specific column names to include in the leaderboard, all else will be excluded
            performance metrics will always be displayed

        Returns:
        --------
        dictionary of leaderboard data
        """
        from aimodelshare.leaderboard import get_leaderboard
        data = get_leaderboard(verbose=verbose,
                               columns=columns,
                               apiurl=self.playground_url,
                               submission_type=self.submission_type)
        return data

    def stylize_leaderboard(self, leaderboard, naming_convention="keras"):
        """
        Stylizes data received from get_leaderbord.
        Parameters:
        -----------
        `leaderboard` : data dictionary object returned from get_leaderboard
        Returns:
        --------
        Formatted competition leaderboard
        """
        from aimodelshare.leaderboard import stylize_leaderboard as stylize_lead
        stylized_leaderboard = stylize_lead(leaderboard=leaderboard, naming_convention=naming_convention)
        return stylized_leaderboard

    def update_access_list(self, email_list=[], update_type="Replace_list"):
        """
        Updates list of authenticated participants who can submit new models to a competition.
        Parameters:
        -----------
        `apiurl`: string
                URL of deployed prediction API

        `email_list`: [REQUIRED] list of comma separated emails for users who are allowed to submit models to competition.  Emails should be strings in a list.
        `update_type`:[REQUIRED] options, ``string``: 'Add', 'Remove', 'Replace_list','Get. Add appends user emails to original list, Remove deletes users from list,
                  'Replace_list' overwrites the original list with the new list provided, and Get returns the current list.
        Returns:
        --------
        response:   "Success" upon successful request
        """
        from aimodelshare.generatemodelapi import update_access_list as update_list
        update = update_list(apiurl=self.playground_url,
                             email_list=email_list, update_type=update_type,
                             submission_type=self.submission_type)
        return update


class Experiment(Competition):
    """
    Parameters:
    ----------
    `playground_url`: playground_url attribute of ModelPlayground class or ``string``
        of existing ModelPlayground URL
    """

    submission_type = "experiment"

    def __init__(self, playground_url):
        self.playground_url = playground_url

    def __str__(self):
        return f"Experiment class instance for playground: {self.playground_url}"


class Data:
    def __init__(self, data_type, playground_url=None):
        self.data_type = data_type
        self.playground_url = playground_url

    def __str__(self):
        return f"This is a description of the Data class."

    def share_dataset(self, data_directory="folder_file_path", classification="default", private="FALSE"):
        from aimodelshare.data_sharing.share_data import share_dataset as share
        response = share(data_directory=data_directory, classification=classification, private=private)
        return response

    def download_data(self, repository):
        from aimodelshare.data_sharing.download_data import download_data as download
        datadownload = download(repository)
        return datadownload
