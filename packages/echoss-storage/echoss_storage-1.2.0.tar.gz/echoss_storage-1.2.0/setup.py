from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

package_name = "echoss_storage"

setup(
    name='echoss-storage',
    version='1.2.0',
    url='',
    install_requires=['boto3>=1.19.0,<2.0', 'opencv-python~=4.8.0.74', 'numpy>=1.22.3', 'tqdm>=4.63.2', 'pillow~=10.1.0', 'echoss-fileformat>=1.1.0'],
    license='',
    author='ckkim',
    author_email='ckkim@12cm.co.kr',
    description='echoss AI Bigdata Solution - Object Storage like S3 handler',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    keywords=['echoss', 'object storage', 's3handler', 's3_handler'],
    package_data={},
    python_requires= '>3.7',
)
