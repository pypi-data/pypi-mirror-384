"""
指标相关命令模块
"""
import json
import copy
from mando import command, arg
from rich.console import Console
from rich.progress import Progress
from ketacli.sdk.ai.client import AIClient
from ketacli.sdk.request.list import list_assets_request
from ketacli.sdk.request.get import get_asset_by_id_request
from ketacli.sdk.request.update import update_asset_request
from ketacli.sdk.base.client import request_get, request
from ketacli.sdk.util import parse_url_params
console = Console()


@command
@arg('operator', type=str, completer=lambda prefix, **kwd: [x for x in ['governance'] if x.startswith(prefix)])
def metric(operator, name=None, id=None, extra=None, page_size=10, page_num=1):
    """
    指标操作

    :param operator: 操作类型，如 governance
    :param -e,--extra: 额外参数，格式为 key=value,key2=value2
    :param -n,--name: 指标名称
    :param -i,--id: 指标 ID
    """
    if operator not in ['governance']:
        console.print(f"[red]不支持的操作类型: {operator}, 当前支持的操作类型为: governance[/red]")
        return
    try:
        assets = []
        extra_dict = {}
        if extra is not None:
            # 解析 url 参数为 dict
            extra_dict = parse_url_params(extra)
        if name:
            req = list_assets_request("metrics", prefix=name, pageSize=page_size, pageNo=page_num)
            resp = request_get(req["path"], req["query_params"], req["custom_headers"]).json()
        elif id:
            metric_info = get_asset_by_id_request(asset_type="metrics", asset_id=id)
            resp = request_get(metric_info["path"], metric_info["query_params"], metric_info["custom_headers"]).json()
        elif extra_dict:
            req = list_assets_request("metrics", pageSize=page_size, pageNo=page_num, **extra_dict)
            resp = request_get(req["path"], req["query_params"], req["custom_headers"]).json()
        else:
            req = list_assets_request("metrics", pageSize=page_size, pageNo=page_num)
            resp = request_get(req["path"], req["query_params"], req["custom_headers"]).json()
        if resp:
            if "items" in resp:
                assets += resp["items"]
            else:
                assets.append(resp)
        
        if not assets:
            console.print("未找到任何指标数据", style="red")
            return

        if operator == "governance":
            _metricsGov(assets)

    except KeyboardInterrupt:
        console.print("\n[yellow]操作已被用户中断[/yellow]")
        console.print("[dim]提示：您可以随时按 Ctrl+C 来中断正在进行的操作[/dim]")
    except Exception as e:
        console.print(f"[red]执行过程中发生错误: {str(e)}[/red]")


def _metricsGov(assets):
    """
    指标治理
    """
    prompt = """
你是一个指标治理专家，负责将未治理的指标进行治理，包括对指标名称进行汉化、添加指标描述、优化指标单位、分类、分组等
你要接受用户传来的指标信息，修改用户要修修改的字段后返回结果，保持数据结构一致性和完整性。接下来用户会传递json类型的数据，你要处理根据如下要求进行处理。返回数据时保持数据结构与传递时一致。不要包含任何其它非json字符。
  - 要求：
    1. 将指标名称(name)翻译为中文
    2. 添加指标描述(description)信息(描述信息要能够反映该指标的含义、以及指标能够反映出哪些信息等)
    3. 指标单位(unit)按照附表中《指标单位清单》进行填写
    4. 指标度量(measureType)按照指标意义选择，可选范围为[COUNTER,GAUGE,HISTOGRAM,SUMMARY]
    5. 指标类别(category)固定为"None",
    6. 指标性质(nature)可选：[Normal,Traffic,Error,Performance,Resource]
    7. 在标签映射(labelList)中，将name字段翻译为中文
    8. 所有者(owner)固定为空字符串，其它字段不做修改
  - 指标单位清单：none,short,percent,percentunit,humidity,dB,hex0x,hex,sci,locale,thousand,time,hertz,ns,µs,ms,s,m,h,d,dtdurationms,dtdurations,dthms,timeZh,hertzZh,nsZh,µsZh,msZh,sZh,mZh,hZh,dZh,dtdurationmsZh,dtdurationsZh,dthmsZh,data
    (IEC),bits,bytes,kbytes,mbytes,gbytes,data rate,pps,bps,Bps,Kbits,KBs,Mbits,MBs,Gbits,GBs,throughput,ops,reqps,rps,wps,iops,opm,rpm,wpm,length,lengthmm,lengthm,lengthft,lengthkm,lengthmi,area,areaM2,areaF2,areaMI2,mass,massmg,massg,masskg,masst,velocity,velocityms,velocitykmh,velocitymph,velocityknot,volume,mlitre,litre,m3,Nm3,dm3,gallons,energy,watt,kwatt,mwatt,Wm2,voltamp,kvoltamp,voltampreact,kvoltampreact,watth,kwatth,kwattm,joule,ev,amp,kamp,mamp,volt,kvolt,mvolt,dBm,ohm,lumens,temperature,celsius,farenheit,kelvin,pressure,pressurembar,pressurebar,pressurekbar,pressurehpa,pressurekpa,pressurehg,pressurepsi,force,forceNm,forcekNm,forceN,forcekN,flow,flowgpm,flowcms,flowcfs,flowcfm,litreh,flowlpm,flowmlpm,angle,degree,radian,grad,acceleration,accMS2,accFS2,accG,radiation,radbq,radci,radgy,radrad,radsv,radrem,radexpckg,radr,radsvh,concentration,ppm,conppb,conngm3,conμgm3,conmgm3,congm3
    """
    client = AIClient(system_prompt=prompt)
    
    if not assets:
        console.print("未找到任何指标数据", style="red")
        return
    
    asset_names = [x.get('key', f'指标{i+1}') for i, x in enumerate(assets)]
    
    # 使用rich进度条显示处理进度
    try:
        with Progress() as progress:
            task = progress.add_task("[green]处理指标治理...", total=len(assets))
            
            for i, asset in enumerate(assets):
                # 更新进度条描述，显示当前处理的指标
                asset_name = asset.get('name', f'指标{i+1}')
                progress.update(task, description=f"[green]正在处理: {asset_name}（{i+1}/{len(assets)}）")
                
                # console.print(asset, overflow="fold")
                asset_id = asset.pop("id")
                description = asset.get("description", "")
                if description:
                    progress.advance(task)
                    continue

                # 处理标签
                _labels = asset.pop("labels", {})
                labels = [x['key'] for x in _labels]
                labelList = copy.deepcopy(_labels)

                # 处理分组
                groupIds = [x.get('id') for x in asset.pop('groups', []) if 'id' in x]
                asset.update({"labelList": labelList, "labels": labels, 'groupIds': groupIds})

                try:
                    resp = client.chat(json.dumps(asset, ensure_ascii=False))
                    try:
                        asset = json.loads(resp.content)
                    except json.JSONDecodeError:
                        console.print(f"[red]解析AI响应失败: {resp}[/red]")
                        progress.advance(task)
                        continue
                    
                    req_info = update_asset_request(asset_type="metrics", id=asset_id, data=asset)
                    resp = request(req_info["method"], req_info["path"], data=req_info['data']).json()
                except KeyboardInterrupt:
                    # 在循环中捕获用户中断，显示已处理的进度
                    console.print(f"\n[yellow]操作已被用户中断[/yellow]")
                    console.print(f"[dim]已处理 {i}/{len(assets)} 个指标[/dim]")
                    return
                except Exception as e:
                    console.print(f"[red]处理指标 {asset_name} 时发生错误: {str(e)}[/red]")
                
                # 推进进度条
                progress.advance(task)
                
        console.print(f"[green]指标治理完成！共处理 {len(assets)} 个指标:\n{asset_names}[/green]")
        
    except KeyboardInterrupt:
        console.print(f"\n[yellow]操作已被用户中断[/yellow]")
        console.print("[dim]提示：您可以随时按 Ctrl+C 来中断正在进行的操作[/dim]")
