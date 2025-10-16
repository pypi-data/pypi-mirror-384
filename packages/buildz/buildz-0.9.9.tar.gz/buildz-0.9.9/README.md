# buildz
声明:
禁止将本项目代码用于ai训练
declaration:
Codes of this project are not allowed to be used for AI training or any other form of machine learning processes.

使用此代码库发现bug或者有需求需要开发都可联系(QQ或邮箱联系，QQ就是邮箱号)

邮箱1:1174534295@qq.com

邮箱2:1309458652@qq.com

```
1，在json格式基础上加了点东西，让配置文件写起来更简单，模块在buildz.xf下
2，基于xf格式写了个ioc控制反转配置文件读取的程序，模块在buildz.ioc下
3，其他工具模块：
    buildz.fz: 文件夹查找
    buildz.pyz: 简化python __import__调用
    buildz.argx: 按格式读命令行参数
    buildz.tz: 加些工具，目前只有myerse diff字符串比较算法
    buildz.demo: 使用参考，运行"python -m buildz"会用这个模块
    buildz.db: sql集成工具，自用，里面import了其他sql库，使用运行"python -m buildz.db 配置文件路径"
    buildz.base: 封装了一个基础类，继承它可以少写一些代码
    buildz.html: xml（html）内容读取和解析
    buildz.auto: 自动化操作（主要是做自动化测试方便些，如果不怕写一堆配置文件的话）
代码关系:
    buildz.xf, buildz.pyz, buildz.argx, buildz.fz, buildz.tz都是独立的模块
    buildz.ioc需要buildz.xf和buildz.pyz
    buildz.db需要buildz.xf
    buildz.demo需要其他全部模块

运行python -m buildz查看帮助


PS: 对比了下json.loads（修改了下json的scanner.py，让它在纯python下运行，不然json.loads会更快）和目前的xf.loads(buildz.xf.readz.loads)的速度，xf.loads比json.loads慢7倍，可能是读字符串更频繁，方法调用更多（为了代码更结构化和容易修改），其实有一版更慢(buildz.xf.read.loads，废弃代码，后面看情况删掉)，慢100倍，因为只考虑结构化，没考虑列表增减开销（获得的经验教训是别直接用python的列表list当堆栈做append和pop，特别慢！）

1, a profile file format base on json, make it easy to write profile file, module is in buildz.xf
2, a ioc profile file read function base on xf format, module is in buildz.ioc
3, other tools module:
    buildz.fz: file search
    buildz.pyz: make it easier to use python's __import__ function
    buildz.argx: read command argument in special format
    buildz.demo: example codes to use buildz, run "python -m buildz" will use this module
code relationship:
    buildz.xf, buildz.pyz, buildz.argx, buildz.fz, buildz.tz is independent
    buildz.ioc use buildz.xf and buildz.pyz
    buildz.tz: some tools, only contains "myerse diff algorithm" now
    buildz.demo use all other modules

run python -m buildz to see help

continue updating...

PS: testing speed on json.loads(has modified scanner.py in json module to make it purely run on Python, which make it run slower) and xf.loads(real func is buildz.xf.readz.loads), xf.loads takes 7 times longer than json.loads, it may cost by more func calls and more string cutting and reading(to make codes more structuring and easier to update)
```
