FROM alpine:latest

RUN apk add npm

COPY package.json /peerstash-web/package.json
COPY ./backend/ /peerstash-web/backend/
COPY ./frontend/ /peerstash-web/frontend/

EXPOSE 3000
EXPOSE 3001

WORKDIR /peerstash-web
RUN npm install
CMD ["npm", "start"]
