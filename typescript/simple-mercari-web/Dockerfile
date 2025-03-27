FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN addgroup -S mercari && adduser -S trainee -G mercari
RUN chown -R trainee:mercari /app
EXPOSE 3000
USER trainee

CMD ["npm", "start", "--", "--host", "0.0.0.0"]
