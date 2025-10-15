# sdk-python

安装

`pip install requests` 

`pip install rsa`

> Crypto安装
> 
> 1.`pip install pycryptodome`
> 
> 2.python安装路径下找到文件夹\Lib\site-packages\crypto, 将crypto重命名为Crypto

## biz_model和params_model使用场景：
GET请求   使用biz_model             如：rpa_tasks_results_get.py
POST、 PUT、DELETE请求：
    Body参数  使用biz_model         如：rpa_plans_post.py
    Query参数 使用params_model      如：rpa_plans_drivers_post.py, rpa_plans_drivers_delete.py

### 2023.5.16
更新OpenClient.py、RequestTypes.py、BaseRequest.py。
支持流式接口调用

### 2022.5.26
更新OpenClient.py、RequestTypes.py、BaseRequest.py。
通过参数params_model = {}设置url携带参数(GET请求以外有效)


## 接口封装步骤

比如查询计划详情接口

- 接口名：/rpa/plans
- 参数：planId 要查询的计划Id
- 返回信息
```
{
        "msg": "SUCCESS",
        "code": "0",
        "data": {
            "name": "任务名称repeat",
            "platformId": "0",
            "actionType": "REPEAT_BY_WEEK"
        },
        "requestId": "765656",
}
```

针对这个接口，封装步骤如下：

1.在`model`包下新建一个类，定义业务参数

```python
class RpaPlansGetModel:
    """查询计划详情"""

    # 要查询的计划Id
    planId = None
```

2.在`request`包下新建一个请求类，继承`BaseRequest`

重写`get_method()`方法，填接口名。

重写`get_request_type()`方法，填接口请求方式。

```python
class RpaPlansGetRequest(BaseRequest):
    """查询计划详情"""

    def __init__(self):
        BaseRequest.__init__(self)

    def get_method(self):
        return '/rpa/plans'

    def get_request_type(self):
        return RequestTypes.GET
```

3.调用方式

```python
    
# 自用API-查询计划详情
def rpa_plans_get():
    # 创建请求客户端
    client = OpenClient(Config.app_id, Config.private_key, Config.url)

    # 创建请求
    request = RpaPlansGetRequest()
    # 请求参数，方式一
    model = RpaPlansGetModel()
    model.planId = 5070
    request.biz_model = JsonUtil.to_json_string(model)
    # 请求参数，方式二
    # request.biz_model = {
    #     'planId': 5070
    # }

    # 调用请求
    response = client.execute(request, user_token='填写user_token')

    if response.is_success():
        print('response: ', response)
        print('data: ', response.data)
    else:
        print("response: ", response)
        print('请求失败,request_id:%s, code:%s, msg:%s, sub_code:%s, sub_msg:%s' % \
              (response.request_id, response.code, response.msg, response.sub_code, response.sub_msg))

```

## 流式接口调用方式

```python
        # 调用请求，设置stream=True
        response = client.execute(request, app_token='填写app_token', stream=True)
        # 迭代获取流结果
        for item in response.iter_content():
            if item.is_success():
                print(item.get_content())
                print(item.data)
            else:
                print('请求失败,request_id:%s, code:%s, msg:%s, sub_code:%s, sub_msg:%s' %
                      (item.request_id, item.code, item.msg, item.sub_code, item.sub_msg))
```