from setuptools import setup, find_namespace_packages

setup(
    name='brynq_sdk_profit',
    version='5.1.8-dev',
    description='Profit wrapper from BrynQ',
    long_description='Profit wrapper from BrynQ',
    author='BrynQ',
    author_email='support@brynq.com',
    packages=find_namespace_packages(include=['brynq_sdk*']),
    include_package_data=True,
    license='BrynQ License',
    install_requires=[
        'brynq-sdk-brynq>=4,<5',
        'brynq-sdk-functions>=2',
        'aiohttp>=3,<=4',
        'pandas>=1,<3',
        'requests>=2,<=3',
        'tenacity>=8,<9',
        'pydantic>=2,<3',
        'faker>=37.8.0',
        'polyfactory>=2.22.2',
        'bsn>=0.0.2'
    ],
    zip_safe=False,
)
