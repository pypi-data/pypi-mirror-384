import io
import os
import boto3
import botocore.response
import cv2
import json
import numpy as np
import time
import datetime
import tqdm
from PIL import Image
from typing import Union

from echoss_fileformat import FileUtil, get_logger

logger = get_logger(logger_name='echoss_storage')

def _split_s3_key(s3_key):
    key = str(s3_key)
    last_name = key.split('/')[-1]
    return key.replace(last_name, ""), last_name


# 빈문자열 체크
def _is_blank(str_data:str):
    if str_data and str_data.strip():
        return False
    return True


# print시 문자에 색을 넣을 수 있는 함수
def colorstr(*input_data):
    # Colors a string https://en.wikipedia.org/wiki/ANSI_escape_code, i.e.  colorstr('blue', 'hello world')
    *args, string = input_data if len(input_data) > 1 else ('blue', 'bold', input_data[0])  # color arguments, string
    colors = {'black': '\033[30m',  # basic colors
              'red': '\033[31m',
              'green': '\033[32m',
              'yellow': '\033[33m',
              'blue': '\033[34m',
              'magenta': '\033[35m',
              'cyan': '\033[36m',
              'white': '\033[37m',
              'bright_black': '\033[90m',  # bright colors
              'bright_red': '\033[91m',
              'bright_green': '\033[92m',
              'bright_yellow': '\033[93m',
              'bright_blue': '\033[94m',
              'bright_magenta': '\033[95m',
              'bright_cyan': '\033[96m',
              'bright_white': '\033[97m',
              'end': '\033[0m',  # misc
              'bold': '\033[1m',
              'underline': '\033[4m'}
    return ''.join(colors[x] for x in args) + f'{string}' + colors['end']


class S3ResourceHandler:
    def __init__(self, config_file:Union[str, dict], env:str=None):
        """
        :param config_file: yaml or json file_path or config dictionary
        """
        if type(config_file) == dict:
            self.config_file = config_file
        elif type(config_file) == str and os.path.exists(config_file):
            self.config_file = FileUtil.dict_load(config_file)
        else:
            logger.debug('설정 파일을 dict형식 혹은 파일의 경로로 입력해주세요.')

        if env is not None and env in self.config_file:
            self.s3_config = self.config_file[env]
        else:
            self.s3_config = self.config_file

        if 's3' in self.s3_config:
            self.s3_config = self.s3_config['s3']

        self.s3_session = boto3.Session(
            region_name=self.s3_config['region_name'],
            aws_access_key_id=self.s3_config['access_key_id'],
            aws_secret_access_key=self.s3_config['secret_access_key'])

        self.s3 = self.s3_session.resource(service_name='s3', endpoint_url=self.s3_config.get('endpoint_url'))

    def get_bucket_list(self, include_date:bool=False):
        """
        S3ClientHandler class의 get_bucket_list 함수를 사용하며,
        data_info 옵션을 사용하여
        단순히 버킷의 리스트만 출력하거나, 버킷의 생성날짜까지 확인할 수 있도록 한 함수
        :param include_date: True or False
        :return: If date_info is True -> Output : Dict,
        False -> Output : List
        """
        bucket_list_info = self.s3.buckets.all()

        if include_date:
            result_dict = {
                bucket_info.name: bucket_info.creation_date.strftime('%Y-%m-%d')
                for bucket_info in bucket_list_info
            }
            return result_dict
        else:
            result_list = [
                bucket_info.name
                for bucket_info in bucket_list_info
            ]
            return result_list

    def select_bucket(self, bucket):
        """
        s3에서 작업 하기 전 작업할 버킷을 선택하는 단계 독립적으로는 거의 사용하지 않음
        거의 아래의 함수들에 사용
        """
        s3bucket = self.s3.Bucket(bucket)
        return s3bucket

    def get_object_list(self, bucket, s3_prefix, after_ts: int or str=0, pattern=None, use_tqdm=True):
        """
        after_ts 에는 "2023-02-28 00:00:00" 포맷으로 작성해야 한다.
        :param bucket: bucket name
        :param s3_prefix: 버킷 이후 공통되는 경로
        :param after_ts: 입력되는 시간 이후 수정된 데이터만 추리기 위한 파라미터 ex) "2023-02-28 00:00:00"
        :param pattern: 예를들면 확장자
        :param use_tqdm: 예를들면 확장자
        :return:
        """
        s3bucket = self.s3.Bucket(bucket)
        object_list = s3bucket.objects.filter(Prefix=s3_prefix)

        filenames = []
        count = 0
        if use_tqdm:
            iterator = tqdm.tqdm(object_list)
        else:
            iterator = object_list

        for obj in iterator:
            count += 1
            if pattern is not None and not pattern in obj.key:
                continue

            last_modified_dt = obj.last_modified
            s3_ts = last_modified_dt.timestamp() * 1000
            if after_ts != 0:
                after_ts_ = datetime.datetime.strptime(after_ts, "%Y-%m-%d %H:%M:%S")
                after_ts__ = time.mktime(after_ts_.timetuple())*1000
            else:
                after_ts__ = after_ts
            if s3_ts > after_ts__:
                s3_path, s3_filename = _split_s3_key(obj.key)
                # directory check
                if _is_blank(s3_filename) or s3_filename.endswith("/"):
                    pass
                else:
                    filenames.append(s3_path + s3_filename)
        return filenames

    def download_object(self, bucket_name, target_file_path, download_file_path):
        """
        버킷내의 object를 로컬로 다운로드 하기 위한 함수
        :param bucket_name: 버킷명
        :param target_file_path: 다운로드 하고자하는 버킷 내의 object 이름(경로)
        :param download_file_path: 로컬에 다운로드 받고자 하는 경로(파일의 이름 포함)
        :return:
        """
        s3bucket = self.s3.Bucket(bucket_name)
        s3bucket.download_file(target_file_path, download_file_path)

    def upload_object(self, bucket_name, target_file_path, upload_file_path, ExtraArgs = None):
        """
        로컬의 파일을 s3로 업로드 하기 위한 함수
        :param bucket_name: 버킷명
        :param target_file_path: 업로드 하고자하는 로칼의 파일 경로(파일 이름 포함)
        :param upload_file_path: S3에 업로드 하고 싶은 경로(폴더 구조와 파일의 이름 포함)
        :param ExtraArgs: metadata 입력 ex. {'ContentType': "video/mp4", 'ACL': "public-read"}
        :return:
        """
        s3bucket = self.s3.Bucket(bucket_name)
        if ExtraArgs is None:
            s3bucket.upload_file(target_file_path, upload_file_path)
        else:
            s3bucket.upload_file(target_file_path, upload_file_path, ExtraArgs)

    def put_object(self, object_body, object_name, trg_bucket):
        """
        로컬의 파일을 s3로 업로드 하기 위한 함수
        이 함수는 json파일또는 txt파일을 업로드하는데 사용
        (이미지 업로드에 사용할 수 있으나 이미지의 경우 입력 데이터를 잘 넣어주어야 함)
        이미지를 업로드 하고 싶다면 yolov7/utils/detect.py 파일 164번째 줄 참고
        :param object_body: Object data
        :param object_name: The full path to upload
        :param trg_bucket: The bucket to upload
        :return:
        """
        extention = os.path.splitext(os.path.basename(object_name))[-1]
        if (extention == ".json") | (extention == "json"):
            object_body = json.dumps(object_body, indent="\t", ensure_ascii=False)
        trg_s3bucket = self.select_bucket(trg_bucket)
        trg_s3bucket.put_object(Body=object_body, Key=object_name, ACL="public-read")

    def s3tos3_put_object(self, src_file_name, trg_file_name, trg_s3_config, fin_print=True):
        """
        ex) src_s3 = S3ResourceHandler(src_s3_config)\n
        src_s3.s3tos3_put_object(Put parameters)
        :param src_file_name: File path
        :param trg_file_name: Final file path
        :param trg_s3_config: Target s3 config data, yaml data
        :param fin_print:
        :return: None
        """
        trg_s3 = S3ResourceHandler(trg_s3_config)

        # with 문으로 안전하게 open
        with self.get_object_file(self.s3_config['bucket'], src_file_name) as src_file_view:
            # 파일 확장자 검사
            ext = os.path.splitext(src_file_name)[-1].lower()

            # 확장자에 따라 읽기 방식 선택
            if ext == '.json':
                data = src_file_view.as_json()  # dict 반환
            else:
                data = src_file_view.as_bytes()  # bytes 반환

            # 데이터 업로드
            trg_s3.put_object(data, trg_file_name, trg_s3_config['bucket'])

            if fin_print:
                logger.debug(
                    f"{colorstr(self.s3_config['bucket'])}: {src_file_name} {colorstr('red', 'bold', '->')} {colorstr(trg_s3_config['bucket'])}: {trg_file_name}"
                )

    def move_object(self, src_file_name, trg_file_name, bucket, acl='public-read'):
        """
        Args:
            src_file_name(str) : 원본 파일 명(버킷명을 포함하지 않음) \n
            trg_file_name(str) : 이동 대상 경로 파일 명(버킷명을 포함하지 않음) \n
            bucket(str) : 버킷명 \n
            acl (str) : ACL
        Returns:
            src_file들을 같은 버킷 내에서 이동
        """
        try:
            copy_source = {'Bucket': bucket, 'Key': src_file_name}
            self.s3.Object(bucket, trg_file_name).copy_from(CopySource=copy_source, ACL=acl)
            self.s3.Object(bucket, src_file_name).delete()
        except Exception as e:
            logger.error(f"error moving object {src_file_name} to {trg_file_name}: {e}")
            raise

    def remove_empty_folder(self, bucket:str):
        """
        버킷 내부 Temp 폴더 속 빈 폴더들을 자동으로 삭제시키는 함수
        Args:
            bucket (str) : 버킷명
        Returns:
            빈 폴더들을 자동으로 삭제
        """
        s3_bucket = self.select_bucket(bucket)
        for obj in s3_bucket.objects.filter(Prefix='Temp/',Delimiter='/*'):
            # 폴더 객체가 없는 경우에만 삭제
            if obj.key[-1] != '/':
                continue
            prefix = obj.key
        
            # 해당 폴더의 객체 수를 세어 빈 폴더인지 확인
            num_objects = sum(1 for _ in s3_bucket.objects.filter(Prefix=prefix))
            if (num_objects > 0) and (prefix != 'Temp/'):
                print('Delete empty folder -',prefix)
                s3_bucket.objects.filter(Prefix=prefix).delete()
                continue

    def get_object_file(self, bucket:str, file_name):
        s3_object = self.s3.Object(bucket, file_name)
        return self.S3ResourceFileView(s3_object)

    class S3ResourceFileView:
        def __init__(self, s3_object):
            self.obj = s3_object
            self._body = None # Lazy Loading

        def _load_body(self):
            if self._body is None or getattr(self._body, "closed", False):
                stream_body = self.obj.get()['Body']
                if isinstance(stream_body, botocore.response.StreamingBody):
                    self._body = io.BytesIO(stream_body.read()) # 항상 BytesIO로 변환
                else:
                    self._body = stream_body  # 이미 BytesIO거나 안전한 경우
            return self._body

        def as_bytes(self):
            body = self._load_body()
            if body.seekable():
                body.seek(0)
            return body.read()

        def as_text(self, encoding='utf-8'):
            return self.as_bytes().decode(encoding)

        def as_json(self):
            return json.loads(self.as_text())

        def as_pil_image(self):
            return Image.open(io.BytesIO(self.as_bytes()))

        def as_cv2_image(self):
            np_bytes = np.asarray(bytearray(self.as_bytes()), dtype=np.uint8)
            return cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)

        def save_to_disk(self, filepath):
            with open(filepath, 'wb') as f:
                f.write(self.as_bytes())

        def seek(self, pos, whence=0):
            body = self._load_body()
            return body.seek(pos, whence)

        def tell(self):
            body = self._load_body()
            return body.tell()

        def close(self):
            if self._body and not getattr(self._body, 'closed', False):
                self._body.close()
            self._body = None

        def get_content_type(self):
            try:
                return self.obj.get()['ContentType']
            except KeyError:
                return None

        def is_image(self):
            content_type = self.get_content_type()
            if content_type:
                return content_type.startswith('image/')
            # fallback to extension check
            ext = self.obj.key.lower().split('.')[-1]
            return ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp']

        def __enter__(self):
            # with 문 시작할 때 반환할 객체
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            # with 문 끝날 때 자동으로 close 호출
            self.close()

        def __getattr__(self, name):
            """
            Delegate any undefined attribute to the original S3.Object instance.
            """
            return getattr(self.obj, name)

        def __repr__(self):
            return f"<S3ResourceFileView(bucket={self.obj.bucket_name}, key={self.obj.key})>"


    def get_object_info(self, bucket, file_path):
        """
        object의 최종 수정일시와 s3_link를 output으로 출력한다.
        출력된 값을 DB에 적재할 수 있다.
        UTC 기준이기 때문에 한국 시간(KST, UTC+9) 으로 변환하기 위해 9시간을 더하는 작업
        
        :param bucket: 버킷 명
        :param file_path: object path
        :return: (last_modified, url)
        """
        last_modified = ""
        url = None
        with self.get_object_file(bucket, file_path) as object_info:
            last_modified = last_modified = (object_info.last_modified + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
            url = "%s/%s/%s" % (self.s3_config['endpoint_url'], bucket, file_path)
        return last_modified, url


if __name__ == '__main__':
    data_dict = FileUtil.dict_load('../data/45_abalone_data/yolo_data/ai_solution_dataset_test.yaml')

    s3resource = S3ResourceHandler(data_dict)
    s3_bucket_list = s3resource.get_bucket_list()
    print(s3_bucket_list)

    # with open("../data/45_abalone_data/yolo_data/AI_Hub_s3_config.yaml") as f:
    #     aihub_data_dict = yaml.load(f, Loader=yaml.SafeLoader)
    # objects_list = s3resource.get_object_list(data_dict['bucket'], "bb_seg_data")
    # print(objects_list[0])
    # new_name = f"113.패류 종자생산(전복) 데이터/02.저작도구/{os.path.basename(objects_list[0])}"
    #
    # s3resource.s3tos3_put_object(objects_list[0], new_name, data_dict, aihub_data_dict)
    object_lists = s3resource.get_object_list(data_dict['bucket'], data_dict['yolo_data_path'], "2023-02-28 14:00:00")
    print(len(object_lists))
    object_lists = s3resource.get_object_list(data_dict['bucket'], data_dict['yolo_data_path'])
    print(len(object_lists))
    # ob_info = s3resource.get_object_info(data_dict['bucket'], object_lists[0])
    # print(ob_info)
