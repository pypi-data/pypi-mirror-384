from setuptools import setup, find_packages

def get_libraries():
    import pathlib, sys
    file = open(pathlib.Path(sys.argv[0]).parent.resolve() / 'libraries.txt', 'r')
    return file.readlines()

setup(name='flask-ban-states', version='1.0', description='Библиотека для удобной блокировки людей по стране.', long_description='Крайне простая библиотека: инициализируйте класс - и готово! (Впишите список заблокированных кодов стран, тип ответа при 403, и сам ответ. JSON/HTML)', author='florestdev', author_email='florestone4185@internet.ru', packages=find_packages(), python_requires='>=3.10', project_urls={"Social Resources": 'https://taplink.cc/florestone4185', 'Flask':"https://pypi.org/project/Flask/", "GitHub":"https://github.com/florestdev/flaskbannerstates"}, install_requires=get_libraries())