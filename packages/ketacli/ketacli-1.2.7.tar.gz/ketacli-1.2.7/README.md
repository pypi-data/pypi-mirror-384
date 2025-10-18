# ketadb 工具

## 示例

```shell
ketacli login --name <username> --endpoint http://localhost:9000 --token <yourtoken>

ketacli logout

# 枚举所有仪表盘
ketacli list dashboard --fields id,app,updateTime --sort updateTime --order asc --prefix test 

# 描述资源的字段
ketacli describe dashboard 

# 插入一条数据

ketacli insert --repo test01 '[{"a":1}]'

# 查询一条数据

ketacli search 'repo=test01 | limit 10' 

# 指定返回格式，支持json、csv、html、latex等

ketacli search 'repo=test01 | limit 10' --format json

#  创建一个资源

ketacli create repos test_repo --file file.json

# 删除一个资源
ketacli delete repos -n test_repo

# 查看可操作的资源列表
ketacli rs

# 查看具体资源操作方法
ketacli rs --type repos

# watch 资源变化
ketacli list repo --watch

ketacli search '''search2 repo="*"|stats count() as cnt by repo,sourcetype |sort by cnt |limit 10''' -w --interval 1

# 下载资源
ketacli download <assetType> [-e ectra] [--base_path path]

# 示例：下载 App
ketacli download apps --base_path apps -e app_name=keta_docs

# 下载任意资源（普通 json 接口将会保存 json 文件）
ketacli download repo -e name=_internal

# 安装 app
ketacli update apps -o install -e name=aws,version=1.0.1

# 卸载 app
ketacli update apps -o uninstall -e name=aws

# 重装/升级 app
ketacli update apps -o upgrade -e name=aws,version=1.0.1

# 终端画图
ketacli plot 'search2 start="-60m" repo="*" | timechart span="1m" count() as cnt by repo ' --y_field cnt --x_field _time --group_field repo --type line

# 内置仪表盘
ketacli dashboard -c infra-host  # 目前内置了infra-host audit k8s-monitor monitor四个仪表盘


```

# 自定义仪表盘
可参考示例仪表盘的 yaml 文件配置进行配置: [charts](ketacli/charts/)


## 自动补全

在你的 .bashrc / .zshrc 中加入以下语句

```shell
#zshrc 中不存在的话也需要添加
autoload -U +X bashcompinit && bashcompinit

eval "$(register-python-argcomplete ketacli)"
```