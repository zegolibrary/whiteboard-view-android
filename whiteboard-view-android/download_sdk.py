import os
import json
import sys
import shutil
import urllib2
import zipfile
import tarfile
import subprocess
import ssl
import argparse

WB_PROJECT_NEW_URL = 'https://artifact-master.zego.cloud/generic/whiteboard/public/android/ZegoWhiteboardView/{}/{}/zegowhiteboardview_android.zip?version={}'
WB_BRANCH_TAGS = ['feature', 'hotfix', 'customer']
WB_SUB_DIR_NAMES = ['online', 'test']

THIS_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

def __parse_args(args):
    args = args[1:]
    parser = argparse.ArgumentParser(description='The root build script.')

    parser.add_argument('--sdk_version', type=str, default='')

    return parser.parse_args(args)


def __unzip_file(src_zip_file, dst_folder):
    if src_zip_file.endswith('.tar') or src_zip_file.endswith('.gz'):
        with tarfile.open(src_zip_file, 'r:gz') as f:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner) 
                
            
            safe_extract(f, dst_folder)
    elif src_zip_file.endswith('.zip'):
        if sys.platform == 'win32':
            with zipfile.ZipFile(src_zip_file, 'r') as f:
                f.extractall(dst_folder)
        else:
            subprocess.check_call(['unzip', '-o', '-q', src_zip_file, '-d', dst_folder])


def main(argv):
    args = __parse_args(argv)
    print("arguments: {}".format(args))
    print(sys.version)

    if len(args.sdk_version) == 0:
        raise Exception("SDK URL must not be EMPTY!")

    dst_libs_path = os.path.join(THIS_SCRIPT_PATH, '..', 'whiteboardviewsdk')

    for branch_tag in WB_BRANCH_TAGS:
        u = None
        for sub_dir in WB_SUB_DIR_NAMES:
            oss_url = WB_PROJECT_NEW_URL.format(branch_tag, sub_dir, args.sdk_version)
            artifact_name = oss_url.split('/')[-1]
            artifact_name = artifact_name.split('?')[0] # remove url version
            try:
                request = urllib2.Request(oss_url)
                print('\n --> Request: "{}"'.format(oss_url))
                context = ssl._create_unverified_context()
                u = urllib2.urlopen(request, context=context)
                print(' <-- Response: {}'.format(u.code))
            except :
                pass
        if u is not None and u.code == 200:
            break

    artifact_path = os.path.join(THIS_SCRIPT_PATH, artifact_name)
    with open(artifact_path, 'wb') as fw:
        fw.write(u.read())

    tmp_dst_unzip_folder = os.path.join(THIS_SCRIPT_PATH, '__tmp__')
    __unzip_file(artifact_path, tmp_dst_unzip_folder)

    for folder in os.listdir(tmp_dst_unzip_folder):
        product_folder = os.path.join(tmp_dst_unzip_folder, folder)
        if os.path.isdir(product_folder):
            for f in os.listdir(product_folder):
                shutil.copy(os.path.join(product_folder, f), os.path.join(dst_libs_path))
            break

    print("Download SDK success")

    shutil.rmtree(tmp_dst_unzip_folder, ignore_errors=True)
    os.remove(artifact_path)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
