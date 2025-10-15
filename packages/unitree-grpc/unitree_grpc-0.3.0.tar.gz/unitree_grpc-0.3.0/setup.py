from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
import os
import subprocess

class BuildPy(build_py):
    def run(self):
        # 编译 proto 文件
        proto_file = os.path.join(os.path.dirname(__file__), "unitree", "pingpong.proto")
        subprocess.run([
            "python", "-m", "grpc_tools.protoc",
            "-I.",
            f"--python_out={os.path.dirname(proto_file)}",
            f"--grpc_python_out={os.path.dirname(proto_file)}",
            proto_file
        ], check=True)
        super().run()

setup(
    name='unitree_grpc',
    version='0.3.0',
    packages=find_packages(),
    install_requires=[
        'grpcio',
        'grpcio-tools',
        'pyQt5'
    ],
    cmdclass={
        'build_py': BuildPy,
    },
    entry_points={
        'console_scripts': [
            'unitree-server=unitree.server.simpleserver:serve',
            'unitree-client=unitree.client.simpleclient:run',
        ],
    },
    author='Sukuna',
    author_email='sukunahust@foxmail.com',
    description='A gRPC service for Unitree',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://sukunahust.moe',
    license='MIT',
)