#3.6
docker build . --force-rm=true -f ./docker/Dockerfile.alpine.3.6 -t server.aiknown.cn:31003/z_ai_frame/alpine-python3:3.6 && docker push server.aiknown.cn:31003/z_ai_frame/alpine-python3:3.6

#3.7
docker build . --force-rm=true -f ./docker/Dockerfile.alpine -t server.aiknown.cn:31003/z_ai_frame/alpine-python3 && docker push server.aiknown.cn:31003/z_ai_frame/alpine-python3:latest

#tensorflow
docker build . --force-rm=true -f ./docker/Dockerfile.alpine.tensorflow -t server.aiknown.cn:31003/z_ai_frame/alpine-python3:tensorflow && docker push server.aiknown.cn:31003/z_ai_frame/alpine-python3:tensorflow

# tensorflow opencv
docker build . --force-rm=true -f ./docker/Dockerfile.tensorflow_opencv -t server.aiknown.cn:31003/z_ai_frame/python3:tensorflow_opencv && docker push server.aiknown.cn:31003/z_ai_frame/python3:tensorflow_opencv
