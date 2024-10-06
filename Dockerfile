# Use an official Python runtime as a parent image
FROM python:3.10.14-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    imagemagick \
    ffmpeg \
    build-essential \
    python3-dev \
    libsndfile1-dev \
    espeak \
    libespeak-dev \
    iputils-ping \
    curl \
    libpng-dev && \
    apt-get clean && \
    apt-get autoremove

# Install ImageMagick
RUN wget https://github.com/ImageMagick/ImageMagick/archive/refs/tags/7.1.0-31.tar.gz && \
    tar xzf 7.1.0-31.tar.gz && \
    cd ImageMagick-7.1.0-31 && \
    ./configure --prefix=/usr/local --with-bzlib=yes --with-fontconfig=yes --with-freetype=yes --with-gslib=yes --with-gvc=yes --with-jpeg=yes --with-jp2=yes --with-png=yes --with-tiff=yes --with-xml=yes --with-gs-font-dir=yes && \
    make -j && \
    make install && \
    ldconfig /usr/local/lib/ && \
    cd .. && rm -rf ImageMagick-7.1.0-31

# Install Aeneas
RUN git clone https://github.com/readbeyond/aeneas.git && \
    cd aeneas && \
    python -m pip install -r requirements.txt && \
    python setup.py install && \
    cd .. && rm -rf aeneas

# Copy application code to the container
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV IMAGEMAGICK_BINARY=/usr/local/bin/magick

# Start the Django development server on port 11001
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]