from setuptools import setup, find_packages

setup(
    name='tools-collections-python',
    version='0.0.2',
    packages=find_packages(),
    install_requires=[
        # 依赖列表
    ],
    author='pikad',
    author_email='1195628604@qq.com',
    description='tools for some open-source projects',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://gitee.com/itdqj/tools-collections-python',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)
