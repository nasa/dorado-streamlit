#
# Copyright © 2021 United States Government as represented by the Administrator
# of the National Aeronautics and Space Administration. No copyright is claimed
# in the United States under Title 17, U.S. Code. All Other Rights Reserved.
#
# SPDX-License-Identifier: NASA-1.3
#

FROM python:slim AS deps
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes -o requirements.txt

FROM python
COPY --from=deps requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

RUN mkdir /app
WORKDIR /app
COPY sensitivity.py .

RUN useradd -r -s /usr/sbin/nologin -d /app app && chown app:app /app
EXPOSE 8501:8501/tcp
USER app:app
ENTRYPOINT [ \
    "streamlit", "run", \
    "--global.metrics=false", \
    "--client.showErrorDetails=false", \
    "--browser.gatherUsageStats=false"]
CMD ["sensitivity.py"]
