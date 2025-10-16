# v1.1.3 change package name from echoss_s3handler to echoss_storage and use echoss-fileformat
# v1.1.4 remove S3ClientHandler, add S3ResourceFileView class, change internal implementation
- initial config: str or dict
- add internal class S3ResouceFileView as return object get_object_file()
- move read_file() to S3ResouceFileView as_json() or as_text()
- move read_image() to S3ResouceFileView as_pil_image() or as as_cv2_image()
# v1.1.6 hot fix as_pil_image() and add get_content_type() and is_image()


#  install 방법
pip install -U echoss-storage

## import 방법
```python
from echoss_storage import S3ResourceHandler

```

custom yolov7과 image_utils의 함수 사용시 S3에 있는 데이터를 사용하고자 하여 만든 Class

# Resource Class
내부 주요 함수
```
    # s3 config 파일 읽기
    s3_config = "../s3 config file path/ai_solution_dataset_test.yaml"
    # class 할당
    s3_resource = S3ResourceHandler(config, env=None)
    
    s3_resource.get_bucket_list(data_info=False)
     - 현재 config 파일에 해당하는 접속 계정에 있는 bucket들의 정보를 출력해준다.(버킷명, 버킷 생성날짜 등)
     - data_info를 True로 하게 되면 출력이 버킷명이 key값, 마지막 생성일자를 vlaue로 하는 Dict형태로 출력되며,
     false로 하면 버킷의 목록만 list형태로 출력.
    
    s3_resource.get_object_info(bucket, file_path)
     - parameter로 입력된 object의 마지막 수정일시(YYYY-MM-DD HH:MM:SS 꼴)와 s3link를 출력해준다.
  
    s3_resource.get_object_list(bucket, s3_prefix, after_ts=0, pattern=None, tqdm_=True)
     - s3_prefix는 버킷 이후 공통되는 경로 입력
     - after_ts는 입력된 이후 추가/수정된 데이터만 추리기 위함(포맷 : "2023-02-28 00:00:00")
     - patter은 확장자와 같은 부분
     - object들의 path를 list로 반환한다.
    
    s3_resource.download_object(bucket_name, target_file_path, download_file_path)
     - S3에 있는 object를 local에 다운로드하기 위한 함수
     - target_file_path는 다운로드 하고자하는 버킷 내의 object 경로
     - download_file_path는 로컬에 다운받고자 하는 경로 입력(파일의 이름 포함)
    
    s3_resource.upload_object(bucket_name, target_file_path, upload_file_path, ExtraArgs=None)
     - locla에 있는 데이터를 S3에 업로드하기 위한 함수
     - target_file_path는 업로드 하고자하는 로컬의 파일 경로
     - upload_file_path는 s3에 업로드 하고자하는 경로
     - ExtraArgs는 metadata 예를들어 {'ContentType': "video/mp4", 'ACL': "public-read"}위와 같이 입력
    
    s3_resource.put_object(object_body, object_name, trg_bucket)
     - 메모리상으로 저장되어있는 json혹은 txt 데이터를 S3 object로 업로드하는데 사용하는 함수
     - object_body는 메모리 상으로 저장되어 있는 데이터
     - object_name은 업로드 하고자하는 경로및 파일명의 path
     - trg_bucket은 업로드 하고자하는 버킷명
     - 이미지도 업로드할 수 있으나 이때에는 아래와 같이 이미지를 PIL, io라이브러리를 이용하여 가공한 뒤 업로드를 해야합니다.
        img0 = Image.fromarray(im0, mode='RGB')
        out_img = io.BytesIO()
        img0.save(out_img, format='png')
        out_img.seek(0)
    
    s3_resource.s3tos3_put_object(src_file_name, trg_file_name, trg_s3_config, fin_print=True)
     - 서로 다른 S3계정간의 데이터를 local에 따로 다운로드 한 뒤 업로드 하는 것이 아닌 메모리상으로 불러 업로드하는 함수
     - src_file_name은 옮기고자하는 s3 파일의 전체 경로(버킷명은 안적어주어도 무방 -> class를 호출할때의 config파일에서 가지고 옴)
     - trg_file_name은 옮겨가야할 s3에서의 경로 입력(파일명까지)
     - trg_s3_config는 옮겨가야할 s3의 config파일(확장자는 yaml)

    s3_resource.move_object(src_file_name, trg_file_name, bucket)
     - 같은 s3내 같은 버킷에서의 파일 이동
     - src_file_name은 원본 파일
     - trg_file_name은 이동되어야 할 경로
    
    s3_resource.read_file(bucket, file_name)
     - S3에 있는 파일을 메모리로 읽기 위한 함수
    
    s3_resource.read_image(bucket, file_name, library="cv2")
     - S3에 있는 이미지 파일을 메모리로 읽는 함수
     - 이후 사용되는 이미지 형식에 따라 옵션에 "cv2", "PIL"을 선택하여 사용 가능
    
```

