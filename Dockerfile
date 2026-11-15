# Water Check in a container: the same commands as on a laptop or in GitHub Actions.
#   docker build -t water-check .
#   docker run --rm -v "$PWD:/work" -e WATERCHECK_ROOT=/work water-check run
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY watercheck ./watercheck
COPY docs/evidence/W1_protokol_powierzchnia_poziom.md ./docs/evidence/W1_protokol_powierzchnia_poziom.md
RUN pip install --no-cache-dir .
ENTRYPOINT ["python", "-m", "watercheck"]
CMD ["selftest"]
