FROM python:3.10-alpine

RUN addgroup -S mercari && adduser -S trainee -G mercari
# RUN chown -R trainee:mercari /path/to/db
RUN mkdir -p /db && chown -R trainee:mercari /db
ENV PATH="/usr/local/bin:$PATH"
USER trainee

CMD ["python", "-V"]
