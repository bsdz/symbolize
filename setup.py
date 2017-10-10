from distutils.core import setup
import versioneer

setup(name='symbolize',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Mathematical Symbol Engine',
    author='Blair Azzopardi',
    author_email='blairuk@gmail.com',
    url='https://github.com/bsdz/symbolize',
)