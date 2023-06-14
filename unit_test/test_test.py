def setup_module():
    print('\n *** 初始化-模块 ***')


def teardown_module():
    print('\n ***   清除-模块 ***')


class Test_1:
    def test_code(self):
        query_params = {
            "username": "asdasd",
            "password": "asdasd",
            "code": "abcd"
}
