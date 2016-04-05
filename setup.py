try:
    from setuptools import setup
except:
    from distutils.core import setup

from distutils.command.build import build
from distutils.command.install_data import install_data
from distutils import log
from os import walk, path, listdir, makedirs
from subprocess import Popen

from morias.core import __version__

__locales__ = ('cs',)


def doc():
    with open('README.rst', 'r') as readme:
        return readme.read().strip()


def skip(name):
    return (name[0] == '.' or
            name[-1] == '~' or
            name[-4:] == '.bak')


def find_data_files(directory, targetFolder=""):
    rv = []
    for root, dirs, files in walk(directory):
        if targetFolder:
            rv.append((targetFolder + root[len(directory):],
                       list(root+'/'+f for f in files if not skip(f))))
        else:
            rv.append((root,
                       list(root+'/'+f for f in files if not skip(f))))
    return rv


class X_build(build):
    def initialize_options(self):
        build.initialize_options(self)
        self.locales = None

    def finalize_options(self):
        build.finalize_options(self)
        if self.locales is None:
            self.locales = path.join(self.build_base, 'locales')

    def run(self):
        build.run(self)             # run original build
        log.info("running build_locales")
        if self.dry_run:
            return

        if not path.exists(self.locales):
            makedirs(self.locales)
        for it in __locales__:
            dest = '%s/%s/LC_MESSAGES' % (self.locales, it)
            if not path.exists(dest):
                makedirs(dest)
            log.info('msgfmt\t%s' % it)
            proc = Popen(['msgfmt', '-o', dest+'/morias.mo',
                          'locales/%s.po' % it])
            if proc.wait() != 0:
                exit(1)


class X_install_data(install_data):
    def initialize_options(self):
        install_data.initialize_options(self)
        self.locales = None
        self.build_base = None

    def finalize_options(self):
        install_data.finalize_options(self)
        self.set_undefined_options('build', ('build_base', 'build_base'))
        if self.locales is None:
            self.locales = path.join(self.build_base, 'locales')

    def run(self):
        for it in listdir(self.locales):
            if not path.isdir(self.locales+'/'+it):
                continue
            self.data_files.append(
                find_data_files(self.locales+'/'+it,
                                'share/morias/locales'+'/'+it)[1])
        install_data.run(self)


setup(
    name="morias",
    version=__version__,
    description="Content Management System",
    author="Ondrej Tuma",
    author_email="mcbig@zeropage.cz",
    url="http://morias.zeropage.cz",
    packages=['morias', 'morias.lib', 'morias.core'],
    scripts=['morias_sdigest.py', 'morias_bcrypt.py', 'migrate_from_php.py'],
    data_files=(find_data_files('css', 'share/morias/css') +
                find_data_files('js', 'share/morias/js') +
                find_data_files('fonts', 'share/morias/fonts') +
                find_data_files('templ', 'share/morias/templ') +
                find_data_files('sql', 'share/morias/sql')),
    license="BSD",
    long_description=doc(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Natural Language :: Czech",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content"],
    requires=['poorwsgi (>= 1.6)', 'falias', 'jinja2 (>= 2.7)',
              'docutils_tinyhtmlwriter', 'unidecode', 'bcrypt',
              'pysqlite', 'PythonMagick'],
    install_requires=['PoorWSGI >= 1.6.0dev21', 'falias', 'jinja2 >= 2.7',
                      'docutils-tinyhtmlwriter', 'unidecode', 'bcrypt',
                      'pysqlite', 'babel'],
    cmdclass={'build': X_build,
              'install_data': X_install_data}
)
