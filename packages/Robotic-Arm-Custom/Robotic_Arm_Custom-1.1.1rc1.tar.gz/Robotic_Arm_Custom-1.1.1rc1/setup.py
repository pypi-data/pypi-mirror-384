from setuptools import setup, find_packages
import setuptools.command.build_py
import os

# 自定义构建命令来排除特定模块
class CustomBuildPyCommand(setuptools.command.build_py.build_py):
    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        return [
            (pkg, mod, file)
            for (pkg, mod, file) in modules
            if mod != 'rm_robot_interface_internal'  # 排除指定模块
        ]
setup(
    name='Robotic_Arm_Custom',
    version='1.1.1.c1',
    # url='https://github.com/your_username/your_package_name',
    license='MIT',
    author='RM_Poppy',
    author_email='poppy@realman-robot.com',
    # description='',
    # 假设你有一个README.md文件
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        # 你的包所依赖的其他Python包列表
    ],

    include_package_data=True,
    packages=find_packages(include=['Robotic_Arm']), 
    python_requires=">=3.9",

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    cmdclass={
        'build_py': CustomBuildPyCommand,  # 使用自定义构建命令
    }
    # package_data={
    #     'libs': ['linux_arm/*', 'linux_x86/*.so', 'win_32/*.dll', 'win_64/*.dll'],
    # },
    # ... 其他参数 ...
)
