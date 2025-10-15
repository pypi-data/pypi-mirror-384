from setuptools import setup, find_packages

def get_libraries():
    import pathlib, sys
    file = open(pathlib.Path(sys.argv[0]).parent.resolve() / 'libraries.txt', 'r')
    return file.readlines()

setup(name='florestmessangerapi', version='1.7', description='API для FlorestMessanger (BOT).', long_description='Документация API на сайте: https://florestmsgs-florestdev4185.amvera.io/api_docs', author='florestdev', author_email='florestone4185@internet.ru', packages=find_packages(), python_requires='>=3.10', project_urls={"Social Resources": 'https://taplink.cc/florestone4185', 'Messanger':"https://florestmsgs-florestdev4185.amvera.io/chat", 'API Docs':"https://florestmsgs-florestdev4185.amvera.io/api_docs"}, install_requires=get_libraries())