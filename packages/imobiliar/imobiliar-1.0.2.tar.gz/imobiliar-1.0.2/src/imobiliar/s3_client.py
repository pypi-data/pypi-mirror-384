import boto3, os

class ClientS3:
    def __init__(self):
        self._s3 = None
        pass
    
    def login(self, access_key: str, secret_key: str):
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        self._s3 = session.client("s3")
        
    def upload_file(self, bucket: str, filepath:str):
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            self._s3.upload_fileobj(  
                f,
                Bucket=bucket,
                Key=filename,
                ExtraArgs={"ContentType": "application/pdf"}
            )
