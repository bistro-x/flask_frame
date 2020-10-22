# flask_rest_frame flask 的 rest 快速开发框架

## 环境变量
- CHECK_API 检测API的权限 默认 True
- LICENSE_CHECK 检测证书是否过期 默认 True
- FETCH_USER 获取当前用户到会话中 默认 True

#### 编译 docker 镜像

假设 flask_rest_frame 被作为子模块引入到当前项目的 frame 文件夹下

```docker
docker build -f ./frame/docker/Dockerfile.source  .
```

编译基本容器

```shell
#3.6
docker build . --force-rm=true -f ./docker/Dockerfile.alpine.3.6 -t server.aiknown.cn:31003/z_ai_frame/alpine-python3:3.6 && docker push server.aiknown.cn:31003/z_ai_frame/alpine-python3:3.6

#3.7
docker build . --force-rm=true -f ./docker/Dockerfile.alpine -t server.aiknown.cn:31003/z_ai_frame/alpine-python3 && docker push server.aiknown.cn:31003/z_ai_frame/alpine-python3:latest

#tensorflow
docker build . --force-rm=true -f ./docker/Dockerfile.alpine.tensorflow -t server.aiknown.cn:31003/z_ai_frame/alpine-python3:tensorflow && docker push server.aiknown.cn:31003/z_ai_frame/alpine-python3:tensorflow

# tensorflow opencv
docker build . --force-rm=true -f ./docker/Dockerfile.tensorflow_opencv -t server.aiknown.cn:31003/z_ai_frame/python3:tensorflow_opencv && docker push server.aiknown.cn:31003/z_ai_frame/python3:tensorflow_opencv

```

加密版本使用 Dockerfile.encrypt

## 文件夹文件

- http: 网络请求相关文件
