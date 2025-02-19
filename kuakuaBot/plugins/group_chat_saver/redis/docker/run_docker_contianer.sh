# 按需替换 /Volumes/external_disk/redis_data
docker run -d \
  --name kuakuabot-redis \
  -v /Volumes/Samsung_T5/workspace/redis/working_directory:/data \
  -p 6379:6379 \
  group-chat-saves  