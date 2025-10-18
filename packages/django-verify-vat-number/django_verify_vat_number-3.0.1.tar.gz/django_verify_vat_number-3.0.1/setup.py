from distutils.command.build import build

from setuptools import setup


class custom_build(build):
    sub_commands = [('compile_catalog', lambda x: True)] + build.sub_commands


setup(cmdclass={'build': custom_build})
