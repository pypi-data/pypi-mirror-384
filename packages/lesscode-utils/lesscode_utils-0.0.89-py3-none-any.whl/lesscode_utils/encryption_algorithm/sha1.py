class SHA1:
    @staticmethod
    def encrypt(string: str):
        """
        :param string: 待加密字符串
        :return:
        """
        import hashlib
        sha = hashlib.sha1(string.encode('utf-8'))
        encrypt_string = sha.hexdigest()
        return encrypt_string
