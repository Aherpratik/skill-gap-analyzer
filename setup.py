from setuptools import find_packages, setup
from typing import List


HYPEN_E_DOT = '-e .'
def get_requirements(file_path:str)->list[str]:
    """
    this will get the requirements from the requirement folder
    """
    requirements=[]
    with open(file_path) as file_obj:
        requirements=file_obj.readlines()
        [req.replace("\n","") for req in requirements]

        if HYPEN_E_DOT in requirements:
            requirements.remove(HYPEN_E_DOT)
    
    return requirements



setup(
    name="skill gap analyzer",
    version='0.0.1',
    author="Pratik",
    author_email="paher3636@gmail.com",
    packages=find_packages(),
    install_requirements=get_requirements('requirements.txt')
)