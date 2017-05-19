import boto3
import botocore

from string import ascii_lowercase, ascii_uppercase
from random import choice
from time import time

from app.configs.s3_configs import *

class ImageHandler():

    def __init__(self):
        self.session = boto3.Session(aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
        self.client = self.session.client('s3')
        self.s3 = self.session.resource('s3')

    def get_presigned_post(self):
        file_key = ''.join([choice(ascii_uppercase + ascii_lowercase) for x in range(8)])
        while not self.check_file_exists(file_key):
            file_key = ''.join([choice(ascii_uppercase + ascii_lowercase) for x in range(8)])
            print(file_key + " already exists")

        fields = {'x-amz-acl': ACL}
        conditions = [
            {'x-amz-acl': ACL},
            ['content-length-range', 10, MAX_SIZE]  # 10Mb limit
        ]

        return self.client.generate_presigned_post(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=300  # 5 minutes from now
        )

    def check_file_exists(self, file_key):
        try:
            self.s3.Object(BUCKET_NAME, file_key).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return True
            else:
                raise
        else:
            return False

    def delete_file_by_key(self, file_key):
        bucket = self.s3.Bucket(BUCKET_NAME)

        objects_to_delete = []
        objects_to_delete.append({'Key':file_key})

        return bucket.delete_objects(
            Delete={
                'Objects':objects_to_delete
            }
        )

if __name__ == "__main__":
    imgHandler = ImageHandler()
    print imgHandler.delete_file_by_key('GojjGjRP')