from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(username,seconds):
    s=Serializer('27@Messanger',seconds)
    return s.dumps({'id':username}).decode('utf-8')
