FROM node:20-alpine

# Install Firebase CLI
RUN npm install -g firebase-tools

# Set working directory
WORKDIR /workspace

ENTRYPOINT ["firebase"]
