# Stage 1: Build the React app
FROM node:16-alpine as build
WORKDIR /app

# 从构建上下文的 tata-frontend/ 子目录中复制 package 文件
COPY tata-frontend/package*.json ./

# 安装依赖
RUN npm ci

# 从构建上下文的 tata-frontend/ 子目录中复制所有源代码
COPY tata-frontend/. .

# 构建应用
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# 从构建阶段复制编译好的前端文件
COPY --from=build /app/build /usr/share/nginx/html

# 从构建上下文的项目根目录复制自动修复脚本
COPY ./40-fix-api.sh /docker-entrypoint.d/40-fix-api.sh

# 赋予脚本执行权限
RUN chmod +x /docker-entrypoint.d/40-fix-api.sh

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]