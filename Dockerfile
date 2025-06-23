# Use the official manylinux2014 image from the Python Packaging Authority (PyPA)
# It's based on CentOS 7, which has glibc 2.17 - extremely compatible.
FROM quay.io/pypa/manylinux2014_x86_64

# Use yum (the CentOS package manager) to install Kivy's system dependencies
RUN yum install -y mesa-libGL-devel SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel pkgconfig

# Define the path to the specific Python version we want to use inside the image
# This image provides many Python versions in /opt/python/
ENV PYTHON_VERSION=cp310-cp310
ENV PYTHON_PATH=/opt/python/${PYTHON_VERSION}/bin

# Install our required Python packages using the specific pip from that version
RUN ${PYTHON_PATH}/pip install --no-cache-dir kivy pillow pyinstaller

# Set the working directory for the build
WORKDIR /src

# Define the entrypoint for the container. This is the command that will run
# when we start the container. It uses the specific Python interpreter.
ENTRYPOINT ["/opt/python/cp310-cp310/bin/pyinstaller"]
