FROM node:20-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY express.js .

EXPOSE 4567

CMD ["node", "express.js"]
