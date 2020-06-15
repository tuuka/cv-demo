import psutil
import fnmatch
import os
import random
from flask import url_for, current_app as app


def get_mode_img_filename(mode):
    filename = random.choice([f for f in os.listdir(os.path.join(app.static_folder, 'images'))
           if fnmatch.fnmatch(f, f'*{mode}*.jpg')])
    return url_for('static', filename='images/' + filename)

def get_text_from_babel_file(filename):
    with open(os.path.join(app.static_folder, 'text', filename)) as f:
        content = f.readlines()
        content = [x.strip().strip("_('").strip("')") for x in content]
    return content


# from app import aws_boto
# from botocore.exceptions import ClientError
# import json, time

def print_memory():
    def round_to_mb(v):
        return round(v / 1024 / 1024, 2)

    mem = round_to_mb(psutil.Process(os.getpid()).memory_info().rss)
    all_mem = round_to_mb(psutil.virtual_memory().available)
    app.logger.info(f'RAM: {all_mem}MB; Process size: {mem}MB')


def print_lambda_timings(r=None):
    try:
        timings = r.get('time', None)
        app.logger.info(f'All Lambda invokation time: {timings["all_time"]}sec; '
                        f'prediction itself: {timings["model_prediction_time"]}sec.')
    except Exception as e:
        app.logger.info(f'Cannot extract time data from response. Error: {e}.')


'''
def invoke_lambda_function_synchronous(name, parameters, region_name='us-west-2'):
    """Invoke a Lambda function synchronously
    :param name: Lambda function name or ARN or partial ARN
    :param parameters: Dict of parameters and values to pass to function
    :return: Dict of response parameters and values. If error, returns None.
    """
    t = time.time()
    # Convert the parameters from dict -> string -> bytes
    params_bytes = json.dumps(parameters).encode()

    # Invoke the Lambda function
    #lambda_client = boto3.client('lambda', region_name=region_name)

    try:
        response = aws_boto.clients['lambda'].invoke(FunctionName=name,
                                        InvocationType='RequestResponse',
                                        LogType='Tail',
                                        Payload=params_bytes)
    except ClientError as e:
        app.logger.error(e)
        return None
    print(f'Lambda invokation time: {round(time.time() - t,2)} sec')
    return response
'''
