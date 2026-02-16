# Use Node.js LTS version
FROM node:20-alpine

# Install git
RUN apk add --no-cache git

# Set working directory
WORKDIR /app

# Create a fresh Vite React project
RUN npm create vite@latest . -- --template react

# Install dependencies
RUN npm install

# Install additional packages
RUN npm install lucide-react

# Install Tailwind and PostCSS
RUN npm install -D tailwindcss@3.4.1 postcss@8.4.35 autoprefixer@10.4.17

# Copy configuration files (we'll create these next)
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Expose Vite dev server port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]