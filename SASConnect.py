import saspy
import os
import json

# import boto3
# import logging
# from botocore.exceptions import ClientError

sas = saspy.SASsession()

def execute_sas_program(program_file):
    """
    Function to execute a SAS program file
    """
    with open(program_file, "r") as file:
        program = file.read()

    print(program)

    # code = open('/users/myuserid.files/SAS_filename.sas').read()
    # results_dict = sas.submit(code)
    sas.submitLST(program)

# TODO Function to convert Pandas DataFrame to JSON/Python Dictionary

def getinfo():
    """

    """
    # dbconn

    autoexec = sas.submitLST(
        """
        %include "/home/u50452179/src/getmetadata.sas";
        %getmetadata(path=%str(/home/u50452179/data));
        """)

    # cursor = dbconn.cursor()

    # TODO Upload current data path and data library name to database

    #------------------#
    # List of Datasets #
    #------------------#

    # specify SAS dataset
    outds = sas.sasdata("out_datasets", libref='work')

    # Convert the SAS dataset to pandas DataFrame
    df_ds = outds.to_df()

    # TODO Upload the list of datasets to PostgreSQL database


    # Convert the DataFrame to list of dictionaries
    data_list_ds = df_ds.to_dict('records')

    # Define the output JSON file and path
    output_ds = 'dataset_schema.json'

    # Write the data to a JSON file
    with open(output_ds, 'w') as f:
        json.dump(data_list_ds, f, indent=2)

    #-------------------#
    # List of Variables #
    #-------------------#

    # specify SAS dataset
    outds_var = sas.sasdata("outds_variables", libref = 'work')

    # Convert the SAS dataset to pandas DataFrame
    df_var = outds_var.to_df()

    # TODO Upload the list of variables to PostgreSQL database

    # Convert DataFrame to list of dictionaries
    data_list_var = df_var.to_dict('records')

    # Define the output JSON file and path
    output_var = 'dataset_variable_schema.json'

    # Write the data to a JSON file
    with open(output_var, 'w') as f:
        json.dump(data_list_var, f, indent=2)

    #--------------------#
    # List of Parameters #
    #--------------------#

    # specify SAS dataset
    outds_ept = sas.sasdata("outds_endpoints", libref='work')

    # Convert the SAS dataset to pandas DataFrame
    df_ept = outds_ept.to_df()

    # TODO Upload the list of parameters to PostgreSQL database

    # Convert DataFrame to list of dictionaries
    data_list_ept = df_ept.to_dict('records')

    # Define the output JSON file and path
    output_ept = 'dataset_endpoint_schema.json'

    # Write the data to a JSON file
    with open(output_ept, 'w') as f:
        json.dump(data_list_ept, f, indent=2)

    #--------------------#
    # List of Population #
    #--------------------#

    # specify SAS dataset
    outds_popuvar = sas.sasdata("outds_popuvar", libref = 'work')

    # Convert the SAS dataset to pandas DataFrame
    df_popuvar = outds_popuvar.to_df()

    # TODO Upload the list of variables to PostgreSQL database

    # Convert DataFrame to list of dictionaries
    data_list_popuvar = df_popuvar.to_dict('records')

    # Define the output JSON file and path
    output_popuvar = 'dataset_population_schema.json'

    # Write the data to a JSON file
    with open(output_popuvar, 'w') as f:
        json.dump(data_list_popuvar, f, indent=2)

    #-------------------#
    # List of Covariate #
    #-------------------#

    # specify SAS dataset
    outds_covar = sas.sasdata("outds_covar", libref = 'work')

    # Convert the SAS dataset to pandas DataFrame
    df_covar = outds_covar.to_df()

    # TODO Upload the list of variables to PostgreSQL database

    # Convert DataFrame to list of dictionaries
    data_list_covar = df_covar.to_dict('records')

    # Define the output JSON file and path
    output_covar = 'dataset_covariate_schema.json'

    # Write the data to a JSON file
    with open(output_covar, 'w') as f:
        json.dump(data_list_covar, f, indent=2)

    #---------------------------#
    # List of Response Variable #
    #---------------------------#

    # specify SAS dataset
    outds_rspvar = sas.sasdata("outds_rspvar", libref = 'work')

    # Convert the SAS dataset to pandas DataFrame
    df_rspvar = outds_rspvar.to_df()

    # TODO Upload the list of variables to PostgreSQL database

    # Convert DataFrame to list of dictionaries
    data_list_rspvar = df_rspvar.to_dict('records')

    # Define the output JSON file and path
    output_rspvar = 'dataset_rspvar_schema.json'

    # Write the data to a JSON file
    with open(output_rspvar, 'w') as f:
        json.dump(data_list_rspvar, f, indent=2)

def download(file, output):
    """
    Download file from SAS remote server

    :param file: File to download from SAS server
    :param output: Output file name
    :return: True if the file is downloaded successfully
    """
    # local_file = os.path.expanduser("~/Dropbox/Workspace/") + output
    local_file = output
    remote_file = "/home/u50452179/output/" + file
    return sas.download(local_file, remotefile=remote_file)

def upload_file(file_name, bucket="llm-integration", object_name=None, region="us-east-2", folder="output"):
    """
    Upload a file to an S3 bucket (code from AWS)

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :param region: AWS S3 region name
    :param folder: Destination folder name
    :return: True if file was uploaded, else False
    """
    # TODO Add Procedures to Save to AWS S3 Directly

    include(macro_name="upload_file_aws")
    sas.submitLST(f"%upload_file_aws(filename=%str({file_name}));")

    # -------------------------------------------------- #
    # If S3 object_name was not specified, use file_name #
    # -------------------------------------------------- #
    # if object_name is None:
    #     object_name = os.path.basename(file_name)

    # --------------- #
    # Upload the file #
    # --------------- #
    # s3_client = boto3.client('s3')
    # try:
    #     response = s3_client.upload_file(file_name, bucket, object_name)
    # except ClientError as e:
    #     logging.error(e)
    #     return False

    # TODO add folder later
    return f"https://{bucket}.s3.{region}.amazonaws.com/{file_name}"

def include(macro_name):
    sas.submitLST(f"%include '/home/u50452179/src/{macro_name}.sas';")

def include_analysis(analysis_method):
    """
    Include certain SAS file in the session
    """
    method = analysis_method.lower()
    include(f"{method}_macro")

def data_library(ads_location="/home/u50452179/data"):
    """
    Add data library location for the upcoming analysis
    """
    sas.submitLST(f"libname ads '{ads_location}';")

def find_data(analysis_details):
    """
    Find corresponding analysis datasets according to user's request
    """
    # TODO Fill in details to find analysis dataset according to endpoint
    return "ADQSNPIX"

def execute_analysis(analysis_details):
    """
    Execute the analysis according to the user-defined analysis details
    """
    print(analysis_details)

    analysis_method = analysis_details["AnalysisMethod"]

    include_analysis(analysis_method)
    data_library()

    filename = analysis_method + "_" + analysis_details["UserID"] + "_" + str(analysis_details["SessionID"])

    f = open("generated/" + filename + ".sas", "w")
    f.write(f"%{analysis_method}(inds={find_data(analysis_details)}")
    for key, value in analysis_details['Parameters'].items():
        f.write(f",{key}={value}")
    f.write(f",filename=%str({filename})")
    f.write(");")
    f.close()

    execute_sas_program("generated/" + filename + ".sas")

    aws_url = upload_file(filename + ".pdf")

    return aws_url

if __name__ == "__main__":
    # test for download functionality
    # x = download("input.txt", "output.txt")
    # print(x)
    # print(x['Success'])
    # print(x['LOG'])
    #
    # s3 = boto3.client('s3')
    # url = upload_file("output.txt", "llm-integration")
    # print(url)

    # test for getinfo()
    getinfo()