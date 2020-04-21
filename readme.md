# flask_rest_frame flask 的 rest 快速开发框架

#### 编译 docker 镜像

假设 flask_rest_frame 被作为子模块引入到当前项目的 frame 文件夹下

```docker
docker build -f ./frame/docker/Dockerfile.source  .
```

编译基本容器
```shell
docker build . -f ./docker/Dockerfile.alpine -t server.aiknown.cn:31003/z_ai_frame/alpine-python3
```

加密版本使用 Dockerfile.encrypt
