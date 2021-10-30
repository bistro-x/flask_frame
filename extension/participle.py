import requests


participle_app = None
participle_service_url = None


def init_app(app):
    global participle_app, participle_service_url

    participle_app = app
    participle_service_url = app.config.get('PARTICIPLE_SERVICE_URL', None)


def participle_sentence(sentence):
    """
    获取句字符串分词结果
    :param sentence: 句字符串
    :return : List
    """
    global participle_app, participle_service_url

    if not participle_app or not participle_service_url:
        return []

    try:
        response = requests.post(
            url=participle_service_url + '/participle',
            headers={'Content-Type': 'application/json'},
            json={"sentence": sentence}
        )
        words = response.json()['result']
    except Exception as e:
        if hasattr(participle_app, 'logger'):
            participle_app.logger.error(f'{sentence} participle except {str(e)}')
        return []
    else:
        return words