## 使用
建议使用flask_rest_frame 被作为子模块引入到当前项目的 frame 文件夹下
下方的说明都是以frame文件夹的基础

## 编译
普通编译
```bash
docker build -f ./frame/docker/Dockerfile.source  .
```

加密编译
```bash
docker build -f ./frame/docker/Dockerfile.encrypt  .
```

基础镜像
```bash
#3.6
docker build . --force-rm=true -f ./docker/Dockerfile.alpine.3.6 -t server.aiknown.cn:31003/z_ai_frame/alpine-python3:3.6 && docker push server.aiknown.cn:31003/z_ai_frame/alpine-python3:3.6

#3.7
nohup docker build . --force-rm=true -f ./docker/Dockerfile.alpine -t server.aiknown.cn:31003/z_ai_frame/alpine-python3 && docker push server.aiknown.cn:31003/z_ai_frame/alpine-python3:latest &
```

## 文件夹文件
http: 网络请求相关文件
requirements.txt 框架依赖的库
requirements_all.txt 规定使用项目用到的所有库和版本，作为基础镜像打包


## 配置信息
| 分组 | 配置项 | 说明 |
| --- | --- | --- |
| 数据库 | SQLALCHEMY_DATABASE_URI | 数据库链接地址 |
| 数据库 | DB_SCHEMA | 对接的数据库 schema |
| 数据库 | AUTO_UPDATE | 是否自动更新数据库(DB_INIT_FILE,DB_VERSION_FILE,DB_UPDATE_FILE) |
| 数据库 | DB_INIT_FILE | 数据库初始化脚本 |
| 数据库 | DB_VERSION_FILE | 数据库迭代脚本（根据版本更新） |
| 数据库 | DB_UPDATE_FILE | 数据库开发脚本（本次启动运行） |
| 权限 | FETCH_USER | 是否获取用户 |
| 权限 | CHECK_API | API接口检查 |

## 权限初始化
生成初始化项目信息
invoke api-init

给admin做所有功能的授权
