FROM redis:7.4.2

# 复制自定义配置文件到容器内
COPY redis.conf /usr/local/etc/redis/redis.conf

# 声明数据存储目录（仅为文档说明，实际路径在运行时挂载）
VOLUME /data

# 使用自定义配置启动 Redis
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]