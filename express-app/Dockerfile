FROM node:20-alpine

WORKDIR /usr/src/app

COPY package.json ./
RUN npm ci --only=production

# Copy app source
COPY . .

EXPOSE 4567

CMD ["node", "server.js"]