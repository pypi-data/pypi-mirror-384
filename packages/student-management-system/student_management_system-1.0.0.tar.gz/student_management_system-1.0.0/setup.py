from setuptools import setup, find_packages

setup(
    name='student_management_system',
    version='1.0.0',
    author='Your Name',
    author_email='your_email@example.com',
    description='A simple student management system',
    packages=find_packages(),
    install_requires=[
        # list your dependencies here
        # example: 'requests', 'flask', etc.
    ],
    entry_points={
        'console_scripts': [
            'student-management=student_management.main:main'
        ],
    },
    python_requires='>=3.7',
)
