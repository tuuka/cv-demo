import json
import logging
import os
import zipfile
import zlib
import boto3
from botocore.exceptions import ClientError
import requests, argparse
from distutils.util import strtobool



def create_lambda_deployment_package(srcfile, deployment_package):
    """Create a Lambda deployment package (ZIP file)
    :param srcfile: Lambda function source file
    :param deployment_package: Name of generated deployment package
    :return: True if deployment package created. Otherwise, False.
    """

    # Create the deployment package
    with zipfile.ZipFile(deployment_package, mode='w',
                         compression=zipfile.ZIP_DEFLATED
                         ) as deploy_pkg:
        try:
            deploy_pkg.write(srcfile)
        except Exception as e:
            logging.error(e)
            return False
    return True


def get_iam_role_arn(iam_role_name):
    """Retrieve the ARN of the specified IAM role
    :param iam_role_name: IAM role name
    :return: If the IAM role exists, return ARN, else None
    """

    # Try to retrieve information about the role
    iam_client = boto3.client('iam')
    try:
        result = iam_client.get_role(RoleName=iam_role_name)
    except ClientError as e:
        logging.error(e)
        return None
    return result['Role']['Arn']


def iam_role_exists(iam_role_name):
    """Check if the specified IAM role exists
    :param iam_role_name: IAM role name
    :return: True if IAM role exists, else False
    """

    # Try to retrieve information about the role
    if get_iam_role_arn(iam_role_name) is None:
        return False
    return True


def create_iam_role_for_lambda(iam_role_name):
    """Create an IAM role to enable a Lambda function to call AWS services
    :param iam_role_name: Name of IAM role
    :return: ARN of IAM role. If error, returns None.
    """

    # Lambda trusted relationship policy document
    lambda_assume_role = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': '',
                'Effect': 'Allow',
                'Principal': {
                    'Service': 'lambda.amazonaws.com'
                },
                'Action': 'sts:AssumeRole'
            }
        ]
    }
    iam_client = boto3.client('iam')
    try:
        result = iam_client.create_role(RoleName=iam_role_name,
                                        AssumeRolePolicyDocument=json.dumps(lambda_assume_role))
    except ClientError as e:
        logging.error(e)
        return None
    lambda_role_arn = result['Role']['Arn']

    # Attach the AWSLambdaBasicExecutionRole (AWSLambdaExecute) policy to the role
    # If planning to use AWS X-Ray, also attach the AWSXrayWriteOnlyAccess policy
    lambda_policy_arn = 'arn:aws:iam::aws:policy/service-role/AWSLambdaExecute'
    try:
        iam_client.attach_role_policy(RoleName=iam_role_name,
                                      PolicyArn=lambda_policy_arn)
    except ClientError as e:
        logging.error(e)
        return None

    # Return the ARN of the created IAM role
    return lambda_role_arn


def get_function_arn(name,
                     region='us-west-2'):
    """Retrieve the ARN of the specified Lambda Function
    :param iam_role_name: IAM role name
    :return: If the IAM role exists, return ARN, else None
    """

    # Try to retrieve information about the role
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        result = lambda_client.get_function(FunctionName=name)
    except ClientError as e:
        logging.error(e)
        return None
    return result


def deploy_lambda_function(name,
                           iam_role,
                           handler,
                           deployment_package,
                           layers=[],
                           memory_size=2048,
                           timeout=20,
                           region='us-west-2'):
    """Deploy the Lambda function
    :param name: Descriptive Lambda function name
    :param iam_role: IAM Lambda role
    :param handler: Name of Lambda handler function
    :param deployment_package: Name of deployment package
    :param memory_size: Lambda memori size
    :param timeout: Lambda timeout
    :param region: Lambda region
    :return: Dictionary containing information about the function, else None
    """

    # Load the deployment package into memory
    # Alternatively, upload it to S3
    with open(deployment_package, mode='rb') as pkg:
        deploy_pkg = pkg.read()

    # Create the Lambda function
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        result = lambda_client.create_function(FunctionName=name,
                                               Runtime='python3.7',
                                               Role=iam_role,
                                               Handler=handler,
                                               Code={'ZipFile': deploy_pkg},
                                               Timeout=timeout,
                                               MemorySize=memory_size,
                                               Environment={
                                                   'Variables': {
                                                       'VAR1': 'var1',
                                                   }
                                               },
                                               Layers=layers
                                               #["arn:aws:lambda:us-west-2:018266177413:layer:Numpy-Pillow-ONNXruntime:1"]
                                               )
    except ClientError as e:
        logging.error(e)
        return None
    return result


def create_lambda_layer(layer_name,
                           zipfile,
                           region='us-west-2'):
    """Create a Lambda layer
    It is assumed that zipfile includes all the necessary libraries
    for function.
    :param layer_name: Lambda layer name
    :param zipfile: Lambda layer source file
    :param region: Lambda layer region
    :return: String ARN of the created Lambda layer. If error, returns None.
    """

    # Load the deployment package into memory
    # Alternatively, upload it to S3
    with open(zipfile, mode='rb') as pkg:
        deploy_pkg = pkg.read()

    # Create the Lambda function
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        microservice = lambda_client.publish_layer_version(LayerName=layer_name,
                                                     Content={
                                                         'ZipFile': deploy_pkg
                                                     },
                                                     CompatibleRuntimes=[
                                                         'python3.7', 'python3.8'
                                                     ],)
    except ClientError as e:
        logging.error(e)
        return None

    if microservice is None:
        return None
    layer_arn = microservice['LayerArn']
    logging.info(f'Created Lambda layer: {layer_name}')
    logging.info(f'ARN: {layer_arn}')
    response = lambda_client.list_layers(
        CompatibleRuntime='python3.7')['Layers']
    for layer in response:
        if layer['LayerArn'] == layer_arn:
            layer_arn = layer['LatestMatchingVersion']['LayerVersionArn']
            return layer_arn
    return None

def get_layers(layers, region='us-west-2'):
    lambda_client = boto3.client('lambda', region_name=region)
    response = lambda_client.list_layers(
                        CompatibleRuntime='python3.7')['Layers']
    existing_layers = {l['LayerName']:i for i, l in enumerate(response)}
    layers_arn = []
    for layer in layers:
        # Parse the filename and extension in srcfile
        layer_name, _ = os.path.splitext(layer)
        layer_name = layer_name.replace('_','-')
        if layer_name in existing_layers.keys():
            logging.info(f'Layer {layer_name} exists:\n'
                         f'{response[existing_layers[layer_name]]}')
            layers_arn.append(response[existing_layers[layer_name]]['LatestMatchingVersion']['LayerVersionArn'])
        else:
            result = create_lambda_layer(layer_name, layer, region)
            if result is not None:
                layers_arn.append(result)
    return layers_arn

def create_lambda_function(function_name,
                           srcfile,
                           handler_name,
                           role_name,
                           layers=[],
                           memory_size=2048,
                           timeout=20,
                           region='us-west-2'):
    """Create a Lambda function
    It is assumed that srcfile includes an extension, such as source.py or
    source.js. The filename minus the extension is used to construct the
    ZIP file deployment package, e.g., source.zip.
    If the role_name exists, the existing role is used. Otherwise, an
    appropriate role is created.
    :param function_name: Lambda function name
    :param srcfile: Lambda source file
    :param handler_name: Lambda handler name
    :param role_name: Lambda role name
    :param memory_size: Lambda memory size
    :param timeout: Lambda timeout
    :param region: Lambda region
    :return: String ARN of the created Lambda function. If error, returns None.
    """

    # Parse the filename and extension in srcfile
    filename, _ = os.path.splitext(srcfile)

    # Create a deployment package
    deployment_package = f'{filename}.zip'
    if not create_lambda_deployment_package(srcfile, deployment_package):
        return None

    # Create Lambda IAM role if necessary
    if iam_role_exists(role_name):
        # Retrieve its ARN
        iam_role_arn = get_iam_role_arn(role_name)
    else:
        iam_role_arn = create_iam_role_for_lambda(role_name)
        if iam_role_arn is None:
            # Error creating IAM role
            return None


    # Check if function allready exists
    response = get_function_arn(function_name, region)

    if response is None:
        # Deploy the Lambda function
        microservice = deploy_lambda_function(function_name, iam_role_arn,
                                              f'{filename}.{handler_name}',
                                              deployment_package,
                                              layers=layers,
                                              memory_size=memory_size,
                                              timeout=timeout,
                                              region=region)
        if microservice is None:
            return None
        lambda_arn = microservice['FunctionArn']
        logging.info(f'Created Lambda function: {function_name}')
        logging.info(f'ARN: {lambda_arn}')
    else:
        lambda_arn = response['Configuration']['FunctionArn']
        logging.info(f'Lambda function with name {function_name} exists!')
        logging.info(f'ARN: {lambda_arn}')
        if strtobool(input('Function exists. Do you want to delete it? [y/n]:')):
            if delete_lambda_function(function_name, region=region):
                logging.info(f'Lambda function with name {function_name} was deleted!')
                if strtobool(input('Do you want to delete API Gateway? [y/n]:')):
                    return 'delete_api'
            exit(0)
    return lambda_arn


def delete_lambda_function(function_name, region='us-west-2'):
    """Delete all versions of a Lambda function
    :param function_name: Lambda function to delete
    :return: True if function was deleted, else False
    """

    # Delete all versions of the Lambda function
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        lambda_client.delete_function(FunctionName=function_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def invoke_lambda_function_synchronous(name, parameters, region='us-west-2'):
    """Invoke a Lambda function synchronously
    :param name: Lambda function name or ARN or partial ARN
    :param parameters: Dict of parameters and values to pass to function
    :return: Dict of response parameters and values. If error, returns None.
    """

    # Convert the parameters from dict -> string -> bytes
    params_bytes = json.dumps(parameters).encode()

    # Invoke the Lambda function
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        response = lambda_client.invoke(FunctionName=name,
                                        InvocationType='RequestResponse',
                                        LogType='Tail',
                                        Payload=params_bytes)
    except ClientError as e:
        logging.error(e)
        return None
    return response


def get_lambda_arn(lambda_name, region='us-west-2'):
    """Retrieve the ARN of a Lambda function
    :param lambda_name: Name of Lambda function
    :return: String ARN of Lambda function. If error, returns None.
    """

    # Retrieve information about the Lambda function
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        response = lambda_client.get_function(FunctionName=lambda_name)
    except ClientError as e:
        logging.error(e)
        return None
    return response['Configuration']['FunctionArn']


def create_rest_api(api_name, lambda_name, region='us-west-2'):
    """Create a REST API for a Lambda function
    The REST API defines a child called /example and a stage called prod.
    :param api_name: Name of the REST API
    :param lambda_name: Name of existing Lambda function
    :param region: API Gateway region
    :return: URL of API. If error, returns None.
    """

    # Specify child resource name under root and stage name
    child_resource_name = 'example'
    stage_name = 'prod'

    # Create initial REST API
    api_client = boto3.client('apigateway', region_name=region)
    try:
        result = api_client.create_rest_api(name=api_name)
    except ClientError as e:
        logging.error(e)
        return None
    api_id = result['id']
    logging.info(f'Created REST API: {result["name"]}, ID: {api_id}')

    # Get the ID of the API's root resource
    try:
        result = api_client.get_resources(restApiId=api_id)
    except ClientError as e:
        logging.error(e)
        return None
    root_id = None
    for item in result['items']:
        if item['path'] == '/':
            root_id = item['id']
    if root_id is None:
        logging.error('Could not retrieve the ID of the API\'s root resource.')
        return None

    # Define a child resource called /example under the root resource
    try:
        result = api_client.create_resource(restApiId=api_id,
                                            parentId=root_id,
                                            pathPart=child_resource_name)
    except ClientError as e:
        logging.error(e)
        return None
    example_id = result['id']

    # Define an ANY method on the /example resource
    try:
        api_client.put_method(restApiId=api_id,
                              resourceId=example_id,
                              httpMethod='ANY',
                              authorizationType='NONE')
    except ClientError as e:
        logging.error(e)
        return None

    # Set the content-type of the API's ANY method response to JSON
    content_type = {'application/json': 'Empty'}
    try:
        api_client.put_method_response(restApiId=api_id,
                                       resourceId=example_id,
                                       httpMethod='ANY',
                                       statusCode='200',
                                       responseModels=content_type)
    except ClientError as e:
        logging.error(e)
        return None

    # Set the Lambda function as the destination for the ANY method
    # Extract the Lambda region and AWS account ID from the Lambda ARN
    # ARN format="arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME"
    lambda_arn = get_lambda_arn(lambda_name, region=region)
    if lambda_arn is None:
        return None
    sections = lambda_arn.split(':')
    region = sections[3]
    account_id = sections[4]
    # Construct the Lambda function's URI
    lambda_uri = f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/' \
        f'functions/{lambda_arn}/invocations'
    try:
        api_client.put_integration(restApiId=api_id,
                                   resourceId=example_id,
                                   httpMethod='ANY',
                                   type='AWS',
                                   integrationHttpMethod='POST',
                                   uri=lambda_uri)
    except ClientError as e:
        logging.error(e)
        return None

    # Set the content-type of the Lambda function to JSON
    content_type = {'application/json': ''}
    try:
        api_client.put_integration_response(restApiId=api_id,
                                            resourceId=example_id,
                                            httpMethod='ANY',
                                            statusCode='200',
                                            responseTemplates=content_type)
    except ClientError as e:
        logging.error(e)
        return None

    # Deploy the API
    try:
        api_client.create_deployment(restApiId=api_id,
                                     stageName=stage_name)
    except ClientError as e:
        logging.error(e)
        return None

    # Grant invoke permissions on the Lambda function so it can be called by
    # API Gateway.
    # Note: To retrieve the Lambda function's permissions, call
    # Lambda.Client.get_policy()
    source_arn = f'arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*/{child_resource_name}'
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        lambda_client.add_permission(FunctionName=lambda_name,
                                     StatementId=f'{lambda_name}-invoke',
                                     Action='lambda:InvokeFunction',
                                     Principal='apigateway.amazonaws.com',
                                     SourceArn=source_arn)
    except ClientError as e:
        logging.error(e)
        return None

    # Construct the API URL
    api_url = f'https://{api_id}.execute-api.{region}.amazonaws.com/{stage_name}/{child_resource_name}'
    logging.info(f'API base URL: {api_url}')
    return api_url


def get_rest_api_id(api_name, region='us-west-2'):
    """Retrieve the ID of an API Gateway REST API
    :param api_name: Name of API Gateway REST API
    :return: Retrieved API ID. If API not found or error, returns None.
    """

    # Retrieve a batch of APIs
    api_client = boto3.client('apigateway', region_name=region)
    try:
        apis = api_client.get_rest_apis()
    except ClientError as e:
        logging.error(e)
        return None

    # Search the batch
    while True:
        for api in apis['items']:
            if api['name'] == api_name:
                # Found the API we're searching for
                return api['id']

        # Is there another batch of APIs?
        if 'position' in apis:
            # Get another batch
            try:
                apis = api_client.get_rest_apis(position=apis['position'])
            except ClientError as e:
                logging.error(e)
                return None
        else:
            # API not found
            logging.error(f'API {api_name} was not found.')
            return None


def delete_rest_api(api_name, region='us-west-2'):
    """Delete an API Gateway API object, including all resources, stages, etc.
    :param api_name: Name of API object to delete
    :return: True if API was deleted, otherwise false
    """

    # Get the API's ID
    api_id = get_rest_api_id(api_name, region=region)
    if api_id is None:
        return False

    # Delete all versions of the API Gateway object and associated resources
    api_client = boto3.client('apigateway', region_name=region)
    try:
        api_client.delete_rest_api(restApiId=api_id)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def main():
    """Exercise the module's Lambda and API Gateway functions"""

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True,
                        help="lambda source code file, required!")
    parser.add_argument('-n', '--name',
                        default='lambda_handler', required=True,
                        help="lambda function name, "
                             "(must contain only letters, numbers, hyphens, or "
                             "underscores), required!")
    parser.add_argument('-ha', '--handler',
                        default='lambda_handler',
                        help="handler function name (default: 'lambda_handler')")
    parser.add_argument('-ro', '--role',
                        default='basic-lambda-role',
                        help="lambda function role name (default: 'basic-lambda-role')")
    parser.add_argument('-reg', '--region',
                        default='us-west-2',
                        help="lambda function region (default: 'us-west-2')")
    parser.add_argument('-a', '--api',
                        help="API name (default: '{lambda function name}-API')")
    parser.add_argument('-m', '--memory', type=int, default=2048,
                        help="memory size (default: 2048')")
    parser.add_argument('-t', '--timeout', type=int, default=20,
                        help="timeout, sec (default: 20')")
    parser.add_argument('-l', '--layer', action='append',
                        help="zip file with layer code")

    args = parser.parse_args()
    #print(args)

    # Set these values before running the program
    lambda_srcfile = args.source.lower()
    lambda_function_name = args.name.lower()
    lambda_handler_name = args.handler
    region = args.region.lower()
    memory_size = args.memory
    timeout = args.timeout
    lambda_role_name = args.role.lower()        # Created if doesn't exist
    # API name in API Gateway
    api_name = f'{lambda_function_name.replace("_","-")}-api' if args.api is None else args.api
    layers = [] if args.layer is None else args.layer

    # Set up logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(asctime)s: %(message)s')

    logging.info(f'Deploying Lambda function: {lambda_function_name}...')
    logging.info(f'Source file: {lambda_srcfile}')
    logging.info(f'Handler name: {lambda_handler_name}')
    logging.info(f'Region: {region}')
    logging.info(f'Memory size: {memory_size}')
    logging.info(f'Timeout: {timeout}')
    logging.info(f'Role name: {lambda_role_name}')
    logging.info(f'API name: {api_name}')
    logging.info(f'layers: {layers}')

    layers_arn=[]
    if len(layers) > 0:
        layers_arn = get_layers(layers, region=region)
        if layers_arn is None:
            exit(1)

    # Create a Lambda function
    lambda_arn = create_lambda_function(lambda_function_name,
                                        lambda_srcfile,
                                        lambda_handler_name,
                                        lambda_role_name,
                                        layers = layers_arn,
                                        memory_size=memory_size,
                                        timeout=timeout,
                                        region=region)
    if lambda_arn is None:
        exit(1)

    if lambda_arn =='delete_api':
        if delete_rest_api(api_name, region=region):
            logging.info(f'API Gateway with name {api_name} was deleted!')
        exit(0)

    # Invoke the Lambda function
    # Define parameters
    lambda_parms = {'http_verb': 'PUT',
                    'functionID': lambda_arn,
                    'parameters': {
                        'parm01': 'Lambda parameter #1',
                        'parm02': 'Lambda parameter #2',
                    }}
    response = invoke_lambda_function_synchronous(lambda_arn, lambda_parms, region=region)
    if response is None:
        exit(1)
    logging.info(f'Invoked Lambda function: {lambda_function_name}')
    logging.info(f'Status code: {response["StatusCode"]}')
    logging.info('Returned key:value pairs:')
    return_values = json.load(response['Payload'])
    for key, value in return_values.items():
        logging.info(f'  {key}: {value}')

    # Create an API Gateway frontend for the Lambda function
    api_url = create_rest_api(api_name, lambda_function_name, region=region)

    # Invoke the REST API
    # Use requests package (pip install requests)
    https_response = requests.put(api_url, data=json.dumps(lambda_parms))
    logging.info(f'API status code: {https_response.status_code}')
    logging.info(f'Returned text: {https_response.text}')

    # Clean up: Delete the API Gateway and Lambda function resources
    # Note: If an IAM role was created, it will still exist
    #delete_rest_api(api_name)
    #logging.info(f'Deleted API: {api_name}')
    #delete_lambda_function(lambda_function_name)
    #logging.info(f'Deleted Lambda function: {lambda_function_name}')


if __name__ == '__main__':
    main()